# Copyright (c) 2026, EBICS Bank Connector
"""Notification helpers (Email + ERPNext Notification + ToDo)."""
from __future__ import annotations

import frappe
from frappe.utils import now


def notify_admin(subject: str, message: str):
    """Notify the configured admin user + email address.

    If no recipient is configured in Bank Automation Settings, the message is
    only logged (no silent fallback to a placeholder address).
    """
    settings = _settings()
    recipients = []
    if settings.notify_email:
        recipients.append(settings.notify_email)
    if settings.admin_user:
        email = frappe.get_cached_value("User", settings.admin_user, "email")
        if email and email not in recipients:
            recipients.append(email)

    if recipients:
        try:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=_wrap(message),
                reference_doctype="EBICS Settings",
            )
        except Exception:  # noqa: BLE001
            # never let notification failure break the sync
            frappe.log_error(title=f"EBICS notify failed: {subject}", message=message)
    else:
        # no recipient configured — log so it is at least visible in Error Log
        frappe.log_error(
            title=f"EBICS notification (no recipient configured): {subject}", message=message
        )

    _create_todo(subject, message)


def notify_user(user: str, subject: str, message: str):
    if not user:
        return notify_admin(subject, message)
    email = frappe.get_cached_value("User", user, "email") or user
    try:
        frappe.sendmail(recipients=[email], subject=subject, message=_wrap(message))
    except Exception:  # noqa: BLE001
        frappe.log_error(title=f"EBICS notify failed: {subject}", message=message)
    _create_todo(subject, message, assigned_to=user)


def _create_todo(subject, message, assigned_to=None):
    try:
        frappe.get_doc(
            {
                "doctype": "ToDo",
                "subject": subject[:140],
                "description": message,
                "status": "Open",
                "priority": "Medium",
                "allocated_to": assigned_to or _settings().admin_user or "Administrator",
            }
        ).insert(ignore_permissions=True)
    except Exception:  # noqa: BLE001
        frappe.log_error(title="EBICS ToDo create failed", message=message)


def _wrap(message: str) -> str:
    return f"""<div style="font-family: sans-serif; line-height: 1.5;">
<p>Hallo,</p>
<p>{message}</p>
<p style="color:#888; font-size:11px;">EBICS Bank Connector &middot; {now()}</p>
</div>"""


def _settings():
    from ebics_bank_connector.doctype.bank_automation_settings.bank_automation_settings import get_settings

    return get_settings()
