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

## 2. Install the EBICS backend library (optional)

The app installs and runs without an EBICS backend (a stub backend is used
for tests). To communicate with a real bank, install an EBICS library of
your choice:

```bash
# Option A: fintech (proprietary, free for non-commercial, paid for commercial)
bench --site site1.local pip install fintech lxml

# Option B: ebicsclient (PolyForm Noncommercial, paid for commercial)
bench --site site1.local pip install ebicsclient lxml

# Option C: any other EBICS library you have a license for
```

> The EBICS backend is **not** declared as a dependency in `pyproject.toml`
> because every available pure-Python EBICS library is either proprietary or
> license-restricted. You choose and install the backend yourself — the app's
> backend adapter handles the rest. See `Bank Automation Settings` in the
> dashboard to configure which backend module to use.

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
