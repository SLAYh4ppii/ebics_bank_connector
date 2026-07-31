# Copyright (c) 2026, EBICS Bank Connector
"""Automatic payment matching engine.

Priority (configurable in Bank Automation Settings):

    1. Rechnungsnummer erkennen   (RE-2026-001, RE2026-001, ...)
    2. Kunden-ID
    3. Lieferanten-ID
    4. Verwendungszweck
    5. Betrag

On a hit, a Payment Entry is created and linked to the Bank Transaction
(via the Bank Transaction Payments child table) and the invoice is reconciled.
"""
from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Optional

import frappe
from frappe.utils import flt, getdate

from ebics_bank_connector.ebics.camt_parser import Transaction

log = logging.getLogger(__name__)

# invoice number patterns: RE-2026-001, RE2026001, R-2026-0001, PINV-..., etc.
INVOICE_PATTERNS = [
    re.compile(r"\b(RE|RECHNUNG|INV|INVOICE)\s*[-]?\s*(\d{4,6}[-]?\d{1,6})\b", re.IGNORECASE),
    re.compile(r"\bRE[-]?\s?(\d{4})[-]?(\d{1,6})\b", re.IGNORECASE),
    re.compile(r"\b(SI|PI|PINV|PURCH)\s*[-]?\s*(\d{4,6}[-]?\d{1,6})\b", re.IGNORECASE),
]


def match_transaction(bank_transaction_name: str) -> dict:
    """Try to match a Bank Transaction to an open invoice. Returns result dict."""
    bt = frappe.get_doc("Bank Transaction", bank_transaction_name)
    settings = _settings()

    text_blob = " ".join(
        [
            bt.get("description") or "",
            bt.get("reference_no") or "",
            bt.get("transaction_id") or "",
        ]
    ).upper()

    # 1. invoice number
    if settings.match_invoice_number:
        hit = _match_by_invoice(text_blob, bt)
        if hit:
            return _apply_match(bt, hit)

    # 2. customer id
    if settings.match_customer_id:
        hit = _match_by_party_id(text_blob, "Customer", "Sales Invoice")
        if hit:
            return _apply_match(bt, hit)

    # 3. supplier id
    if settings.match_supplier_id:
        hit = _match_by_party_id(text_blob, "Supplier", "Purchase Invoice")
        if hit:
            return _apply_match(bt, hit)

    # 4. purpose / 5. amount handled inside _match_by_invoice already
    return {"matched": False}


def _match_by_invoice(text_blob: str, bt) -> Optional[dict]:
    for pattern in INVOICE_PATTERNS:
        for m in pattern.finditer(text_blob):
            candidate = m.group(0).replace(" ", "").upper()
            # try Sales Invoice
            inv = _find_open_invoice("Sales Invoice", candidate, bt)
            if inv:
                return {"invoice_type": "Sales Invoice", "invoice_name": inv, "party_type": "Customer"}
            inv = _find_open_invoice("Purchase Invoice", candidate, bt)
            if inv:
                return {"invoice_type": "Purchase Invoice", "invoice_name": inv, "party_type": "Supplier"}
    return None


def _find_open_invoice(doctype: str, ref: str, bt, amount: Optional[float] = None) -> Optional[str]:
    if amount is None and bt is not None:
        amount = flt(bt.get("deposit") or 0) - flt(bt.get("withdrawal") or 0)
    # match by name containing the reference and still outstanding
    candidates = frappe.get_all(
        doctype,
        filters={"docstatus": 1, "status": ["in", ["Unpaid", "Partly Paid", "Overdue"]]},
        or_filters={"name": ["like", f"%{ref}%"], "po_no": ["like", f"%{ref}%"]},
        pluck="name",
        limit=50,
    )
    settings = _settings()
    for name in candidates:
        inv = frappe.get_cached_doc(doctype, name)
        outstanding = flt(inv.get("outstanding_amount") or 0)
        if outstanding <= 0:
            continue
        # skip amount check when no amount is available (suggestion mode)
        if amount is not None and settings.match_amount and not _amount_matches(abs(amount), outstanding, settings.amount_tolerance):
            continue
        return name
    return None


def _match_by_party_id(text_blob: str, party_doctype: str, invoice_doctype: str) -> Optional[dict]:
    """Match by customer/supplier name appearing in the transaction text.

    Instead of loading every party and doing a substring check (slow + false
    positives on short names), we query parties whose name is long enough to
    be distinctive and appears as a whole word in the text blob.
    """
    party_field = "customer" if party_doctype == "Customer" else "supplier"
    # only consider parties with a name of at least 4 characters to avoid
    # trivial false positives (e.g. "Me" matching "ME GmbH")
    parties = frappe.get_all(
        party_doctype,
        filters={"name": [">", ""]},
        fields=["name"],
    )
    for p in parties:
        name = (p["name"] or "").upper()
        if len(name) < 4:
            continue
        # require a word-boundary match, not a bare substring, so "Meier GmbH"
        # does not match a transaction that merely contains "MEIERSTRASSE"
        if not re.search(r"\b" + re.escape(name) + r"\b", text_blob):
            continue
        inv = frappe.get_all(
            invoice_doctype,
            filters={
                "docstatus": 1,
                "status": ["in", ["Unpaid", "Partly Paid", "Overdue"]],
                party_field: p["name"],
            },
            order_by="posting_date asc",
            pluck="name",
            limit=1,
        )
        if inv:
            return {
                "invoice_type": invoice_doctype,
                "invoice_name": inv[0],
                "party_type": party_doctype,
            }
    return None


def _amount_matches(imported: float, outstanding: float, tolerance_pct: float) -> bool:
    if tolerance_pct <= 0:
        return abs(imported - outstanding) < 0.01
    diff = abs(imported - outstanding)
    allowed = abs(outstanding) * (tolerance_pct / 100.0)
    return diff <= allowed


def _apply_match(bt, hit: dict) -> dict:
    """Create a Payment Entry and link it to the Bank Transaction."""
    settings = _settings()
    try:
        pe_name = _create_payment_entry(bt, hit)
        _link_to_bank_transaction(bt, pe_name)
        frappe.db.set_value("Bank Transaction", bt.name, "status", "Reconciled", update_modified=False)
        return {"matched": True, "payment_entry": pe_name, **hit}
    except Exception:  # noqa: BLE001
        log.exception("Failed to apply match for %s", bt.name)
        return {"matched": False, "error": "Anwendung fehlgeschlagen"}


def _create_payment_entry(bt, hit: dict) -> str:
    inv_doctype = hit["invoice_type"]
    inv_name = hit["invoice_name"]
    party_type = hit["party_type"]
    party = frappe.get_cached_value(inv_doctype, inv_name, party_type.lower())
    company = bt.get("company") or frappe.get_cached_value("Bank Account", bt.bank_account, "company")
    amount = flt(bt.get("deposit") or 0) - flt(bt.get("withdrawal") or 0)
    payment_type = "Receive" if amount > 0 else "Pay"

    pe = frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": payment_type,
            "company": company,
            "posting_date": getdate(bt.get("date")),
            "party_type": party_type,
            "party": party,
            "paid_amount": abs(amount),
            "received_amount": abs(amount),
            "paid_from": _party_account(party_type, party, company, payment_type),
            "paid_to": _bank_gl_account(bt.bank_account, company),
            "reference_no": bt.get("transaction_id") or bt.get("reference_no") or "",
            "reference_date": getdate(bt.get("reference_date") or bt.get("date")),
            "bank_account": bt.bank_account,
        }
    )
    pe.append(
        "references",
        {
            "reference_doctype": inv_doctype,
            "reference_name": inv_name,
            "allocated_amount": abs(amount),
        },
    )
    pe.insert(ignore_permissions=True)
    pe.submit()
    return pe.name


def _party_account(party_type, party, company, payment_type):
    if party_type == "Customer":
        return frappe.get_cached_value("Company", company, "default_receivable_account") or _default_account(company, "Receivable")
    return frappe.get_cached_value("Company", company, "default_payable_account") or _default_account(company, "Payable")


def _bank_gl_account(bank_account, company):
    return frappe.get_cached_value("Bank Account", bank_account, "account")


def _default_account(company, kind):
    acc_type = "Receivable" if kind == "Receivable" else "Payable"
    acc = frappe.get_all(
        "Account",
        filters={"company": company, "account_type": acc_type, "is_group": 0},
        pluck="name",
        limit=1,
    )
    return acc[0] if acc else None


def _link_to_bank_transaction(bt, payment_entry: str):
    """Add the payment entry to the Bank Transaction's payments child table."""
    bt = frappe.get_doc("Bank Transaction", bt.name)
    amount = flt(bt.get("deposit") or 0) - flt(bt.get("withdrawal") or 0)
    bt.append(
        "payment_entries",
        {
            "payment_entry": payment_entry,
            "allocated_amount": abs(amount),
        },
    )
    bt.save(ignore_permissions=True)


def suggest_party(tx: Transaction) -> dict:
    """Best-effort suggestion used when creating a Payment Matching Task."""
    text_blob = " ".join([tx.counterparty_name, tx.description, tx.reference]).upper()
    for pattern in INVOICE_PATTERNS:
        m = pattern.search(text_blob)
        if m:
            candidate = m.group(0).replace(" ", "").upper()
            for doctype, party in (("Sales Invoice", "Customer"), ("Purchase Invoice", "Supplier")):
                name = _find_open_invoice(doctype, candidate, None, amount=None)
                if name:
                    return {"invoice_type": doctype, "invoice_name": name, "party_type": party, "party": None}
    return {}


def _settings():
    from ebics_bank_connector.doctype.bank_automation_settings.bank_automation_settings import get_settings

    return get_settings()
