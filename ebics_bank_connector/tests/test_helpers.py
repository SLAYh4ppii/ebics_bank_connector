# Copyright (c) 2026, EBICS Bank Connector
"""Shared test helpers."""
import frappe


def ensure_company_and_bank_account():
    """Return (company, bank_account) - creating a minimal set if needed."""
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        company = frappe.get_all("Company", pluck="name", limit=1)
        company = company[0] if company else None
    if not company:
        company = frappe.get_doc(
            {
                "doctype": "Company",
                "company_name": "_Test EBICS Co",
                "country": "Germany",
                "default_currency": "EUR",
            }
        ).insert()
        company = company.name

    bank_account = frappe.db.exists("Bank Account", {"company": company, "iban": "DE89370400440532013000"})
    if bank_account:
        return company, bank_account

    bank = frappe.db.exists("Bank", {"bank_name": "VR-Bank Test"}) or frappe.get_doc(
        {"doctype": "Bank", "bank_name": "VR-Bank Test"}
    ).insert().name

    # ensure a GL account exists for the bank
    gl = frappe.get_all(
        "Account",
        filters={"company": company, "account_type": "Bank", "is_group": 0},
        pluck="name",
        limit=1,
    )
    if not gl:
        gl = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": "Bank",
                "parent_account": frappe.get_all("Account", filters={"company": company, "is_group": 1, "account_type": "Application of Funds (Assets)"}, pluck="name", limit=1)[0],
                "company": company,
                "account_type": "Bank",
                "account_currency": "EUR",
            }
        ).insert().name
    else:
        gl = gl[0]

    ba = frappe.get_doc(
        {
            "doctype": "Bank Account",
            "bank": bank,
            "account_name": "Girokonto Test",
            "iban": "DE89370400440532013000",
            "account": gl,
            "company": company,
        }
    ).insert()
    return company, ba.name
