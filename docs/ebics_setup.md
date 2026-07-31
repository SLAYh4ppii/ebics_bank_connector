# EBICS Einrichtung

Dieses Dokument beschreibt die EBICS-spezifischen Schritte. Für die
Bediener-Perspektive siehe `user_manual.md` („Bank in 5 Minuten verbinden").

## Was ist EBICS?

EBICS (Electronic Banking Internet Communication Standard) ist der in
Deutschland verbreitete Standard für die sichere Kommunikation zwischen
Unternehmen und Banken. Die App nutzt EBICS, um Kontoauszüge (CAMT.053)
herunterzuladen.

## Voraussetzungen seitens der Bank

1. EBICS-Zugang bei der Bank beantragen (z.B. VR-Bank NordRhön eG).
2. Sie erhalten ein **EBICS-Informationsblatt** mit:
   - Host URL
   - Host ID
   - Partner ID
   - User ID
   - Customer ID (Kunden-Nr.)
   - EBICS Version (meist 3.0)
3. Die Bank muss die Auftragsarten **Z53** (CAMT.053) freischalten.
   Optional **Z54** (CAMT.054).

## Schlüssel-Initialisierung (automatisch)

Der Setup-Wizard führt automatisch den EBICS-Schlüsselaustausch durch:

1. **INI** — Upload der Signatur-Schlüssel (A006)
2. **HIA** — Upload der Verschlüsselungs- (E002) und Authentifizierungs-
   Schlüssel (X002)
3. **HPB** — Download der öffentlichen Bankschlüssel

> Nach INI/HIA muss die Bank die Schlüssel **freischalten** (oft manuell im
> Online-Banking oder per Formular). Erst danach ist HPB erfolgreich und der
> Status wechselt auf „Verbunden".

## Manuelle Schlüssel-Initialisierung

EBICS Settings → „EBICS Schlüssel initialisieren" (wenn der Wizard-Schritt 3
übersprungen wurde).

## EBICS Versionen

| Version | Empfehlung |
|---|---|
| 2.4 | ältere Banken |
| 2.5 | Übergangsversion |
| 3.0 | **Empfohlen** (aktuell, VR-Bank NordRhön) |

## Auftragsarten

| Code | Bedeutung | Standard |
|---|---|---|
| Z53 | CAMT.053 – Kontoauszug | ja |
| Z54 | CAMT.054 – Buchungsdetails | optional |
| HTD | Kontoumsätze / Kontoübersicht | Entdeckung |
| HPB | Bankschlüssel | Schlüsseltausch |

## Backend austauschen

Standard ist `fintech`. Ein anderes Backend lässt sich in den
**Bank Automation Settings** (Dashboard) im Feld „EBICS Backend" eintragen
(Modul-Pfad, z.B. `myapp.my_backend`).

> Früher erfolgte die Konfiguration über `site_config.json` mit dem Schlüssel
> `ebics_backend`. Das wird weiterhin als Fallback unterstützt, das Dashboard
> hat jedoch Vorrang.

Siehe `README.md` → „EBICS-Backend ist austauschbar".

---

## Go-Live-Checkliste (vor erstem Produktivbetrieb)

Der gesamte EBICS-Pfad wurde während der Entwicklung nur mit dem Stub-Backend
getestet. Vor dem Produktivgang **muss** eine echte Bank-Verbindung
durchgespielt werden:

- [ ] `fintech` Bibliothek installiert (`bench pip install fintech`)
- [ ] EBICS-Zugang bei der Bank beantragt, Informationsblatt liegt vor
- [ ] Verbindung im Setup-Wizard angelegt (Host/Partner/User/Customer ID)
- [ ] Schlüssel-Passphrase ≥ 16 Zeichen vergeben
- [ ] **INI** gesendet → Bank hat Schlüssel freigeschaltet
- [ ] **HIA** gesendet
- [ ] **HPB** empfangen → Status „Verbunden"
- [ ] `test_connection` API erfolgreich
- [ ] Erster CAMT.053-Download (Z53) erfolgreich
- [ ] Bank Transactions in ERPNext sichtbar
- [ ] Dedup-Prüfung: zweiter Sync importiert keine Duplikate
- [ ] Optional: CAMT.054 (Z54) Download getestet
- [ ] Scheduler läuft (stündlich), Sync-Log-Einträge entstehen
- [ ] Fehlerfall simuliert (falsche Host URL) → Fehlerzähler steigt,
      nach 3 Fehlern → „Deaktiviert"
- [ ] Erfolgreicher Sync nach Fehler → Zähler reset, Status „Verbunden"
- [ ] Bank-Public-Keys (HPB) auf Plausibilität geprüft (Fingerprint notiert)
- [ ] Backup der `private/files/ebics_keys/` Verzeichnisse erstellt
