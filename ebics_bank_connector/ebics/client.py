# Copyright (c) 2026, EBICS Bank Connector
"""High-level EBICS client.

Wraps a pluggable backend (see :mod:`ebics_bank_connector.ebics.connection`)
and exposes the small set of operations the rest of the app needs:

    ping()                 -> HEV / HPB round-trip
    send_ini_letter()      -> upload A004 signature key
    send_hia_letter()     -> upload E002 encryption + X002 auth keys
    fetch_bank_keys()     -> HPB (download bank public keys)
    fetch_statements()    -> Z53 (CAMT.053) for a date range
    fetch_notifications() -> Z54 (CAMT.054) for a date range (optional)

The backend object passed in must implement the methods below; the default
implementation lives in ``backends.ebics_python``.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional

import frappe

log = logging.getLogger(__name__)


class EbicsClient:
    def __init__(self, settings, backend):
        self.settings = settings
        self.backend = backend

    # ------------------------------------------------------------------
    # connectivity
    # ------------------------------------------------------------------
    def ping(self) -> None:
        """Verify the endpoint + keys with a lightweight round-trip."""
        self.backend.ping()

    # ------------------------------------------------------------------
    # key lifecycle
    # ------------------------------------------------------------------
    def send_ini_letter(self) -> None:
        self.backend.send_ini()

    def send_hia_letter(self) -> None:
        self.backend.send_hia()

    def fetch_bank_keys(self) -> None:
        self.backend.fetch_bank_keys()

    # ------------------------------------------------------------------
    # statement download
    # ------------------------------------------------------------------
    def fetch_statements(
        self,
        start: date,
        end: date,
        account: Optional[str] = None,
    ) -> bytes:
        """Download CAMT.053 (EBICS order type Z53) as raw XML bytes."""
        return self.backend.download(order_type="Z53", start=start, end=end, account=account)

    def fetch_notifications(
        self,
        start: date,
        end: date,
        account: Optional[str] = None,
    ) -> bytes:
        """Download CAMT.054 (EBICS order type Z54) as raw XML bytes."""
        return self.backend.download(order_type="Z54", start=start, end=end, account=account)

    # ------------------------------------------------------------------
    # account discovery (HPD / HTD)
    # ------------------------------------------------------------------
    def list_accounts(self) -> List[dict]:
        """Return list of ``{iban, account_number, currency, description}``."""
        try:
            return self.backend.list_accounts()
        except NotImplementedError:
            # backend does not support HTD; caller falls back to manual entry
            return []


def _to_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    raise TypeError(f"Cannot coerce {value!r} to date")
