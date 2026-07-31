# Copyright (c) 2026, EBICS Bank Connector
"""Integration test: full sync pipeline using the stub EBICS backend.

Requires ERPNext + a Company + a Bank Account. The stub backend is selected
via ``site_config`` ``ebics_backend`` or by monkey-patching the factory.
"""
import frappe
from frappe.tests.utils import FrappeTestCase

from ebics_bank_connector.ebics.backends import stub as stub_backend
from ebics_bank_connector.ebics import connection as connection_mod


class TestSyncPipeline(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force the stub backend for the whole test class
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
                "connection_name": "Test-Stub-" + frappe.generate_hash("", 5),
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

    def test_sync_imports_transactions(self):
        from ebics_bank_connector.sync import sync_connection

        result = sync_connection(self.settings.name)
        self.assertTrue(result["ok"], result.get("errors"))
        self.assertEqual(result["imported"], 2)
        # Bank Transactions created
        count = frappe.db.count(
            "Bank Transaction", {"bank_account": self.bank_account}
        )
        self.assertGreaterEqual(count, 2)

    def test_sync_is_idempotent(self):
        from ebics_bank_connector.sync import sync_connection

        sync_connection(self.settings.name)
        result = sync_connection(self.settings.name)
        # second run should detect duplicates (same transaction ids)
        self.assertEqual(result["imported"], 0)
