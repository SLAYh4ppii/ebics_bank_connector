# Copyright (c) 2026, EBICS Bank Connector
"""Server-side helpers for the Banking Setup Wizard."""
import frappe

from ebics_bank_connector.utils import require_role


@frappe.whitelist()
def get_bank_presets():
    """Return known EBICS presets (URL hints) for the bank selector."""
    return {
        "VR-Bank": {"hint_url": "https://banking.vr-nordrhoen.de/ebics/ebics.aspx", "version": "3.0"},
        "Volksbank": {"hint_url": "", "version": "3.0"},
        "Sparkasse": {"hint_url": "", "version": "3.0"},
        "Andere EBICS Bank": {"hint_url": "", "version": "3.0"},
    }


@frappe.whitelist()
def get_existing_banks():
    """Banks + Bank Accounts already in ERPNext, for the account picker."""
    banks = frappe.get_all("Bank", fields=["name", "bank_name"])
    bank_accounts = frappe.get_all("Bank Account", fields=["name", "bank", "account", "iban"])
    return {"banks": banks, "bank_accounts": bank_accounts}


@frappe.whitelist()
def create_connection(payload):
    """Persist the wizard result: EBICS Settings + EBICS Bank Account rows."""
    require_role("Bank Administrator")
    payload = frappe.parse_json(payload) if isinstance(payload, str) else payload

    settings = frappe.get_doc(
        {
            "doctype": "EBICS Settings",
            "connection_name": payload.get("connection_name") or payload.get("bank_preset"),
            "bank_preset": payload.get("bank_preset"),
            "bank": payload.get("bank"),
            "host_url": payload.get("host_url"),
            "host_id": payload.get("host_id"),
            "partner_id": payload.get("partner_id"),
            "user_id": payload.get("user_id"),
            "customer_id": payload.get("customer_id"),
            "ebics_version": payload.get("ebics_version", "3.0"),
            "signature_version": payload.get("signature_version", "A006"),
            "encryption_version": payload.get("encryption_version", "E002"),
            "authentication_version": payload.get("authentication_version", "X002"),
            "keys_passphrase": payload.get("keys_passphrase"),
            "sync_enabled": 1,
            "default_bank_account": payload.get("default_bank_account"),
            "auto_match": 1,
        }
    )
    settings.insert(ignore_permissions=True)

    for acc in payload.get("accounts", []):
        frappe.get_doc(
            {
                "doctype": "EBICS Bank Account",
                "ebics_settings": settings.name,
                "iban": acc.get("iban"),
                "account_number": acc.get("account_number"),
                "currency": acc.get("currency", "EUR"),
                "account_type": acc.get("account_type", "Girokonto"),
                "bank_account": acc.get("bank_account") or payload.get("default_bank_account"),
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)

    return {"settings": settings.name}
