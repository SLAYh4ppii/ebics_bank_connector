# Copyright (c) 2026, EBICS Bank Connector
"""EBICS Bank Account doctype controller."""
import frappe
from frappe.model.document import Document


class EBICSBankAccount(Document):
    def validate(self):
        self.iban = (self.iban or "").upper().replace(" ", "")
        if self.bank_account:
            # keep the linked ERPNext Bank Account currency in sync
            ba = frappe.get_cached_value(
                "Bank Account", self.bank_account, ["account", "bank"], as_dict=True
            )
            if ba and ba.account:
                gl_account_currency = frappe.get_cached_value(
                    "Account", ba.account, "account_currency"
                )
                if gl_account_currency and self.currency and gl_account_currency != self.currency:
                    frappe.throw(
                        frappe._(
                            "Die W\u00e4hrung ({0}) passt nicht zum verkn\u00fcpften ERPNext-Konto ({1})."
                        ).format(self.currency, gl_account_currency)
                    )
