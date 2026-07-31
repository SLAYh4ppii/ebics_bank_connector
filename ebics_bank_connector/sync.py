# Copyright (c) 2026, EBICS Bank Connector
"""Bank synchronisation engine.

Orchestrates a single sync run for one EBICS connection:

    1. connect (EBICS)
    2. download CAMT.053 (and optionally CAMT.054)
    3. parse transactions
    4. deduplicate against existing Bank Transactions
    5. create ERPNext Bank Transactions
    6. run the matching engine
    7. write an EBICS Sync Log + update cursor

Exposed via the scheduler (``run_hourly_sync``) and the API
(``ebics_bank_connector.sync_now``).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import frappe
from frappe.utils import add_to_date, get_datetime, getdate, now

from ebics_bank_connector.ebics.connection import get_connection
from ebics_bank_connector.ebics.camt_parser import parse_camt
from ebics_bank_connector.erpnext_integration import create_bank_transaction

log = logging.getLogger(__name__)


def run_hourly_sync():
    """Scheduler entry point (runs every 5 min via 'all')."""
    for settings_name in _due_connections("St\u00fcndlich", hours=1):
        try:
            sync_connection(settings_name)
        except Exception:  # noqa: BLE001
            log.exception("EBICS sync failed for %s", settings_name)


def run_daily_sync():
    for settings_name in _due_connections("T\u00e4glich", days=1):
        try:
            sync_connection(settings_name)
        except Exception:  # noqa: BLE001
            log.exception("EBICS daily sync failed for %s", settings_name)


def _due_connections(frequency: str, **delta) -> list:
    """Return connection names whose last_sync is older than the delta window.

    Uses a proper datetime comparison (not getdate) so that hourly connections
    are not re-synced on every scheduler tick.
    """
    threshold = now() if not delta else add_to_date(now(), **{k: -v for k, v in delta.items()})
    rows = frappe.get_all(
        "EBICS Settings",
        filters={"sync_enabled": 1, "status": "Verbunden", "sync_frequency": frequency},
        pluck="name",
    )
    due = []
    for name in rows:
        last = frappe.db.get_value("EBICS Settings", name, "last_sync")
        if not last or get_datetime(last) <= get_datetime(threshold):
            due.append(name)
    return due


def sync_connection(settings_name: str, account_name: str | None = None) -> dict:
    """Run one full sync for a connection. Returns a summary dict.

    Uses a cache-based lock so that overlapping scheduler + manual syncs do not
    run in parallel for the same connection (would cause duplicate work and
    race conditions on the cursor).
    """
    lock_key = f"ebics_sync_lock:{settings_name}"
    if frappe.cache().get(lock_key):
        log.info("Sync already running for %s, skipping", settings_name)
        return {"ok": False, "message": frappe._("Synchronisation l\u00e4uft bereits.")}

    frappe.cache().set(lock_key, True)
    try:
        settings = frappe.get_doc("EBICS Settings", settings_name)
        if not settings.is_active:
            return {"ok": False, "message": frappe._("Verbindung ist nicht aktiv.")}

        accounts = _resolve_accounts(settings, account_name)
        summary = {"ok": True, "imported": 0, "duplicate": 0, "matched": 0, "unmatched": 0, "errors": []}

        for ebics_account in accounts:
            try:
                res = _sync_account(settings, ebics_account)
                summary["imported"] += res["imported"]
                summary["duplicate"] += res["duplicate"]
                summary["matched"] += res["matched"]
                summary["unmatched"] += res["unmatched"]
            except Exception as exc:  # noqa: BLE001
                log.exception("Sync failed for account %s", ebics_account.name)
                summary["errors"].append(str(exc))
                summary["ok"] = False
                settings.mark_error(str(exc))

        settings.mark_synced()
        return summary
    finally:
        frappe.cache().delete(lock_key)


def _resolve_accounts(settings, account_name):
    filters = {"ebics_settings": settings.name, "enabled": 1}
    if account_name:
        filters["name"] = account_name
    return frappe.get_all("EBICS Bank Account", filters=filters, pluck="name")


def _sync_account(settings, ebics_account_name: str) -> dict:
    ebics_account = frappe.get_doc("EBICS Bank Account", ebics_account_name)
    bank_account = ebics_account.bank_account or settings.default_bank_account
    if not bank_account:
        raise frappe.ValidationError(
            frappe._("Kein ERPNext Bank Account f\u00fcr EBICS Konto {0}.").format(ebics_account.iban)
        )

    start, end = _date_range(ebics_account)
    client = get_connection(settings)

    log_doc = frappe.get_doc(
        {
            "doctype": "EBICS Sync Log",
            "ebics_settings": settings.name,
            "ebics_bank_account": ebics_account.name,
            "started_on": now(),
            "order_type": "Z53",
            "from_date": start,
            "to_date": end,
        }
    )

    imported = duplicate = matched = unmatched = 0
    raw_xml = b""
    try:
        raw_xml = client.fetch_statements(start, end, account=ebics_account.iban)
        if settings.raw_xml_storage and raw_xml:
            log_doc.raw_xml_file = _store_xml(raw_xml, settings.name, ebics_account.iban)

        transactions = parse_camt(raw_xml)

        # optional CAMT.054
        if settings.import_camt054:
            try:
                camt054 = client.fetch_notifications(start, end, account=ebics_account.iban)
                transactions += parse_camt(camt054)
            except Exception:  # noqa: BLE001
                log.warning("CAMT.054 download failed, continuing with CAMT.053 only")

        last_tx_id = ebics_account.last_transaction_id
        for tx in transactions:
            # dedup by bank-side transaction id + bank account
            from ebics_bank_connector.erpnext_integration import bank_transaction_exists

            if bank_transaction_exists(tx.transaction_id, bank_account):
                duplicate += 1
                continue
            name = create_bank_transaction(tx, bank_account)
            if not name:
                duplicate += 1
                continue
            imported += 1
            if tx.transaction_id:
                last_tx_id = tx.transaction_id

            # matching
            if settings.auto_match:
                from ebics_bank_connector.matching import match_transaction

                result = match_transaction(name)
                if result.get("matched"):
                    matched += 1
                else:
                    unmatched += 1
                    _create_matching_task(tx, name)
            else:
                unmatched += 1

        # advance cursor
        frappe.db.set_value(
            "EBICS Bank Account",
            ebics_account.name,
            {"last_transaction_id": last_tx_id, "last_synced_at": now()},
            update_modified=False,
        )

        log_doc.ended_on = now()
        log_doc.status = "Erfolgreich" if not (log_doc.error_message) else "Teilweise"
        log_doc.transactions_imported = imported
        log_doc.transactions_duplicate = duplicate
        log_doc.transactions_matched = matched
        log_doc.transactions_unmatched = unmatched
        log_doc.insert(ignore_permissions=True)
    except Exception as exc:  # noqa: BLE001
        log.exception("Account sync error")
        log_doc.ended_on = now()
        log_doc.status = "Fehler"
        log_doc.error_message = str(exc)
        if settings.raw_xml_storage and raw_xml:
            log_doc.raw_xml_file = _store_xml(raw_xml, settings.name, ebics_account.iban)
        log_doc.insert(ignore_permissions=True)
        raise

    return {"imported": imported, "duplicate": duplicate, "matched": matched, "unmatched": unmatched}


def _date_range(ebics_account) -> tuple:
    """Return (start, end) for the next download window."""
    end = date.today()
    last = ebics_account.last_synced_at
    if last:
        start = getdate(last) - timedelta(days=2)  # overlap to catch late bookings
    else:
        start = end - timedelta(days=30)  # initial window
    return start, end


def _store_xml(raw_xml: bytes, settings_name: str, iban: str) -> str:
    import os
    import re

    from frappe.utils import now

    # sanitise inputs so they cannot break out of the filename or folder
    safe_settings = re.sub(r"[^A-Za-z0-9_-]", "_", settings_name or "conn")[:60]
    safe_iban = re.sub(r"[^A-Za-z0-9]", "", iban or "noid")[:34]
    stamp = now().replace(":", "").replace(" ", "_").replace(".", "")
    fname = f"ebics_{safe_settings}_{safe_iban}_{stamp}.xml"
    folder = frappe.get_site_path("private", "files", "ebics_xml")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fname)
    with open(path, "wb") as fh:
        fh.write(raw_xml)
    return f"/private/files/ebics_xml/{fname}"


def cleanup_old_xml():
    """Delete CAMT-XML files older than the configured retention period.

    Scheduled daily via hooks. Set ``xml_retention_days`` in Bank Automation
    Settings to 0 to disable cleanup (keep forever).
    """
    import os
    import time

    from frappe.utils import add_days, getdate, nowdate

    from ebics_bank_connector.ebics_bank_connector.doctype.bank_automation_settings.bank_automation_settings import (
        get_settings,
    )

    settings = get_settings()
    days = settings.get("xml_retention_days") or 0
    if not days or int(days) <= 0:
        return

    cutoff = add_days(nowdate(), -int(days))
    cutoff_ts = time.mktime(getdate(cutoff).timetuple())
    folder = frappe.get_site_path("private", "files", "ebics_xml")
    if not os.path.isdir(folder):
        return

    removed = 0
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        if os.path.getmtime(path) < cutoff_ts:
            try:
                os.remove(path)
                removed += 1
            except OSError:
                log.warning("Could not remove old CAMT-XML %s", path)
    if removed:
        log.info("Cleaned up %d CAMT-XML files older than %d days", removed, days)


def _create_matching_task(tx, bank_transaction_name: str):
    from ebics_bank_connector.matching import suggest_party

    suggestion = suggest_party(tx)
    frappe.get_doc(
        {
            "doctype": "Payment Matching Task",
            "subject": frappe._("Zahlung pr\u00fcfen: {0} ({1})").format(
                tx.counterparty_name or "Unbekannt", str(tx.amount)
            ),
            "status": "Offen",
            "priority": "Mittel",
            "bank_transaction": bank_transaction_name,
            "amount": abs(float(tx.amount)),
            "currency": tx.currency,
            "value_date": getdate(tx.value_date),
            "party_type": suggestion.get("party_type"),
            "party": suggestion.get("party"),
            "suggested_invoice": suggestion.get("invoice_type"),
            "suggested_invoice_name": suggestion.get("invoice_name"),
            "transaction_name": tx.counterparty_name,
            "transaction_description": tx.description,
            "reference": tx.reference,
        }
    ).insert(ignore_permissions=True)
