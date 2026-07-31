# Installation

## Prerequisites

- ERPNext 16 (Frappe Framework 16)
- Linux Ubuntu/Debian (tested in Proxmox LXC)
- Python >= 3.10
- An EBICS-capable bank (e.g. VR-Bank NordRhön eG)

## 1. Install the app

```bash
cd ~/frappe-bench

bench get-app https://github.com/SLAYh4ppii/ebics_bank_connector

bench --site site1.local install-app ebics_bank_connector
```

## 2. EBICS backend

The app uses the [`fintech`](https://pypi.org/project/fintech/) library as its
default EBICS backend. It is declared as a dependency in `pyproject.toml` and
installed automatically by `bench install-app`.

> **License note:** The `fintech` library has its own proprietary license
> (free for non-commercial use, paid license for commercial use). This app's
> GPL-3.0 license applies only to the app code, not to the `fintech` library.
> See <https://www.joonis.de/en/fintech/license/> for details.

To swap the backend for a different EBICS library, see
`Bank Automation Settings` in the dashboard (field "EBICS Backend").

## 3. Enable the scheduler

The scheduler runs automatically once `bench schedule` is running (standard
in production). The app registers:

- **hourly**: synchronization of all connections set to "Hourly"
- **daily**: payment monitoring (open invoices, missing subscription payments)
  and CAMT-XML retention cleanup

## 4. Assign roles

System Settings -> User -> Roles:

- **Bank Administrator**: connect banks, manage settings
- **Bank Accountant**: reconcile transactions
- **Bank Employee**: read-only access

## 5. Connect a bank

In ERPNext: **Banking -> Connect bank** (setup wizard).

See `user_manual.md` for the step-by-step guide.

## Uninstallation

```bash
bench --site site1.local uninstall-app ebics_bank_connector
bench remove-app ebics_bank_connector
```

The EBICS keys are stored under
`<site>/private/files/ebics_keys/<connection>/` and are **not** deleted on
uninstall — remove them manually if no longer needed.
