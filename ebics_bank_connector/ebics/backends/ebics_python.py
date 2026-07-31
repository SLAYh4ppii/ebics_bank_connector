# Copyright (c) 2026, EBICS Bank Connector
"""Default EBICS backend based on the ``fintech`` library (PyPI: fintech).

Adapter that maps the app's needs onto the ``fintech.ebics`` API. The
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
    "Z53": "C53",  # CAMT.053 - bank statements
    "Z54": "C54",  # CAMT.054 - debit/credit notifications
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
        import fintech
        fintech.register()
        from fintech.ebics import EbicsKeyRing, EbicsBank, EbicsUser, EbicsClient
    except ImportError as exc:  # pragma: no cover - depends on env
        raise RuntimeError(
            "Die Bibliothek 'fintech' ist nicht installiert. "
            "Bitte 'pip install fintech' bzw. 'bench pip install fintech' ausf\u00fchren."
        ) from exc

    keyring = EbicsKeyRing(
        keys=keyring_path,
        passphrase=passphrase or None,
    )
    bank = EbicsBank(keyring=keyring, hostid=host_id, url=host_url)
    user = EbicsUser(keyring=keyring, partnerid=partner_id, userid=user_id)

    if allow_create:
        user.create_keys(keyversion=signature_version, bitlength=2048)

    client = EbicsClient(bank, user)
    return _FintechAdapter(client, bank, user)


class _FintechAdapter:
    """Thin adapter implementing the backend contract."""

    def __init__(self, client, bank, user):
        self._c = client
        self._bank = bank
        self._user = user

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
        self._bank.activate_keys()

    def download(self, *, order_type: str, start: date, end: date, account=None) -> bytes:
        method_name = ORDER_TYPES.get(order_type)
        if method_name is None:
            raise NotImplementedError(f"Order type {order_type} not supported by backend")
        method = getattr(self._c, method_name, None)
        if method is None:
            raise NotImplementedError(f"Order type {order_type} not supported by backend")
        result = method(start=start, end=end)
        # confirm receipt with the bank so the download is acknowledged
        try:
            self._c.confirm_download()
        except Exception:
            log.warning("confirm_download failed for %s", order_type)
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

    ``fintech`` returns a dict ``{account_id: xml}`` (one entry per booked
    account). When ``account`` (IBAN) is given we filter to that entry;
    otherwise we concatenate all statements so the parser can split them.
    A bare bytes/str return is passed through.
    """
    if result is None:
        return b""
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    if isinstance(result, str):
        return result.encode("utf-8")
    if isinstance(result, dict):
        if account:
            for key, xml in result.items():
                if key == account or (isinstance(key, str) and account in key):
                    return _to_bytes(xml)
            return b""
        parts = [_to_bytes(xml) for xml in result.values()]
        return b"\n".join(parts) if parts else b""
    return b""


def _to_bytes(value) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return str(value).encode("utf-8")
