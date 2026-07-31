# Copyright (c) 2026, EBICS Bank Connector
"""Swappable EBICS backend factory.

The default backend is the ``fintech`` library (distributed on PyPI as
``fintech``). It can be replaced by any module that exposes an
``EbicsClient``-compatible class.

The backend is selected via the ``ebics_backend`` field in the
**Bank Automation Settings** (Dashboard). The legacy ``site_config.json``
key ``ebics_backend`` is still supported as a fallback.

All bank key material is stored on disk in the site's private folder
(``private/files/ebics_keys/<connection>/keys.pem``). The key file is
encrypted by the ``fintech`` ``EbicsKeyRing`` using the passphrase supplied
in the EBICS Settings (Frappe ``Password`` field, decrypted on demand).
The ``private/files`` directory is not served by the web server.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

import frappe
from frappe.utils import cstr

if TYPE_CHECKING:
    from ebics_bank_connector.ebics.client import EbicsClient
    from ebics_bank_connector.ebics_bank_connector.doctype.ebics_settings.ebics_settings import (
        EBICSSettings,
    )

DEFAULT_BACKEND = "ebics_bank_connector.ebics.backends.ebics_python"


def get_connection(settings: "EBICSSettings", allow_create: bool = False) -> "EbicsClient":
    """Return a high-level :class:`EbicsClient` bound to ``settings``."""
    from ebics_bank_connector.ebics.client import EbicsClient

    backend = _load_backend()
    keyring_dir = _keyring_dir(settings.name)
    os.makedirs(keyring_dir, exist_ok=True)

    backend_client = backend.create(
        host_url=settings.host_url,
        host_id=settings.host_id,
        partner_id=settings.partner_id,
        user_id=settings.user_id,
        version=settings.ebics_version,
        signature_version=settings.signature_version,
        encryption_version=settings.encryption_version,
        authentication_version=settings.authentication_version,
        keyring_path=os.path.join(keyring_dir, "keys.pem"),
        passphrase=settings.get_passphrase(),
        allow_create=allow_create,
    )
    return EbicsClient(settings, backend_client)


def _load_backend():
    """Resolve the backend module: Dashboard setting > site_config > default."""
    backend_path = None
    try:
        from ebics_bank_connector.ebics_bank_connector.doctype.bank_automation_settings.bank_automation_settings import (
            get_settings,
        )
        settings = get_settings()
        backend_path = settings.get("ebics_backend")
    except Exception:
        pass
    if not backend_path:
        backend_path = frappe.conf.get("ebics_backend") or DEFAULT_BACKEND
    module = frappe.get_module(backend_path)
    if not hasattr(module, "create"):
        raise RuntimeError(f"EBICS backend {backend_path!r} has no create() factory")
    return module


def _keyring_dir(settings_name: str) -> str:
    site_path = frappe.get_site_path("private", "files", "ebics_keys")
    safe = "".join(c for c in cstr(settings_name) if c.isalnum() or c in "-_") or "default"
    return os.path.join(site_path, safe)
