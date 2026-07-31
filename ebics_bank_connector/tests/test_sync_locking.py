# Copyright (c) 2026, EBICS Bank Connector
"""Tests for sync locking (B1) and backend account filtering (A4)."""
import frappe
from frappe.tests.utils import FrappeTestCase

from ebics_bank_connector.ebics.backends import stub as stub_backend
from ebics_bank_connector.ebics import connection as connection_mod


class TestSyncLocking(FrappeTestCase):
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
                "connection_name": "Test-Lock-" + frappe.generate_hash("", 5),
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
        self.ebics_account = frappe.get_doc(
            {
                "doctype": "EBICS Bank Account",
                "ebics_settings": self.settings.name,
                "iban": "DE89370400440532013000",
                "currency": "EUR",
                "bank_account": self.bank_account,
                "enabled": 1,
            }
        ).insert()
        # clear any leftover lock
        frappe.cache().delete(f"ebics_sync_lock:{self.settings.name}")

    def test_second_sync_skipped_while_locked(self):
        from ebics_bank_connector.sync import sync_connection

        # pre-set the lock as if another sync is running
        frappe.cache().set(f"ebics_sync_lock:{self.settings.name}", True)
        result = sync_connection(self.settings.name)
        self.assertFalse(result["ok"])
        self.assertIn("bereits", result.get("message", ""))
        # lock must still be present (we set it, sync must not clear it)
        self.assertTrue(frappe.cache().get(f"ebics_sync_lock:{self.settings.name}"))

    def test_lock_released_after_sync(self):
        from ebics_bank_connector.sync import sync_connection

        sync_connection(self.settings.name)
        # lock should be cleared after a successful sync
        self.assertFalse(frappe.cache().get(f"ebics_sync_lock:{self.settings.name}"))

    def test_lock_released_after_failed_sync(self):
        from ebics_bank_connector.sync import sync_connection

        # break the connection so sync fails, then verify lock is released
        frappe.db.set_value("EBICS Settings", self.settings.name, "status", "Fehler")
        sync_connection(self.settings.name)
        self.assertFalse(frappe.cache().get(f"ebics_sync_lock:{self.settings.name}"))


class TestBackendAccountFilter(FrappeTestCase):
    """Verify the stub backend filters by account (A4)."""

    def test_stub_returns_xml_for_matching_iban(self):
        xml = stub_backend.create().download(
            order_type="Z53",
            start=frappe.utils.today(),
            end=frappe.utils.today(),
            account="DE89370400440532013000",
        )
        self.assertTrue(xml)

    def test_stub_returns_empty_for_non_matching_iban(self):
        xml = stub_backend.create().download(
            order_type="Z53",
            start=frappe.utils.today(),
            end=frappe.utils.today(),
            account="DE99OTHERIBAN",
        )
        self.assertEqual(xml, b"")
