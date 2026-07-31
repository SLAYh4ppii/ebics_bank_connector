# Copyright (c) 2026, EBICS Bank Connector
"""Bank Automation Settings (single) doctype controller."""
import frappe
from frappe.model.document import Document


class BankAutomationSettings(Document):
    pass


def get_settings() -> "BankAutomationSettings":
    """Return the cached single instance of the automation settings."""
    return frappe.get_cached_doc("Bank Automation Settings", "Bank Automation Settings")
