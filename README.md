# EBICS Bank Connector

Eine selbst gehostete Banking-Erweiterung für **ERPNext 16**, die Bankkonten
über **EBICS** automatisch überwacht, Umsätze importiert (CAMT.053) und
Zahlungen automatisch Rechnungen zuordnet.

> Bank verbinden → Synchronisieren → Automatisch buchen.

Eine Alternative zu GoCardless Banking, aber mit **EBICS** und vollständiger
ERPNext-16-Integration. Entwickelt und getestet mit der **VR-Bank NordRhön eG**,
funktioniert aber mit jeder EBICS-fähigen Bank (Volksbank, Sparkasse, …).

---

## Highlights

- **Setup-Wizard** „Bank verbinden" (Banking → Bank verbinden) — in 5 Minuten
  eingerichtet, keine EBICS-Kenntnisse nötig.
- **EBICS 2.4 / 2.5 / 3.0** über die ausgetauschte `ebics-python` Bibliothek.
- **CAMT.053** (und optional **CAMT.054**) Import mit Duplikat-Erkennung.
- **Automatische Zahlungszuordnung** (Rechnungsnummer → Kunden-/Lieferanten-ID →
  Verwendungszweck → Betrag) mit automatischer `Payment Entry`-Erstellung.
- **Monitoring**: offene Rechnungen und fehlende Abo-Zahlungen werden
  automatisch als ToDo + E-Mail gemeldet.
- **Dashboard** „Bank Automation" mit Status, letzter Synchronisation,
  neuen Umsätzen, nicht zugeordneten Zahlungen und Fehlern.
- **Sicherheit**: Passwörter als Frappe `Password`-Felder, rollenbasierte
  Berechtigung (Bank Administrator / Buchhalter / Mitarbeiter), EBICS-Schlüssel
  verschlüsselt im `private/files`-Verzeichnis der Site.
- **API**: `POST /api/method/ebics_bank_connector.sync_now`,
  `GET /api/method/ebics_bank_connector.status`.

---

## Schnellstart

```bash
# 1. App holen und installieren
bench get-app https://github.com/example/ebics_bank_connector
bench --site site1.local install-app ebics_bank_connector

# 2. EBICS-Backend-Bibliothek installieren
bench --site site1.local pip install ebics-python lxml

# 3. Im ERPNext: Banking → Bank verbinden
```

Detaillierte Anleitung: [`docs/installation.md`](docs/installation.md) und
[`docs/user_manual.md`](docs/user_manual.md).

---

## Architektur

```
ebics_bank_connector/
├── ebics_bank_connector/
│   ├── hooks.py
│   ├── install.py
│   ├── api.py              # öffentliche API-Endpunkte
│   ├── sync.py             # Synchronisations-Engine + Scheduler
│   ├── matching.py         # Matching-Engine
│   ├── monitoring.py       # Zahlungsüberwachung
│   ├── notifications.py    # E-Mail + ToDo Benachrichtigungen
│   ├── erpnext_integration.py
│   ├── ebics/
│   │   ├── connection.py   # austauschbare Backend-Factory
│   │   ├── client.py        # High-Level EBICS-Client
│   │   ├── parser.py        # ISO 20022 XML-Helfer
│   │   ├── camt_parser.py   # CAMT.053/054 Parser
│   │   └── backends/
│   │       ├── ebics_python.py   # Default-Backend
│   │       └── stub.py          # Test-Backend
│   ├── doctype/
│   │   ├── ebics_settings/
│   │   ├── ebics_bank_account/
│   │   ├── ebics_sync_log/
│   │   ├── bank_automation_settings/
│   │   └── payment_matching_task/
│   ├── page/banking_setup_wizard/
│   └── workspace/bank_automation.json
└── docs/
```

### EBICS-Backend ist austauschbar

Das Standard-Backend nutzt [`ebics-python`](https://pypi.org/project/ebics-python/).
Ein eigenes Backend lässt sich über `site_config.json` einbinden:

```json
{ "ebics_backend": "myapp.my_ebics_backend" }
```

Das Backend-Modul muss eine `create(**kwargs)`-Factory mit den Methoden
`ping`, `send_ini`, `send_hia`, `fetch_bank_keys`, `download`, `list_accounts`
bereitstellen. Siehe `ebics_bank_connector/ebics/backends/ebics_python.py`.

---

## Rollen

| Rolle | Rechte |
|---|---|
| **Bank Administrator** | Verbindungen anlegen/ändern, Schlüssel initialisieren, Einstellungen |
| **Bank Buchhalter** | Umsätze sehen, abstimmen, Matching Tasks bearbeiten |
| **Bank Mitarbeiter** | Umsätze/Tasks nur lesen |

---

## Lizenz

MIT
