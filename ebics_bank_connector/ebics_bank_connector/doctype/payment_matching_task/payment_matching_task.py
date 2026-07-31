# Copyright (c) 2026, EBICS Bank Connector
"""Payment Matching Task doctype controller."""
import frappe
from frappe.model.document import Document


class PaymentMatchingTask(Document):
    def on_update(self):
        if self.has_value_changed("status") and self.status in ("Zugeordnet", "Ignoriert"):
            self.resolved_by = self.resolved_by or frappe.session.user
            self.resolved_on = self.resolved_on or frappe.utils.now()
