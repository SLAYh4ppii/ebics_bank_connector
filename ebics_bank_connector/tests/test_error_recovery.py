# Copyright (c) 2026, EBICS Bank Connector
"""Tests for the error-recovery / retry-counter logic (A5)."""
import frappe
from frappe.tests.utils import FrappeTestCase

from ebics_bank_connector.ebics_bank_connector.doctype.ebics_settings.ebics_settings import (
    MAX_CONSECUTIVE_ERRORS,
)
from ebics_bank_connector.ebics.backends import stub as stub_backend
from ebics_bank_connector.ebics import connection as connection_mod


class TestErrorRecovery(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._orig_load = connection_mod._load_backend
        connection_mod._load_backend = lambda: stub_backend

    @classmethod
    def tearDownClass(cls):
        connection_mod._load_backend = cls._orig_load
        super().tearDownClass()

    def setUp(self):
        from ebics_bank_connector.tests.test_helpers import ensure_company_and_bank_account

        self.company, self.bank_account = ensure_company_and_bank_account()
        self.settings = frappe.get_doc(
            {
                "doctype": "EBICS Settings",
                "connection_name": "Test-Err-" + frappe.generate_hash("", 5),
                "bank_preset": "VR-Bank",
                "host_url": "https://stub.example/ebics",
                "host_id": "HOST",
                "partner_id": "PARTNER",
                "user_id": "USER",
                "customer_id": "CUST",
                "ebics_version": "3.0",
                "sync_enabled": 1,
                "status": "Verbunden",
                "default_bank_account": self.bank_account,
                "auto_match": 0,
                "raw_xml_storage": 0,
            }
        ).insert()

    def test_error_increments_counter(self):
        self.settings.mark_error("network blip")
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "error_count"), 1
        )
        # status stays Verbunden for the first transient error
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "status"), "Verbunden"
        )

    def test_deactivates_after_max_errors(self):
        for i in range(MAX_CONSECUTIVE_ERRORS):
            self.settings.mark_error(f"failure {i}")
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "status"), "Deaktiviert"
        )

    def test_successful_sync_resets_counter(self):
        self.settings.mark_error("transient")
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "error_count"), 1
        )
        self.settings.mark_synced()
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "error_count"), 0
        )
        self.assertEqual(
            frappe.db.get_value("EBICS Settings", self.settings.name, "status"), "Verbunden"
        )

    def test_deactivated_connection_not_picked_up(self):
        for i in range(MAX_CONSECUTIVE_ERRORS):
            self.settings.mark_error(f"failure {i}")
        from ebics_bank_connector.sync import _due_connections

        due = _due_connections("St\u00fcndlich", hours=1)
        self.assertNotIn(self.settings.name, due)
