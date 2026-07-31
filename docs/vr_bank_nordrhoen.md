# VR-Bank NordRhön eG — spezifische Hinweise

Die App wurde primär für die **VR-Bank NordRhön eG** entwickelt. Diese Bank
nutzt die Standard-EBICS-Schnittstelle der Genossenschaftsbanken (Fiducia /
Atruvia).

## Bekannte Daten (Beispiele — bitte mit Ihrem EBICS-Blatt abgleichen)

| Feld | Wert |
|---|---|
| Host URL | `https://banking.vr-nordrhoen.de/ebics/ebics.aspx` *(Beispiel)* |
| EBICS Version | 3.0 |
| Auftragsart Kontoauszug | Z53 (CAMT.053) |
| Auftragsart Buchungsdetails | Z54 (optional) |

> Die exakte Host URL entnehmen Sie bitte Ihrem persönlichen
> EBICS-Informationsblatt der VR-Bank NordRhön eG.

## Schritte

1. EBICS-Zugang bei der VR-Bank NordRhön eG beantragen
   (Online-Banking → Firmenkunden → EBICS freischalten).
2. EBICS-Informationsblatt mit Host/Partner/User ID bereithalten.
3. ERPNext → Banking → Bank verbinden → „VR-Bank" wählen.
4. Daten eintragen, „Verbindung testen".
5. Schlüssel in der Bank freischalten lassen (oft im Online-Banking unter
   „EBICS-Verwaltung" → „Schlüssel freigeben").
6. Erneut „Verbindung testen" → Status „Verbunden".
7. Konten auswählen, Fertigstellen.

## Support

Bei Problemen mit der Bank-Schnittstelle selbst wenden Sie sich an die
VR-Bank NordRhön eG. Bei Problemen mit der ERPNext-Integration siehe
`troubleshooting.md`.
