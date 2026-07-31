# Copyright (c) 2026, EBICS Bank Connector
# For license information, see the LICENSE file.
"""EBICS Settings doctype controller.

Stores a single bank connection (EBICS host/partner/user credentials) and
manages the local EBICS key material lifecycle (INI / HIA / HPB).
"""
import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password

# After this many consecutive errors the connection is auto-deactivated
# so the scheduler stops retrying a broken endpoint. A successful sync
# resets the counter to zero and re-activates the connection.
MAX_CONSECUTIVE_ERRORS = 3


class EBICSSettings(Document):
    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------
    def validate(self):
        self.host_url = (self.host_url or "").strip().rstrip("/")
        if self.sync_enabled and not self.default_bank_account:
            frappe.throw(
                frappe._("Bitte w\u00e4hlen Sie ein ERPNext Bank Account f\u00fcr die Synchronisation.")
            )

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def on_update(self):
        # keep the connection status sane
        if self.status == "Entwurf" and self.keys_initialized:
            self.db_set("status", "Verbunden")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return bool(self.sync_enabled and self.status == "Verbunden")

    def mark_synced(self):
        """Reset error counter and clear status on a successful sync."""
        frappe.db.set_value(
            self.doctype,
            self.name,
            {"last_sync": frappe.utils.now(), "error_count": 0, "status": "Verbunden"},
            update_modified=False,
        )

    def mark_error(self, message: str):
        """Increment the error counter; deactivate after MAX_CONSECUTIVE_ERRORS.

        The status stays 'Verbunden' for the first few transient errors so the
        scheduler keeps retrying. Only after repeated failures does the
        connection flip to 'Deaktiviert' and stops being picked up.
        """
        count = (self.error_count or 0) + 1
        now = frappe.utils.now()
        if count >= MAX_CONSECUTIVE_ERRORS:
            new_status = "Deaktiviert"
        else:
            new_status = "Verbunden"
        frappe.db.set_value(
            self.doctype,
            self.name,
            {"error_count": count, "last_error_on": now, "status": new_status},
            update_modified=False,
        )
        if self.notify_on_error:
            from ebics_bank_connector.notifications import notify_admin

            notify_admin(
                subject=frappe._("EBICS Verbindungsfehler: {0}").format(self.connection_name),
                message=message,
            )

    # ------------------------------------------------------------------
    # credential access (decrypted on demand, never logged)
    # ------------------------------------------------------------------
    def get_passphrase(self) -> str:
        if not self.keys_passphrase:
            return ""
        return get_decrypted_password(self.doctype, self.name, "keys_passphrase", raise_exception=False) or ""

    # ------------------------------------------------------------------
    # whitelisted server actions (called from form / wizard)
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def test_connection(self):
        """HEV / HPB round-trip to verify the EBICS endpoint + keys."""
        from ebics_bank_connector.ebics.connection import get_connection

        try:
            client = get_connection(self)
            client.ping()
            self.db_set("status", "Verbunden")
            return {"ok": True, "message": str(frappe._("Verbindung erfolgreich getestet."))}
        except Exception as exc:  # noqa: BLE001
            self.db_set("status", "Fehler")
            return {"ok": False, "message": _humanize_error(exc)}

    @frappe.whitelist()
    def initialize_keys(self):
        """Run the INI/HIA letter flow and fetch the HPB bank keys."""
        from ebics_bank_connector.ebics.connection import get_connection

        try:
            client = get_connection(self, allow_create=True)
            client.send_ini_letter()
            client.send_hia_letter()
            client.fetch_bank_keys()
            self.db_set(
                {
                    "keys_initialized": 1,
                    "ini_done": 1,
                    "hia_done": 1,
                    "hpb_done": 1,
                    "keys_status": "Aktiv (HPB empfangen)",
                    "status": "Verbunden",
                }
            )
            return {"ok": True, "message": str(frappe._("EBICS-Schl\u00fcssel erfolgreich initialisiert."))}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "message": _humanize_error(exc)}


def _humanize_error(exc) -> str:
    """Translate raw EBICS/protocol errors into user-friendly German messages."""
    msg = str(exc)
    friendly = {
        "EBICS_NO_USER": "Der Benutzer ist bei der Bank nicht bekannt. Bitte User ID pr\u00fcfen.",
        "EBICS_USER_UNKNOWN": "Der Benutzer ist bei der Bank nicht bekannt. Bitte User ID pr\u00fcfen.",
        "EBICS_AUTHENTICATION_FAILED": "Authentifizierung fehlgeschlagen. Schl\u00fcssel m\u00fcssen evtl. freigeschaltet werden.",
        "EBICS_KEYMGMT_UNSUPPORTED_ORDER": "Die Bank unterst\u00fctzt die angeforderte Auftragsart nicht.",
        "EBICS_CONNECTION": "Verbindung zur Bank konnte nicht hergestellt werden. Host URL pr\u00fcfen.",
    }
    for code, text in friendly.items():
        if code in msg:
            return f"{text} ({msg})"
    return msg

