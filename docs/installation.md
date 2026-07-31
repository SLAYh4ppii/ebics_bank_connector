# Installation

## Voraussetzungen

- ERPNext 16 (Frappe Framework 16)
- Linux Ubuntu/Debian (getestet in Proxmox LXC)
- Python ≥ 3.10
- Eine EBICS-fähige Bank (z.B. VR-Bank NordRhön eG)

## 1. App installieren

```bash
cd ~/frappe-bench

bench get-app https://github.com/example/ebics_bank_connector

bench --site site1.local install-app ebics_bank_connector
```

## 2. EBICS-Backend-Bibliothek installieren

```bash
bench --site site1.local pip install ebics-python lxml
```

> `ebics-python` ist das Standard-Backend. Es ist als Dependency in der
> `pyproject.toml` deklariert, wird aber bei `bench get-app` nicht automatisch
> installiert — daher der explizite `pip install`.

## 3. Scheduler aktivieren

Der Scheduler läuft automatisch, sobald `bench schedule` läuft (Standard in
Produktion). Die App registriert:

- **stündlich**: Synchronisation aller Verbindungen mit Intervall „Stündlich"
- **täglich**: Zahlungsüberwachung (offene Rechnungen, fehlende Abo-Zahlungen)

## 4. Rollen zuweisen

System Settings → User → Roles:

- **Bank Administrator**: Bank verbinden, Einstellungen
- **Bank Buchhalter**: Umsätze abstimmen
- **Bank Mitarbeiter**: nur Lesezugriff

## 5. Bank verbinden

Im ERPNext: **Banking → Bank verbinden** (Setup-Wizard).

Siehe `user_manual.md` für die Schritt-für-Schritt-Anleitung.

## Deinstallation

```bash
bench --site site1.local uninstall-app ebics_bank_connector
bench remove-app ebics_bank_connector
```

Die EBICS-Schlüssel liegen unter
`<site>/private/files/ebics_keys/<verbindung>/` und werden beim Uninstall
**nicht** gelöscht — ggf. manuell entfernen.
