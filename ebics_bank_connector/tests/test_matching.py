# Copyright (c) 2026, EBICS Bank Connector
"""Tests for the matching engine invoice-number detection."""
import re

import frappe
from frappe.tests.utils import FrappeTestCase

from ebics_bank_connector.matching import INVOICE_PATTERNS


class TestMatchingPatterns(FrappeTestCase):
    def test_detects_re_invoice(self):
        text = "Rechnung RE-2026-001 Vielen Dank"
        self.assertTrue(any(p.search(text.upper()) for p in INVOICE_PATTERNS))

    def test_detects_compact_invoice(self):
        text = "RE2026001"
        self.assertTrue(any(p.search(text.upper()) for p in INVOICE_PATTERNS))

    def test_no_false_positive(self):
        text = "Gehalt Juli 2026"
        self.assertFalse(any(p.search(text.upper()) for p in INVOICE_PATTERNS))

    def test_detects_purchase_invoice(self):
        text = "PINV-2026-0001 Lieferant"
        self.assertTrue(any(p.search(text.upper()) for p in INVOICE_PATTERNS))
