# Benutzerhandbuch

## Bank in 5 Minuten verbinden

1. Menü **Banking → Bank verbinden** öffnen.
2. **Schritt 1 – Bank auswählen**: Bank (VR-Bank / Volksbank / Sparkasse /
   Andere) und optional eine bestehende ERPNext-Bank wählen.
3. **Schritt 2 – EBICS Daten**: Die Zugangsdaten aus dem EBICS-Informationsblatt
   der Bank eintragen (Host URL, Host ID, Partner ID, User ID, Customer ID,
   EBICS Version). Eine Passphrase für die lokalen Schlüssel vergeben.
4. **Schritt 3 – Verbindung testen**: Auf „Verbindung testen" klicken.
   - ✅ Erfolg: Schlüssel werden initialisiert (INI/HIA/HPB).
   - ❌ Fehler: Verständliche Meldung, z.B. „User ID bei Bank nicht bekannt".
5. **Schritt 4 – Konten auswählen**: Erkannte Konten anhaken oder IBAN manuell
   eingeben. ERPNext-Bank-Account zuordnen. Auf „Fertigstellen" klicken.

Fertig. Die Synchronisation läuft automatisch.

## Wo sehe ich die Umsätze?

- **Bank Automation** Workspace: Status & Kennzahlen.
- **Banking → Bank Transaction**: Alle importierten Umsätze (Status
  „Pending" = noch nicht zugeordnet, „Reconciled" = zugeordnet).
- **Banking → EBICS Sync Log**: Protokoll jeder Synchronisation inkl.
  importierter/duplikat/zugeordneter Anzahlen und Original-XML.

## Zahlungszuordnung

Die App versucht automatisch, jede eingehende Zahlung einer offenen Rechnung
zuzuordnen (Priorität: Rechnungsnummer → Kunden-ID → Lieferanten-ID →
Verwendungszweck → Betrag). Bei Treffer wird eine **Payment Entry** erstellt
und die Bank Transaction auf „Reconciled" gesetzt.

Konnte nicht zugeordnet werden, entsteht ein **Payment Matching Task**
(„Zahlung prüfen") unter Banking → Zahlungen prüfen. Dort kann der Buchhalter
die Zahlung manuell einer Rechnung zuordnen oder ignorieren.

## Manuell synchronisieren

- EBICS Settings → „Jetzt synchronisieren", oder
- `POST /api/method/ebics_bank_connector.sync_now` (Body: `{"settings":"<Name>"}`)

## Einstellungen

**Banking → Bank Automation Settings**:

- Synchronisations-Intervall (Stündlich / Täglich)
- Automatische Zuordnung an/aus
- Payment Entry automatisch erstellen
- Matching-Prioritäten (Rechnungsnummer, Kunden-ID, …)
- Betrag-Toleranz in %
- Warn-Schwellen: offene Rechnung ab N Tagen, Abo fehlt ab N Tagen
- Admin-Benutzer & Benachrichtigungs-E-Mail

## Benachrichtigungen

Bei Fehlern, offenen Rechnungen und fehlenden Abo-Zahlungen werden
automatisch **E-Mails** und **ToDos** erzeugt (Empfänger = konfigurierter
Admin-Benutzer).
