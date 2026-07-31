# Copyright (c) 2026, EBICS Bank Connector
"""Default EBICS backend based on the ``ebics-python`` library.

Adapter that maps the app's needs onto the ``ebics_python`` API. The
library is imported lazily so the app can be installed even if the
backend is swapped out for a different one.
"""
from __future__ import annotations

import logging
from datetime import date

import frappe

log = logging.getLogger(__name__)

# EBICS order type codes
ORDER_TYPES = {
    "Z53": "Z53",  # CAMT.053 - bank statements
    "Z54": "Z54",  # CAMT.054 - debit/credit notifications
}


def create(
    *,
    host_url: str,
    host_id: str,
    partner_id: str,
    user_id: str,
    version: str,
    signature_version: str,
    encryption_version: str,
    authentication_version: str,
    keyring_path: str,
    passphrase: str,
    allow_create: bool = False,
):
    try:
        from ebics.client import EbicsClient as _PyEbicsClient  # type: ignore
        from ebics.models import Keyring  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on env
        raise RuntimeError(
            "Die Bibliothek 'ebics-python' ist nicht installiert. "
            "Bitte 'pip install ebics-python' bzw. 'bench pip install ebics-python' ausf\u00fchren."
        ) from exc

    # ebics-python expects version strings like "3.0"
    keyring = Keyring(
        keys=keyring_path,
        passphrase=passphrase or None,
        create=allow_create,
        version=version,
        signature_version=signature_version,
        encryption_version=encryption_version,
        authentication_version=authentication_version,
    )
    client = _PyEbicsClient(
        keyring=keyring,
        host_id=host_id,
        partner_id=partner_id,
        user_id=user_id,
        url=host_url,
    )
    return _PyEbicsAdapter(client)


class _PyEbicsAdapter:
    """Thin adapter implementing the backend contract."""

    def __init__(self, client):
        self._c = client

    def ping(self):
        try:
            self._c.HEV()
        except Exception:
            # fall back to HPB if HEV unsupported
            self._c.HPB()

    def send_ini(self):
        self._c.INI()

    def send_hia(self):
        self._c.HIA()

    def fetch_bank_keys(self):
        self._c.HPB()

    def download(self, *, order_type: str, start: date, end: date, account=None) -> bytes:
        # ebics-python exposes C53/C54 download methods which return a dict
        # of {account_identifier: xml_content} (one entry per booked account).
        method = {
            "Z53": getattr(self._c, "C53", None),
            "Z54": getattr(self._c, "C54", None),
        }.get(order_type)
        if method is None:
            raise NotImplementedError(f"Order type {order_type} not supported by backend")
        result = method(start_date=start, end_date=end)
        return _extract_account_xml(result, account)

    def list_accounts(self):
        htd = getattr(self._c, "HTD", None)
        if htd is None:
            return []
        try:
            return htd()
        except Exception:
            log.exception("HTD account discovery failed")
            return []


def _extract_account_xml(result, account: str | None) -> bytes:
    """Normalise the C53/C54 return value to raw XML bytes.

    ebics-python returns a dict ``{account_id: xml}`` (one entry per booked
    account). When ``account`` (IBAN) is given we filter to that entry;
    otherwise we concatenate all statements so the parser can split them.
    A bare bytes/str return (older backends, stub) is passed through.
    """
    if result is None:
        return b""
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    if isinstance(result, str):
        return result.encode("utf-8")
    if isinstance(result, dict):
        if account:
            # try exact key, then IBAN substring match
            for key, xml in result.items():
                if key == account or (isinstance(key, str) and account in key):
                    return _to_bytes(xml)
            return b""
        # no account filter: concatenate all statements
        parts = [_to_bytes(xml) for xml in result.values()]
        return b"\n".join(parts) if parts else b""
    return b""


def _to_bytes(value) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return str(value).encode("utf-8")
