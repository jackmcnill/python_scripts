# Strompreis-Prognose – Übergabe an die lokale Session

Stand: 19.10.2026. Ziel: Aus dem Verlauf des dynamischen Stromtarifs (Tibber) in
Home Assistant abschätzen, wie die Preise in Zukunft aussehen könnten und ob der
aktuelle Preis günstig oder teuer ist.

## Quelle in Home Assistant

- Preis-Sensor (Tibber): `sensor.electricity_price_wilhelm_busch_strasse_17`, Einheit EUR/kWh
- Verlauf reicht bis August 2023 zurück (Langzeit-Statistik, `source="statistics"`)
- Weitere Sensoren: `sensor.tibber_price_level_deutsch` (Tibber-Level, zuletzt „günstig"),
  `sensor.energyzero_today_energy_*` (Day-Ahead-Marktpreise inkl. „all_in"),
  `sensor.epex_spot_data_*`
- `ha_get_history` liefert pro Aufruf höchstens 1000 Zeilen (≈ 41 Tage stündlich,
  ≈ 2,7 Jahre täglich). Für längere Zeiträume in Blöcken abfragen, mit
  `start_time` und `end_time`. Das Feld `fields` nicht auf `time_range` beschränken,
  sonst kommen keine Daten zurück.

## Daten in `daten/` (aus den Statistiken exportiert, Zeitzone Europe/Berlin)

| Datei | Inhalt |
|---|---|
| `tage_2023_08_bis_2026_05.csv` | Tageswerte mean/min/max, 12.08.2023 bis 27.05.2026 |
| `stunden_2025_10_bis_12.csv` | Stundenmittel 01.10. bis 21.12.2025 |
| `stunden_2026_07_bis_10.csv` | Stundenmittel 20.07. bis 17.10.2026 (Lücke: 30.08. bis 07.09.) |

Lücke bei den Tageswerten: 28.05. bis 19.07.2026 fehlt (Abrufgrenze 1000 Zeilen).
Für Juni/Juli 2026 hier ggf. nachladen.

## Ergebnisse

Monatsmittel (€/kWh):

| Monat | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| Okt | 0,27 | 0,31 | 0,32 | ca. 0,40 (bisher) |
| Nov | 0,28 | 0,34 | 0,34 | – |
| Dez | 0,25 | 0,33 | 0,33 | – |
| Jan | 0,29 | 0,35 | 0,35 | – |
| Feb | 0,27 | 0,37 | 0,33 | – |

- Seit September 2026 liegt der Preis im Schnitt bei ca. 0,40 €/kWh, etwa 25 %
  über dem Vorjahr. Ursache (Markt, Tarif, Netzentgelte/Abgaben) ist aus den Daten
  nicht ersichtlich und sollte geprüft werden.
- Die Tagesschwankung ist größer geworden: Werktags 0,31 bis 0,55 (Okt 2025: 0,29 bis 0,42).
- Saisonal: Okt → Nov +2 % (2023), +11 % (2024), +6 % (2025). Dezember ≈ November.
  Januar/Februar meist am teuersten.
- Letzte 28 Tage: Mittel 0,399, unteres Viertel (günstig) < 0,352, oberes Viertel (teuer) > 0,451.
- Tagesprofil Werktag: Nacht ≈ 0,39; Morgenspitze 06 bis 09 Uhr 0,45 bis 0,49;
  Mittagstal 11 bis 16 Uhr 0,31 bis 0,36; Abendspitze 18 bis 20 Uhr 0,51 bis 0,55.
  Wochenende: Mittagstal 0,25 bis 0,28, Abendspitze 0,44 bis 0,46.
- Im Nov/Dez 2025 war das Mittagstal flacher (≈ 0,34), Nachtstunden blieben am günstigsten.

Einordnung des Preises am 18.10.2026, 00:30 Uhr: 0,387 €/kWh. Gegenüber den letzten
4 Wochen leicht günstig, gegenüber dem Vorjahr hoch. Als Schwelle daher den
gleitenden 28-Tage-Schnitt verwenden, nicht die Vorjahre.

Prognose (reines Muster aus der Vergangenheit, ohne Wetter/Wind/Gaspreis):
- Nov 2026: ca. 0,42 bis 0,45 €/kWh im Mittel
- Dez 2026 bis Feb 2027: ca. 0,42 bis 0,47 €/kWh

## Offene nächste Schritte (nicht umgesetzt)

1. Template-Sensoren in Home Assistant: „günstig/mittel/teuer" relativ zum
   28-Tage-Schnitt (z. B. mit `statistics`-Sensor) und die günstigsten Stunden
   der nächsten 24 h aus den EnergyZero-/Tibber-Day-Ahead-Daten.
2. Ggf. Dashboard-Karte oder Automation (Wallbox, Waschmaschine).
   Vorher den Skill `home-assistant-best-practices` (MCP-Resource
   `skill://home-assistant-best-practices/SKILL.md`) lesen.
3. Ursache des Preisanstiegs gegenüber 2025 klären.

## Auswertung erneut ausführen

```
python3 strompreis_prognose/analyse.py
```

Es wurde nichts in Home Assistant verändert.
