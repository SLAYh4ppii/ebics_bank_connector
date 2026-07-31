// Copyright (c) 2026, EBICS Bank Connector
// Banking Setup Wizard - 4 step guided flow:
//   1. Bank auswählen
//   2. EBICS Daten eingeben
//   3. Verbindung testen
//   4. Konten auswählen
frappe.pages["banking_setup_wizard"].on_page = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Bank verbinden"),
        single_column: true,
    });

    const state = {
        step: 1,
        bank_preset: "VR-Bank",
        presets: {},
        banks: [],
        bank_accounts: [],
        discovered: [],
    };

    const $body = $(wrapper).find(".layout-main-section");
    $body.html('<div id="ebics-wizard"></div>');
    const $wiz = $("#ebics-wizard");

    function render() {
        $wiz.html(template());
        bind();
    }

    function template() {
        const steps = [1, 2, 3, 4].map((n) => {
            const active = n === state.step ? "active" : n < state.step ? "done" : "";
            const labels = ["Bank", "EBICS", "Test", "Konten"];
            return `<div class="ebics-step ${active}"><span class="ebics-step-num">${n}</span><span class="ebics-step-label">${labels[n - 1]}</span></div>`;
        }).join('<div class="ebics-step-sep"></div>');
        return `
        <div class="ebics-wizard">
            <div class="ebics-progress">${steps}</div>
            <div class="ebics-card">${step_body()}</div>
            <div class="ebics-actions">
                <button class="btn btn-default btn-ebics-prev" ${state.step === 1 ? "disabled" : ""}>${__("Zurück")}</button>
                <button class="btn btn-primary btn-ebics-next">${state.step === 4 ? __("Fertigstellen") : __("Weiter")}</button>
            </div>
        </div>`;
    }

    function step_body() {
        if (state.step === 1) return step1();
        if (state.step === 2) return step2();
        if (state.step === 3) return step3();
        return step4();
    }

    // ---- Step 1: Bank auswählen ----
    function step1() {
        const opts = ["VR-Bank", "Volksbank", "Sparkasse", "Andere EBICS Bank"]
            .map((b) => `<option ${state.bank_preset === b ? "selected" : ""}>${b}</option>`).join("");
        const banks = state.banks.map((b) => `<option value="${b.name}">${b.bank_name}</option>`).join("");
        return `
        <h3>${__("Bank auswählen")}</h3>
        <p class="text-muted">${__("Wählen Sie Ihre Bank. Die EBICS-Daten können im nächsten Schritt eingegeben werden.")}</p>
        <div class="row">
            <div class="col-md-6"><label>${__("Bank")}</label>
                <select class="form-control" id="ebics-bank-preset">${opts}</select></div>
            <div class="col-md-6"><label>${__("ERPNext Bank (optional)")}</label>
                <select class="form-control" id="ebics-bank"><option value="">${__("-- Neu anlegen --")}</option>${banks}</select></div>
        </div>
        <div class="row mt-3">
            <div class="col-md-6"><label>${__("Verbindungsname")}</label>
                <input class="form-control" id="ebics-conn-name" placeholder="${__("z.B. VR-Bank NordRhön - Girokonto")}"></div>
        </div>`;
    }

    // ---- Step 2: EBICS Daten eingeben ----
    function step2() {
        const hint = state.presets[state.bank_preset] || {};
        return `
        <h3>${__("EBICS Zugangsdaten")}</h3>
        <p class="text-muted">${__("Diese Daten erhalten Sie von Ihrer Bank (EBICS-Informationsblatt).")}</p>
        <div class="row">
            <div class="col-md-6"><label>Host URL</label><input class="form-control" id="ebics-host-url" value="${hint.hint_url || ""}" placeholder="https://..."></div>
            <div class="col-md-6"><label>Host ID</label><input class="form-control" id="ebics-host-id"></div>
            <div class="col-md-6 mt-2"><label>Partner ID</label><input class="form-control" id="ebics-partner-id"></div>
            <div class="col-md-6 mt-2"><label>User ID</label><input class="form-control" id="ebics-user-id"></div>
            <div class="col-md-6 mt-2"><label>Customer ID</label><input class="form-control" id="ebics-customer-id"></div>
            <div class="col-md-6 mt-2"><label>EBICS Version</label>
                <select class="form-control" id="ebics-version"><option>2.4</option><option>2.5</option><option selected>3.0</option></select></div>
            <div class="col-md-6 mt-2"><label>${__("Schlüssel-Passphrase")}</label><input type="password" class="form-control" id="ebics-passphrase"></div>
        </div>`;
    }

    // ---- Step 3: Verbindung testen ----
    function step3() {
        return `
        <h3>${__("Verbindung testen")}</h3>
        <p class="text-muted">${__("Wir prüfen die EBICS-Verbindung und initialisieren ggf. die Schlüssel.")}</p>
        <div id="ebics-test-result" class="alert" style="display:none"></div>
        <button class="btn btn-primary" id="ebics-test-btn">${__("Verbindung testen")}</button>`;
    }

    // ---- Step 4: Konten auswählen ----
    function step4() {
        const discovered = state.discovered.length
            ? state.discovered.map((a) => `
                <tr><td><input type="checkbox" class="ebics-acc-check" data-iban="${a.iban}" data-num="${a.account_number || ""}" data-ccy="${a.currency || "EUR"}" checked></td>
                <td>${a.iban}</td><td>${a.account_number || ""}</td><td>${a.currency || "EUR"}</td><td>${a.description || ""}</td></tr>`).join("")
            : `<tr><td colspan="5" class="text-muted">${__("Keine Konten automatisch erkannt. Bitte IBAN manuell eingeben.")}</td></tr>`;
        const ba = state.bank_accounts.map((b) => `<option value="${b.name}">${b.name} (${b.iban || ""})</option>`).join("");
        return `
        <h3>${__("Konten auswählen")}</h3>
        <p class="text-muted">${__("Wählen Sie die Konten, die überwacht werden sollen.")}</p>
        <table class="table"><thead><tr><th></th><th>IBAN</th><th>Konto-Nr.</th><th>Währung</th><th>Bezeichnung</th></tr></thead><tbody>${discovered}</tbody></table>
        <div class="row mt-2">
            <div class="col-md-4"><label>${__("IBAN manuell")}</label><input class="form-control" id="ebics-manual-iban" placeholder="DE..."></div>
            <div class="col-md-4"><label>${__("ERPNext Bank Account")}</label><select class="form-control" id="ebics-default-ba"><option value="">${__("-- neu --")}</option>${ba}</select></div>
        </div>`;
    }

    function bind() {
        $("#ebics-bank-preset").on("change", function () { state.bank_preset = $(this).val(); });
        $(".btn-ebics-prev").off("click").on("click", () => { if (state.step > 1) { state.step--; render(); } });
        $(".btn-ebics-next").off("click").on("click", next);
        if (state.step === 3) bind_test();
    }

    function next() {
        if (state.step === 1) {
            state.bank_preset = $("#ebics-bank-preset").val();
            state.connection_name = $("#ebics-conn-name").val() || state.bank_preset;
            state.bank = $("#ebics-bank").val() || null;
            state.step = 2; render();
        } else if (state.step === 2) {
            gather_step2();
            state.step = 3; render();
        } else if (state.step === 3) {
            state.step = 4; discover_accounts();
        } else if (state.step === 4) {
            finish();
        }
    }

    function gather_step2() {
        state.host_url = $("#ebics-host-url").val();
        state.host_id = $("#ebics-host-id").val();
        state.partner_id = $("#ebics-partner-id").val();
        state.user_id = $("#ebics-user-id").val();
        state.customer_id = $("#ebics-customer-id").val();
        state.ebics_version = $("#ebics-version").val();
        state.keys_passphrase = $("#ebics-passphrase").val();
    }

    function bind_test() {
        $("#ebics-test-btn").off("click").on("click", function () {
            const $r = $("#ebics-test-result").hide().removeClass("alert-success alert-danger");
            $r.text(__("Teste Verbindung...")).addClass("alert-info").show();
            // create the settings record first (draft), then test
            frappe.call({
                method: "ebics_bank_connector.page.banking_setup_wizard.banking_setup_wizard.create_connection",
                args: { payload: wizard_payload() },
                freeze: true,
                callback: (res) => {
                    if (!res.message || !res.message.settings) {
                        $r.removeClass("alert-info").addClass("alert-danger").text(__("Speichern fehlgeschlagen."));
                        return;
                    }
                    state.settings_name = res.message.settings;
                    frappe.call({
                        method: "ebics_bank_connector.initialize_keys",
                        args: { settings: state.settings_name },
                        freeze: true,
                        callback: (kres) => {
                            const k = kres.message || {};
                            frappe.call({
                                method: "ebics_bank_connector.test_connection",
                                args: { settings: state.settings_name },
                                freeze: true,
                                callback: (tres) => {
                                    const t = tres.message || {};
                                    $r.removeClass("alert-info");
                                    if (t.ok) {
                                        $r.addClass("alert-success").html("✅ " + t.message);
                                    } else {
                                        $r.addClass("alert-danger").html("❌ " + t.message);
                                    }
                                },
                            });
                        },
                    });
                },
            });
        });
    }

    function wizard_payload() {
        return {
            connection_name: state.connection_name,
            bank_preset: state.bank_preset,
            bank: state.bank,
            host_url: state.host_url,
            host_id: state.host_id,
            partner_id: state.partner_id,
            user_id: state.user_id,
            customer_id: state.customer_id,
            ebics_version: state.ebics_version,
            keys_passphrase: state.keys_passphrase,
            accounts: [],
        };
    }

    function discover_accounts() {
        if (!state.settings_name) { render(); return; }
        frappe.call({
            method: "ebics_bank_connector.list_accounts",
            args: { settings: state.settings_name },
            callback: (res) => {
                state.discovered = res.message || [];
                render();
            },
            error: () => { state.discovered = []; render(); },
        });
    }

    function finish() {
        const accounts = [];
        $(".ebics-acc-check:checked").each(function () {
            accounts.push({ iban: $(this).data("iban"), account_number: $(this).data("num"), currency: $(this).data("ccy"), account_type: "Girokonto" });
        });
        const manual = $("#ebics-manual-iban").val().trim();
        if (manual) accounts.push({ iban: manual, currency: "EUR", account_type: "Girokonto" });
        const default_ba = $("#ebics-default-ba").val() || null;

        frappe.call({
            method: "ebics_bank_connector.page.banking_setup_wizard.banking_setup_wizard.create_connection",
            args: { payload: { ...wizard_payload(), accounts, default_bank_account: default_ba } },
            freeze: true,
            callback: () => {
                frappe.msgprint({ indicator: "green", title: __("Fertig"), message: __("Bank verbunden! Die Synchronisation läuft automatisch.") });
                frappe.set_route("workspace", "bank-automation");
            },
        });
    }

    // bootstrap
    frappe.call({
        method: "ebics_bank_connector.page.banking_setup_wizard.banking_setup_wizard.get_bank_presets",
        callback: (r) => { state.presets = r.message || {}; },
    });
    frappe.call({
        method: "ebics_bank_connector.page.banking_setup_wizard.banking_setup_wizard.get_existing_banks",
        callback: (r) => {
            const d = r.message || {};
            state.banks = d.banks || [];
            state.bank_accounts = d.bank_accounts || [];
            render();
        },
    });
};
