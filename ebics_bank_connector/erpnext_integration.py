# Copyright (c) 2026, EBICS Bank Connector
"""ERPNext integration: create ``Bank Transaction`` records from parsed CAMT data.

This module is the only place that touches ERPNext core doctypes directly,
keeping the rest of the app decoupled. It is defensive about field names so
it keeps working across minor ERPNext 16 patch releases.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

import frappe
from frappe.utils import cint, flt, getdate

from ebics_bank_connector.ebics.camt_parser import Transaction

log = logging.getLogger(__name__)


def bank_transaction_exists(transaction_id: str, bank_account: str) -> bool:
    if not transaction_id:
        return False
    return frappe.db.exists(
        "Bank Transaction",
        {"transaction_id": transaction_id, "bank_account": bank_account},
    )


def create_bank_transaction(
    tx: Transaction,
    bank_account: str,
    company: Optional[str] = None,
) -> Optional[str]:
    """Create a Bank Transaction from a parsed CAMT entry. Returns name or None."""
    if not bank_account:
        raise ValueError("bank_account is required")

    if bank_transaction_exists(tx.transaction_id, bank_account):
        return None

    if not company:
        company = frappe.get_cached_value("Bank Account", bank_account, "company") or _company_for_account(bank_account)
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company") or erpnext_company()

    amount = flt(tx.amount)
    deposit = flt(amount) if amount > 0 else 0.0
    withdrawal = flt(-amount) if amount < 0 else 0.0

    doc = frappe.get_doc(
        {
            "doctype": "Bank Transaction",
            "bank_account": bank_account,
            "company": company,
            "date": getdate(tx.posting_date or tx.value_date),
            "deposit": deposit,
            "withdrawal": withdrawal,
            "transaction_id": tx.transaction_id or tx.account_servicer_ref or "",
            "reference_no": tx.reference or tx.account_servicer_ref or "",
            "reference_date": getdate(tx.value_date),
            "description": _build_description(tx),
            "party_type": "",
            "party": "",
            "status": "Pending",
            "unallocated_amount": abs(amount),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _build_description(tx: Transaction) -> str:
    parts = [tx.counterparty_name, tx.description, tx.reference]
    return " | ".join(p for p in parts if p)


def _company_for_account(bank_account: str) -> Optional[str]:
    gl_account = frappe.get_cached_value("Bank Account", bank_account, "account")
    if gl_account:
        return frappe.get_cached_value("Account", gl_account, "company")
    return None


def erpnext_company() -> Optional[str]:
    companies = frappe.get_all("Company", pluck="name", limit=1)
    return companies[0] if companies else None


def get_bank_account_for_iban(iban: str) -> Optional[str]:
    """Find an ERPNext Bank Account by IBAN (stored on Bank Account)."""
    if not iban:
        return None
    iban = iban.upper().replace(" ", "")
    # ERPNext stores IBAN on the Bank Account doctype
    name = frappe.db.get_value("Bank Account", {"iban": iban}, "name")
    return name
