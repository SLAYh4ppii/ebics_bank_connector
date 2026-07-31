// Copyright (c) 2026, EBICS Bank Connector
// For license information, see the LICENSE file.
frappe.ui.form.on("EBICS Settings", {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Verbindung testen"), () =>
                frm.call("test_connection").then((r) => show_result(r.message))
            );
            frm.add_custom_button(__("Jetzt synchronisieren"), () =>
                frappe.call({
                    method: "ebics_bank_connector.sync_now",
                    args: { settings: frm.doc.name },
                    freeze: true,
                }).then((r) => show_result(r.message))
            );
            if (!frm.doc.keys_initialized) {
                frm.add_custom_button(__("EBICS Schl\u00fcssel initialisieren"), () =>
                    frm.call("initialize_keys").then((r) => {
                        frappe.msgprint(r.message.message || __("Schl\u00fcssel initialisiert."));
                        frm.reload_doc();
                    })
                );
            }
        }
    },
});

function show_result(msg) {
    if (!msg) return;
    if (msg.ok) {
        frappe.msgprint({ indicator: "green", title: __("Erfolg"), message: msg.message });
    } else {
        frappe.msgprint({ indicator: "red", title: __("Fehler"), message: msg.message });
    }
}
