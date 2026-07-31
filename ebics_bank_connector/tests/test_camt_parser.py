# Copyright (c) 2026, EBICS Bank Connector
"""Unit tests for the CAMT.053 parser (no DB / no ERPNext required)."""
from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase

from ebics_bank_connector.ebics.camt_parser import parse_camt
from ebics_bank_connector.tests.sample_camt import SAMPLE_CAMT053


class TestCamtParser(FrappeTestCase):
    def test_parses_two_entries(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        self.assertEqual(len(txs), 2)

    def test_credit_amount_positive(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        credit = [t for t in txs if t.amount > 0][0]
        self.assertEqual(credit.amount, Decimal("150.00"))
        self.assertEqual(credit.currency, "EUR")
        self.assertEqual(credit.bank_account_iban, "DE89370400440532013000")

    def test_debit_amount_negative(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        debit = [t for t in txs if t.amount < 0][0]
        self.assertEqual(debit.amount, Decimal("-42.10"))

    def test_counterparty_extracted(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        credit = [t for t in txs if t.amount > 0][0]
        self.assertEqual(credit.counterparty_name, "Max Mustermann")
        self.assertEqual(credit.iban, "DE12500105170648489890")
        self.assertEqual(credit.bic, "COBADEFFXXX")

    def test_remittance_and_reference(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        credit = [t for t in txs if t.amount > 0][0]
        self.assertIn("RE-2026-001", credit.description)
        self.assertEqual(credit.reference, "E2E-001")
        self.assertEqual(credit.transaction_id, "ASR-001")

    def test_dates(self):
        txs = parse_camt(SAMPLE_CAMT053.encode("utf-8"))
        credit = [t for t in txs if t.amount > 0][0]
        self.assertIsNotNone(credit.value_date)
        self.assertIsNotNone(credit.posting_date)
