# Copyright (c) 2026, EBICS Bank Connector
"""Tests for the setup-wizard role enforcement (A2)."""
import frappe
from frappe.tests.utils import FrappeTestCase


class TestWizardRoleEnforcement(FrappeTestCase):
    def test_create_connection_requires_admin_role(self):
        """A user without the Bank Administrator role must be rejected."""
        from ebics_bank_connector.ebics_bank_connector.page.banking_setup_wizard.banking_setup_wizard import (
            create_connection,
        )

        # create a test user with only the Bank Mitarbeiter role
        test_user = frappe.get_doc(
            {
                "doctype": "User",
                "email": f"test-mitarbeiter-{frappe.generate_hash('', 5)}@example.com",
                "first_name": "Test",
                "last_name": "Mitarbeiter",
                "send_welcome_email": 0,
                "roles": [{"role": "Bank Mitarbeiter"}],
            }
        ).insert(ignore_permissions=True)

        frappe.set_user(test_user.name)
        try:
            with self.assertRaises(frappe.PermissionError):
                create_connection(
                    {
                        "connection_name": "Should Fail",
                        "bank_preset": "VR-Bank",
                        "host_url": "https://stub.example/ebics",
                        "host_id": "H",
                        "partner_id": "P",
                        "user_id": "U",
                    }
                )
        finally:
            frappe.set_user("Administrator")
            test_user.delete(ignore_permissions=True)
