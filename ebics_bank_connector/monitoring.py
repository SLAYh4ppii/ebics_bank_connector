# Copyright (c) 2026, EBICS Bank Connector
"""Payment monitoring.

Daily checks for:
  * open invoices past their due date (warn after N days)
  * recurring subscription payments that did not arrive
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

import frappe
from frappe.utils import add_days, getdate, nowdate

from ebics_bank_connector.notifications import notify_admin, notify_user

log = logging.getLogger(__name__)


def run_daily_monitoring():
    settings = _settings()
    _check_open_invoices(settings.days_open_threshold)
    _check_subscriptions(settings.days_subscription_threshold)


def _check_open_invoices(threshold_days: int):
    today = getdate()
    rows = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "status": ["in", ["Unpaid", "Overdue"]],
            "outstanding_amount": [">", 0],
        },
        fields=["name", "customer", "due_date", "outstanding_amount", "posting_date"],
    )
    for r in rows:
        due = getdate(r.due_date) or getdate(r.posting_date)
        overdue_days = (today - due).days
        if overdue_days >= threshold_days:
            msg = frappe._(
                "Rechnung {0} (Kunde {1}) ist seit {2} Tagen offen. Betrag: {3}"
            ).format(r.name, r.customer, overdue_days, r.outstanding_amount)
            _create_todo(
                frappe._("Offene Rechnung: {0}").format(r.name), msg, r.name, "Sales Invoice"
            )
            notify_admin(subject=frappe._("Offene Rechnung: {0}").format(r.name), message=msg)


def _check_subscriptions(threshold_days: int):
    today = getdate()
    if not frappe.db.table_exists("Subscription"):
        return
    subs = frappe.get_all(
        "Subscription",
        filters={"docstatus": 1, "status": ["in", ["Active", "Trial"]]},
        fields=["name", "customer", "next_date"],
    )
    for s in subs:
        next_date = getdate(s.next_date)
        if next_date and (today - next_date).days >= threshold_days:
            # no matching payment entry found for this period
            if not _has_recent_payment(s.name, next_date):
                msg = frappe._(
                    "Abo {0} (Kunde {1}): erwartete Zahlung am {2} fehlt."
                ).format(s.name, s.customer, next_date)
                _create_todo(
                    frappe._("Abo-Zahlung fehlt: {0}").format(s.name), msg, s.name, "Subscription"
                )
                notify_admin(subject=frappe._("Abo-Zahlung fehlt: {0}").format(s.name), message=msg)


def _has_recent_payment(subscription_name, expected_date) -> bool:
    # Subscription references are not standardized; check Payment Entry remarks
    window = add_days(expected_date, 10)
    return bool(
        frappe.db.exists(
            "Payment Entry",
            {
                "docstatus": 1,
                "posting_date": ["between", [expected_date, window]],
                "remarks": ["like", f"%{subscription_name}%"],
            },
        )
    )


def _create_todo(subject, description, reference, reference_type):
    if frappe.db.exists(
        "ToDo", {"reference_type": reference_type, "reference_name": reference, "status": "Open"}
    ):
        return
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "subject": subject,
            "description": description,
            "reference_type": reference_type,
            "reference_name": reference,
            "status": "Open",
            "priority": "Medium",
            "allocated_to": _settings().admin_user or "Administrator",
        }
    ).insert(ignore_permissions=True)


def _settings():
    from ebics_bank_connector.doctype.bank_automation_settings.bank_automation_settings import get_settings

    return get_settings()
