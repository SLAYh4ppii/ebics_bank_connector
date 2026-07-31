# Copyright (c) 2026, EBICS Bank Connector
"""In-memory stub backend used for tests / dry-runs.

Returns deterministic CAMT.053 sample XML so the rest of the pipeline
(parser, sync, matching) can be exercised without a real bank.
"""
from __future__ import annotations

from datetime import date

from ebics_bank_connector.tests.sample_camt import SAMPLE_CAMT053


def create(**kwargs):
    return _StubBackend(**kwargs)


class _StubBackend:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def ping(self):
        return None

    def send_ini(self):
        return None

    def send_hia(self):
        return None

    def fetch_bank_keys(self):
        return None

    def download(self, *, order_type, start: date, end: date, account=None) -> bytes:
        if order_type == "Z53":
            xml = SAMPLE_CAMT053.encode("utf-8")
            # when an account filter is given, return empty for non-matching IBANs
            if account and account != "DE89370400440532013000":
                return b""
            return xml
        return b""

    def list_accounts(self):
        return [
            {"iban": "DE89370400440532013000", "account_number": "44053201300", "currency": "EUR", "description": "Girokonto"},
        ]
