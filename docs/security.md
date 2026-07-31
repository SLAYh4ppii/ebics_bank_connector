# Sicherheit

## Zugangsdaten

- **Keine Zugangsdaten im Klartext.** Die EBICS-Schlüssel-Passphrase wird als
  Frappe `Password`-Feld gespeichert (verschlüsselt in der Datenbank,
  entschlüsselt nur on-demand im Arbeitsspeicher).
- Host/Partner/User/Customer IDs sind nicht sensibel im Sinne von
  Authentifizierungsgeheimnissen, werden aber dennoch nur berechtigten Rollen
  angezeigt.

## EBICS-Schlüssel

- Die lokalen EBICS-Schlüssel (A006/E002/X002) liegen als PEM-Datei unter
  `<site>/private/files/ebics_keys/<verbindung>/keys.pem`.
- Das Verzeichnis `private/files` ist über den Webserver **nicht** öffentlich
  erreichbar.
- Die Schlüsseldatei ist mit der vergebenen Passphrase verschlüsselt.

## Rollen & Berechtigungen

| Rolle | EBICS Settings | EBICS Konto | Sync Log | Matching Task | Automation Settings |
|---|---|---|---|---|---|
| Bank Administrator | CRUD | CRUD | R | CRUD | CRUD |
| Bank Buchhalter | R | R/W | R | R/W | R |
| Bank Mitarbeiter | R | R | R | R | R |

- Alle API-Endpunkte prüfen die Rolle via `ebics_bank_connector.utils.require_role`.
- `System Manager` hat immer Vollzugriff.

## Logging

- Fehler werden in `Error Log` (Frappe) geschrieben.
- Jede Synchronisation erzeugt einen `EBICS Sync Log`-Eintrag.
- Optional wird das **Original-CAMT-XML** als private Datei gespeichert
  (Einstellung „Original-CAMT-XML speichern"). Enthält keine
  Authentifizierungsdaten, aber Transaktionsdaten — ggf. DSGVO-konform
  aufbewahren/löschen.

## Empfehlungen

- EBICS-Schlüssel-Passphrase stark wählen (≥ 16 Zeichen).
- `private/files`-Verzeichnis regelmäßig sichern (Backup) — ohne Schlüssel
  ist keine EBICS-Verbindung möglich.
- Produktions-Site über HTTPS betreiben.
- Admin-Benutzer für Benachrichtigungen dediziert einrichten.
