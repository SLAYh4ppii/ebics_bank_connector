# Copyright (c) 2026, EBICS Bank Connector
"""Misc utilities: boot session, role checks, formatting."""
from __future__ import annotations

import frappe


def boot_session(session):
    """Expose minimal bank automation status to the desk client."""
    session["ebics_bank_connector"] = {
        "has_connection": bool(
            frappe.db.exists("EBICS Settings", {"status": "Verbunden"})
        ),
        "open_matching_tasks": frappe.db.count("Payment Matching Task", {"status": "Offen"}),
    }
    return session


def require_role(*roles: str):
    """Raise if the current user has none of the given bank roles."""
    if not roles:
        return
    if any(frappe.has_role(r) for r in roles) or frappe.has_role("System Manager"):
        return
    frappe.throw(
        frappe._("Sie haben keine Berechtigung f\u00fcr diese Aktion. Ben\u00f6tigte Rolle: {0}").format(
            ", ".join(roles)
        ),
        frappe.PermissionError,
    )
