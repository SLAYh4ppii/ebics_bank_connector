# Copyright (c) 2026, EBICS Bank Connector
"""Public API endpoints.

    POST /api/method/ebics_bank_connector.sync_now        -> trigger a sync
    GET  /api/method/ebics_bank_connector.status          -> dashboard status
    POST /api/method/ebics_bank_connector.test_connection -> test a connection
    POST /api/method/ebics_bank_connector.initialize_keys  -> INI/HIA/HPB
    GET  /api/method/ebics_bank_connector.list_accounts    -> discover accounts
"""
from __future__ import annotations

import frappe

from ebics_bank_connector.utils import require_role


@frappe.whitelist()
def sync_now(settings: str | None = None):
    """Trigger a manual sync for a connection (or all active ones)."""
    require_role("Bank Administrator", "Bank Buchhalter")
    from ebics_bank_connector.sync import sync_connection

    if settings:
        return sync_connection(settings)
    results = []
    for name in frappe.get_all(
        "EBICS Settings", filters={"sync_enabled": 1, "status": "Verbunden"}, pluck="name"
    ):
        results.append({"settings": name, **sync_connection(name)})
    return results


@frappe.whitelist()
def status():
    """Return the dashboard status snapshot."""
    require_role("Bank Administrator", "Bank Buchhalter", "Bank Mitarbeiter")
    from frappe.utils import now

    connections = frappe.get_all(
        "EBICS Settings",
        fields=["name", "connection_name", "status", "last_sync", "sync_enabled"],
    )
    last_log = frappe.get_all(
        "EBICS Sync Log",
        fields=["name", "status", "started_on", "transactions_imported", "error_message"],
        order_by="started_on desc",
        limit=5,
    )
    return {
        "timestamp": now(),
        "connections": connections,
        "recent_logs": last_log,
        "open_matching_tasks": frappe.db.count("Payment Matching Task", {"status": "Offen"}),
        "errors_today": frappe.db.count(
            "EBICS Sync Log", {"status": "Fehler", "started_on": [">=", frappe.utils.today()]}
        ),
    }


@frappe.whitelist()
def test_connection(settings: str):
    require_role("Bank Administrator")
    doc = frappe.get_doc("EBICS Settings", settings)
    return doc.test_connection()


@frappe.whitelist()
def initialize_keys(settings: str):
    require_role("Bank Administrator")
    doc = frappe.get_doc("EBICS Settings", settings)
    return doc.initialize_keys()


@frappe.whitelist()
def list_accounts(settings: str):
    """Discover available bank accounts via HTD/HPD."""
    require_role("Bank Administrator")
    from ebics_bank_connector.ebics.connection import get_connection

    doc = frappe.get_doc("EBICS Settings", settings)
    client = get_connection(doc)
    return client.list_accounts()
