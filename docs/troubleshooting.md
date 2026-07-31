# Fehlerbehebung

## Verbindungstest schlägt fehl

| Meldung | Ursache / Lösung |
|---|---|
| „Verbindung zur Bank konnte nicht hergestellt werden" | Host URL prüfen, Netzwerk/Firewall, Bank online? |
| „Der Benutzer ist bei der Bank nicht bekannt" | User ID / Partner ID falsch, oder Schlüssel noch nicht freigeschaltet |
| „Authentifizierung fehlgeschlagen" | Schlüssel bei Bank freischalten lassen, dann erneut testen |
| „Die Bibliothek 'fintech' ist nicht installiert" | `bench --site site1.local pip install fintech lxml` |

## Schlüssel lassen sich nicht initialisieren

- INI/HIA gesendet, aber HPB schlägt fehl → Bank muss Schlüssel **freischalten**
  (Online-Banking → EBICS-Verwaltung). Warten, dann erneut „Verbindung testen".
- Status bleibt „Entwurf" → EBICS Settings öffnen, „EBICS Schlüssel
  initialisieren" manuell auslösen.

## Keine Umsätze / leere Synchronisation

- EBICS Sync Log prüfen: `transactions_imported = 0` und `duplicate = 0`?
  Dann lieferte die Bank in diesem Zeitraum keine Umsätze.
- `from_date`/`to_date` im Sync Log prüfen. Beim ersten Lauf werden 30 Tage
  gezogen; danach nur das Delta (+2 Tage Überlappung).
- Auftragsart Z53 bei der Bank freigeschaltet?

## Duplikate werden nicht erkannt

- Dedup basiert auf `transaction_id` (AcctSvcrRef) + Bank Account. Wenn die
  Bank keine stabilen IDs liefert, kann es zu Doppelimporten kommen. In
  diesem Fall `raw_xml_storage` aktivieren und das XML prüfen.

## Zahlung wird nicht automatisch zugeordnet

- Matching Task („Zahlung prüfen") prüfen — dort steht der Vorschlag.
- Rechnungsnummer im Verwendungszweck? Format `RE-2026-001` wird erkannt.
- Rechnung noch offen (`outstanding_amount > 0`)?
- Betrag-Toleranz in Bank Automation Settings erhöhen, falls Beträge
  abweichen.

## CAMT-XML fehlerhaft

- Bei Parse-Fehlern: `raw_xml_storage` aktivieren, Sync Log öffnen,
  „Original CAMT-XML" herunterladen und prüfen.
- Die App speichert das Original-XML auch bei Fehlern (sofern aktiviert),
  damit der Support analysieren kann.

## Scheduler läuft nicht

- `bench schedule` Prozess prüfen (in Produktion via `bench setup systemd`).
- `bench --site site1.local doctor`.
- EBICS Settings: `sync_enabled = 1` und `status = „Verbunden"`?

## API-Fehler 403

- Rolle fehlt. Endpunkte benötigen Bank Administrator / Bank Buchhalter
  (siehe `security.md`).

## Logs & Diagnose

```bash
# letzte Sync Logs
bench --site site1.local console
>>> frappe.get_all("EBICS Sync Log", fields=["*"], order_by="started_on desc", limit=5)

# Fehler-Log
>>> frappe.get_all("Error Log", filters={"method":["like","%ebics%"]}, limit=5)
```
