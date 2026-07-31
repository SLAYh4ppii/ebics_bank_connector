# EBICS Bank Connector

A self-hosted banking extension for **ERPNext 16** that monitors bank accounts
via **EBICS**, imports transactions (CAMT.053), and automatically matches
payments to invoices.

> Connect bank → synchronize → auto-reconcile.

An alternative to GoCardless Banking, but built on **EBICS** with full
ERPNext 16 integration. Developed and tested with **VR-Bank NordRhön eG**,
works with any EBICS-capable bank (Volksbank, Sparkasse, …).

---

## Highlights

- **Setup wizard** "Connect bank" (Banking → Connect bank) — up and running
  in 5 minutes, no EBICS knowledge required.
- **EBICS 2.4 / 2.5 / 3.0** via the `fintech` library.
- **CAMT.053** (and optionally **CAMT.054**) import with duplicate detection.
- **Automatic payment matching** (invoice number → customer/supplier ID →
  remittance info → amount) with automatic `Payment Entry` creation.
- **Monitoring**: open invoices and missing subscription payments are
  reported automatically as ToDos + emails.
- **Dashboard** "Bank Automation" with status, last sync, new transactions,
  unmatched payments, and errors.
- **Security**: passwords stored as Frappe `Password` fields, role-based
  permissions (Bank Administrator / Accountant / Employee), EBICS keys
  encrypted in the site's `private/files` directory.
- **API**: `POST /api/method/ebics_bank_connector.sync_now`,
  `GET /api/method/ebics_bank_connector.status`.

---

## Quick start

```bash
# 1. Get and install the app
bench get-app https://github.com/SLAYh4ppii/ebics_bank_connector
bench --site site1.local install-app ebics_bank_connector

# 2. Install the EBICS backend library
bench --site site1.local pip install fintech lxml

# 3. In ERPNext: Banking → Connect bank
```

Detailed guides: [`docs/installation.md`](docs/installation.md) and
[`docs/user_manual.md`](docs/user_manual.md).

---

## Architecture

```
ebics_bank_connector/
├── ebics_bank_connector/
│   ├── hooks.py
│   ├── install.py
│   ├── api.py              # public API endpoints
│   ├── sync.py             # sync engine + scheduler
│   ├── matching.py         # matching engine
│   ├── monitoring.py       # payment monitoring
│   ├── notifications.py    # email + ToDo notifications
│   ├── erpnext_integration.py
│   ├── ebics/
│   │   ├── connection.py   # swappable backend factory
│   │   ├── client.py       # high-level EBICS client
│   │   ├── parser.py       # ISO 20022 XML helpers
│   │   ├── camt_parser.py  # CAMT.053/054 parser
│   │   └── backends/
│   │       ├── ebics_python.py   # default backend
│   │       └── stub.py          # test backend
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

### EBICS backend is swappable

The default backend uses [`fintech`](https://pypi.org/project/fintech/).
A custom backend can be configured in **Bank Automation Settings** (Dashboard)
via the "EBICS Backend" field, or as a fallback in `site_config.json`:

```json
{ "ebics_backend": "myapp.my_ebics_backend" }
```

The backend module must expose a `create(**kwargs)` factory with the methods
`ping`, `send_ini`, `send_hia`, `fetch_bank_keys`, `download`, `list_accounts`.
See `ebics_bank_connector/ebics/backends/ebics_python.py`.

---

## Roles

| Role | Permissions |
|---|---|
| **Bank Administrator** | Create/edit connections, initialize keys, settings |
| **Bank Accountant** | View transactions, reconcile, work on matching tasks |
| **Bank Employee** | Read-only access to transactions/tasks |

---

## License

GPL-3.0-or-later — see [`LICENSE`](LICENSE).

This software is free software: you can use, modify, and distribute it under
the terms of the GNU General Public License v3 (or later). The copyright notice
(`Copyright (C) 2026 h4ppii`) must be preserved in all copies. Modified versions
must also be released under the GPL-3.0 with source code. Commercial use within
ERPNext deployments is permitted; closed-source redistribution is not.
