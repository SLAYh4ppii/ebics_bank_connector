"""Install hooks for ebics_bank_connector.

Creates the three custom roles used by the app and seeds default
automation settings. Idempotent: safe to run multiple times.
"""
import frappe
from frappe.core.doctype.role.role import Role


ROLES = [
    {"role_name": "Bank Administrator", "desk_access": 1},
    {"role_name": "Bank Buchhalter", "desk_access": 1},
    {"role_name": "Bank Mitarbeiter", "desk_access": 1},
]


def _ensure_roles():
    for r in ROLES:
        if not frappe.db.exists("Role", r["role_name"]):
            doc = frappe.get_doc({"doctype": "Role", **r, "is_custom": 1})
            doc.insert(ignore_permissions=True)


def _ensure_automation_settings():
    if not frappe.db.exists("Bank Automation Settings", "Bank Automation Settings"):
        frappe.get_doc({"doctype": "Bank Automation Settings"}).insert(
            ignore_permissions=True
        )


def before_install():
    pass


def after_install():
    _ensure_roles()
    _ensure_automation_settings()
