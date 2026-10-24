# Übergabe: Smart-Home-Projekt (Home Assistant), Stand 2026-10-19

Dieser Ordner enthält alles, was aus der Cloud-Session weitergeführt werden soll. Die eigentliche Konfiguration liegt in
Home Assistant selbst; hier sind Kopien (Export, Kartenquellen, Themes, Automation) und die Notizen.
Die Ordner `dashboards/`, `cards/`, `themes/`, `automations/` und `backups/` enthalten die Dateien.

## System

- Home Assistant 2026.10.2 auf HAOS Yellow. Zugriff über ha-mcp (MCP-Server `Home_Assistent`) und das File-Editor-Add-on
  (Slug `core_configurator`, Konfigurationspfad `/homeassistant`, öffentliche Dateien `/homeassistant/www` → `/local/`).
- Von außen über Cloudflare Tunnel erreichbar (Absicherung noch offen).
- Nutzer:in schreibt Deutsch, möchte Antworten in einfachem Deutsch. Geräte: iPhone (Home-Assistant-App), Desktop.
- Wallbox: openWB (Interne openWB), Fahrzeug Cupra Tavascan (Firmenwagen). Wechselrichter Fronius Gen24, Speicher BYD, Tibber (Preis `sensor.electricity_price_wilhelm_busch_strasse_17`), EOS (Akkudoktor) nur Anzeige.
- Klimaanlage (Außengerät mit mehreren Innengeräten, MQTT), tado-Heizkörperthermostate über HomeKit Controller.

## Wichtige Regeln, die die Nutzer:in gesetzt hat

- Bestehende Dashboards **nicht** ändern, sondern neue anlegen. Ausnahme: Dashboard **Mutter** nur auf ausdrückliche Anfrage (einmal geschehen: Energiefluss-Karte durch `custom:energiefluss-karte` ersetzt). Das Original „Design A – Klar" (`design-a-klar`) bleibt unberührt.
- Einliegerwohnung und Anbau gehören nicht ins Haupt-Dashboard.
- Waschmaschine, Trockner, Gefrierschrank dürfen nie ausgeschaltet werden (nur Messung, keine Schalter im Dashboard).
- Demand Control der Klimaanlage gilt für alle Innengeräte gemeinsam (steht auf 30 %). **Wert nicht ändern**, nur die Einstellmöglichkeit ist im Dashboard.
- Vor Löschen und Aufräumen immer fragen.

## Dashboards in Home Assistant

| URL-Pfad | Zweck |
|---|---|
| `design-h-klar` | **Aktuelle Hauptentwicklung** („Design H – Klar (Kopie)"), 10 Ansichten: start, energie, auto, raeume, erdgeschoss, obergeschoss, keller, aussen, klima, sicherheit. Export: `dashboards/design-h-klar.json` |
| `design-a-klar` | Original der Nutzer:in („Glass Island 3.2"), nicht ändern. Backup: `backups/design-a-klar_original_backup.json` |
| `dashboard-mutter` | Dashboard der Mutter, nur Energiefluss-Karte getauscht (Backup der alten Karte: `backups/mutter_energiefluss_card_before_replacement.json`) |
| `design-f-vorbild`, `design-g-modern`, `mein-zuhause`, `energie-manager`, `ev-laden`, `heizkosten-vergleich` | ältere Entwürfe/Dashboards, später gemeinsam aufräumen |

Aufräumen steht noch aus (Designs/Themes/Dateien, die nicht mehr gebraucht werden), nur nach Rückfrage.

### Design H: wichtige Entscheidungen

- Hintergrund-Bilder in `/homeassistant/www/glass_island_v3/` (`background_desktop.jpg`, `background_mobile.jpg`, Raumfotos). Handy-Bild ist 9:16 (864×1536); iPhone 17 Pro Max (Modell `iPhone18,2`) ist schmaler, daher scharfes Bild „contain" + unscharfe Füllung (`cards/background-fixed.js`).
- Theme `GI Transparenz` (`themes/gi_transparenz.yaml`): `gi-k` = Transparenz-Regler (aktuell 0,62; kleiner = durchsichtiger). Das Theme hängt nur an den Ansichten (`theme:` je View). Nur `lovelace-background: transparent`, das Bild kommt vom Script.
- **Wichtig:** View-Themes werden von Home Assistant nur auf das View-Element angewendet, nicht auf `<html>`. Das Hintergrund-Script erkennt das Dashboard deshalb am Pfad (`/design-h-klar`), nicht am Theme.
- Alle Karten teilen: Füllung 50 % → 28 % × `gi-k`, Weichzeichner 24 px, Rand `rgba(240,247,255,.44)`, innerer Nebel 0,38 (Schnellzugriff: `variables.fog`).
- Navigation unten (`footer` je View, `custom:mod-card`): Start, Energie, E-Auto, Räume, Sicherheit, ganz unten (4 px + 35 % Safe-Area).
- Karten-Typ `button-card` mit Vorlagen (`button_card_templates`: glass, hero, heading, status, lock_status, quick, picture_room, metric, nav).
- Heizkörper/Klima: Tile-Karten mit `climate-hvac-modes` (Icons) + `target-temperature`; Räume mit Heizung und Klima als Wisch-Karte (`custom:swipe-card`, ohne Punkte), halbe Breite.
- Klima-Ansicht: Heizkörper-Übersicht (Tabelle), Außengerät-Bereich (Demand-Control-Auswahl `select.wohnzimmer_demand_control`, `sensor.ac_aussen_power`).

### Eigene Karten (als Dashboard-Ressourcen, Typ module)

| Datei | Karte | Ressourcen-ID |
|---|---|---|
| `cards/energiefluss-glas.js` | `custom:energiefluss-glas` (eigene Energiefluss-Karte, Kreise + Linien + Zusammenfassung) | d5792a6266d44d6eb93b9a9a88c12d9f |
| `cards/ladeprotokoll-export.js` | `custom:ladeprotokoll-export` (Zeitraum wählen, CSV teilen/kopieren) | fcb8d4d3bd9d4126826c9fb739eba873 |
| `cards/background-fixed.js` | kein Kartentyp, fester Hintergrund für `/design-h-klar` | f27349a60b0d475fbdce7c417b98ea97 |
| `cards/energiefluss-karte.js` | `custom:energiefluss-karte` (zentral, nutzt `power-flow-card-plus`, im Dashboard Mutter) | 980cca2d0e2b47e5a80daca39f54e35b |

Zusätzlich hat die Nutzer:in per HACS `xPower-Flow-Card` und `energy-distribution-ext` installiert (Alternativen zur Energiefluss-Karte, noch nicht genutzt).

Hinweis: Die Dateien sind inline registrierte Ressourcen. **Browser/App cachen sie stark.** Wer eine Karte ändert, legt die
Ressource mit neuer ID an und löscht die alte (so entsteht eine neue URL). In der Companion-App hilft sonst „Frontend-Cache zurücksetzen".

## E-Auto: Ladeprotokoll (Firmenwagen) – neu

- Automation `automation.ev_ladeprotokoll_firmenwagen` (`automations/ev_ladeprotokoll.yaml`), läuft immer, unabhängig von der Lade-Steuerung.
- Vorgang beginnt bei Ladeleistung > `input_number.ev_ladeprotokoll_schwelle_ladeleistung` (100 W), endet nach `input_number.ev_ladeprotokoll_pause_bis_ende` (30 min) ohne Ladung oder beim Abstecken.
- Kosten = Σ (Zähler-Differenz kWh × Tibber-Preis) mit Netz und PV gleich bewertet (so entschieden).
- Beim Ende ein Kalender-Eintrag in `calendar.ladeprotokoll_firmenwagen` (Local Calendar). Beschreibung: `kWh=…;Kosten=…;Preis=…;ZaehlerStart=…;ZaehlerEnde=…;Fahrzeug=Tavascan;Modus=…`.
- Helfer: `input_boolean.ev_ladeprotokoll_vorgang_aktiv`, `input_datetime.ev_ladeprotokoll_start`, `…_letzte_ladung`, `input_number.ev_ladeprotokoll_zahlerstand_start`, `…_kosten`, `…_schwelle_ladeleistung`, `…_pause_bis_ende`.
- CSV: Karte in der Ansicht E-Auto (Semikolon, Dezimalkomma, UTF-8 mit BOM); Abruf nur mit Login (liest den Kalender über die authentifizierte API). Download am iPhone über das Teilen-Menü, sonst „CSV kopieren".
- **Noch nicht** mit einer echten Ladung getestet. Der Ablauf wurde mit einem künstlichen Vorgang geprüft und das Testereignis wieder gelöscht.
- Offene Fragen: Kennzeichen/Name im CSV? Frühere Ladungen manuell nachtragen? Eichrechtskonformer Zähler nötig (Arbeitgeber/Steuerberater klären)?

Die EV-Lade-Steuerung (`automation.ev_laden_steuerung_openwb`) ist seit dem 2026-10-22 **aktiv** und wurde gemeinsam getestet (siehe unten).

## EV-Lade-Steuerung und Speicher-Netzladen (Stand 2026-10-22)

### Was passiert ist (Befunde)

- Die openWB schaltete am 2026-10-19 um 16:48, elf Sekunden nach dem Abstecken, **von selbst auf „Instant Charging"**. In der openWB steht „Standard nach Abstecken" im Standard-Lade-Profil auf Nein; die Ursache ist offen. Das Dashboard-„Aus" (`input_select.ev_lademodus`) wirkt nur über die Lade-Steuerung, deshalb lud das Auto sofort.
- Absicherung: `automation.ev_sofortladen_sperre_openwb` (`automations/ev_sofortladen_sperre.yaml`). Bei Dashboard-Modus „Aus" setzt sie jeden openWB-Lademodus außer Stop/Standby sofort auf Stop zurück und schickt eine Meldung (`notify.mobile_app_weisstdudochnicht1`).
- Beim Laden aus dem Netz entlud die Batterie das Auto mit. Grund: Die Lade-Steuerung war abgeschaltet.
- **Cloudflare cacht 404-Antworten für `/local/`** (Bilder wurden vor dem Hochladen einmal über die Domain angefragt). Cache wurde geleert. Empfohlen, noch nicht angelegt: Cache-Regel `starts_with(uri.path, "/local/")` → Bypass cache.

### EV-Lade-Steuerung (`automation.ev_laden_steuerung_openwb`)

- Netzladen (Modus „Sofort", oder „Günstig" bei Preis unter `input_number.ev_max_strompreis`): openWB auf Instant, 16 A, und die Entladung des Speichers wird per Modbus auf **Hausverbrauch ohne Wallbox + 100 W** begrenzt (Register 40348 = 2, 40355 = Wert in 0,01 %).
- **Geändert am 2026-10-22:** `house_w` kommt jetzt aus `sensor.openwb_controller_hausverbrauch`. Vorher `sensor.solarnet_leistung_verbrauch − Wallbox`; der Sensor sprang kurz auf 16 kW, die Entladegrenze stieg auf 34 %, die Batterie gab etwa 20 s lang 5,4 kW ab.
- **Neu:** Absicherungsschritt im `default`-Zweig: Modus „Günstig", Preis nicht unter Limit, openWB auf Instant → Stop. `trace: stored_traces: 50`.
- **Offen:** Bei Preisanstieg (12:00, 12:30, 13:45) ging der Merker `ev_netzladen_aktiv` aus und die Fronius-Register wurden zurückgesetzt, aber die openWB blieb auf Instant. Beim Moduswechsel um 12:14 kam Stop an. Ursache unbekannt; mit den 50 Traces beim nächsten Preisanstieg ansehen.
- Wichtig: Die HA-Entitäten `number.ziebertz_wesseling_grenzwert_fur_die_entladeleistung_der_batterie` und `switch.ziebertz_wesseling_begrenzung_der_entladeleistung_der_batterie` schreiben **dieselben Modbus-Register**. Wer sie von Hand setzt, wird von der Automation innerhalb von 15 s überschrieben.

### Speicher aus dem Netz laden (neu, `automation.speicher_netzladen_tibber`, Kopie `automations/speicher_netzladen_tibber.yaml`)

- Ergebnis des Tests (2026-10-22, ~14:46): **Zwangsladen aus dem Netz funktioniert.** Mit 3000 W Testleistung lud der Speicher mit 3,0 kW, der Netzbezug stieg auf 2,1 kW (PV 1,7 kW, Haus 0,8 kW). Danach alles zurückgesetzt.
- Modbus (Gen24, Integer-Modell, Block ab 40345; `sensor.reading_battery_settings` liest ihn): StorCtl_Mod **40348 = 3**, OutWRte **40355 = 65536 − Rate** (negativ = Zwangsladen), InWRte **40356 = Rate** mit Rate = Leistung ÷ 15360 W × 10000 (1000 W → 651, 3000 W → 1953). ChaGriSet 40360 steht auf 1. Zurücksetzen: 40348 = 0, 40355 = 10000, 40356 = 10000.
- Helfer: `input_boolean.tibber_speicher_laden` (Hauptschalter, aus), `input_boolean.speicher_netzladen_aktiv` (Merker), `input_number.speicher_max_strompreis_netzladen` (0,28 €), `input_number.speicher_ziel_ladestand_netzladen` (80 %), `input_number.speicher_netzlade_leistung` (1000 W). Die Regler haben einen `initial`-Wert und springen nach einem HA-Neustart darauf zurück.
- Regeln: Laden nur bei Schalter an, Preis unter Max-Preis, Ladestand unter Ziel (Neustart erst 5 % darunter), Auto lädt nicht (kein Netz-/PV-Laden, Wallbox < 500 W). Auto hat Vorrang; beim Stoppen werden die Register nicht angefasst, wenn die EV-Steuerung läuft.
- Stand (2026-10-22 ~15:00): Automation **an** (wirkt nur, wenn `tibber_speicher_laden` an ist), Schalter **aus**, Register auf auto/100 %. Eine geänderte `speicher_netzlade_leistung` wird jetzt im Betrieb nachgeführt.
- **Dashboard:** `design-h-klar/energie`, neue Sektion „Speicher aus dem Netz laden" (Schalter, „Lädt gerade", Speicher-Ladestand, Max-Preis, Ziel-Ladestand, Ladeleistung). Export `dashboards/design-h-klar.json` ist aktualisiert. Starten: Schalter „Netzladen Speicher" einschalten; Max-Preis über dem aktuellen Tibber-Preis stellen.
- Bekannte Lücken: (1) Keine Hysterese beim Preis; (2) Ziel-SoC wird nur von der Automation überwacht, nicht im Fronius (MinRsvPct 40350 bleibt unverändert).
- **Fehlende Entitäten:** In der Ansicht Energie („EOS-Plan (nur Anzeige)") existieren `sensor.eos_genetic_ac_charge_factor`, `sensor.eos_genetic_discharge_allowed_factor`, `sensor.eos_grid_consumption_energy_wh` und `sensor.eos_costs_amt` in Home Assistant nicht mehr. Die EOS-App (`ec9bffb2_eos`) läuft; eine EOS-Integration ist nicht eingerichtet (nur `sensor.eos_batterie_soc_faktor` als Template-Helfer). Die vier Kacheln wurden am 2026-10-22 aus `design-h-klar/energie` entfernt. Dieselben vier Kacheln wurden auch aus der Ansicht E-Auto (`design-h-klar/auto`) entfernt, samt der dann leeren Sektion „EOS-Plan (nur Anzeige)". Die Sektionsüberschrift „EOS-Plan (nur Anzeige)" in der Energie-Ansicht gehört jetzt nur noch zu den vier Kurzwerten Netz, PV, Speicher und Strompreis.
- Quellen für die Registerwerte: libe.net „Fronius and BYD battery control via Modbus", simon42-Forum „Fronius netzladung". Beide gelten für ähnliche Geräte; auf diesem System jetzt bestätigt.

## tado Heizkörper (HomeKit)

Zuordnung aus der tado-App ist in Home Assistant gesetzt (Geräte umbenannt, Bereiche gesetzt):
Wohnzimmer VA1519789568 (+ Temperatursensor SU4135593472), Küche VA1620452864, Flur VA1133913600, Schlafzimmer VA3225298176,
Badezimmer VA2833982976, Ankleidezimmer VA2534614272, Gästezimmer VA2148673024, Einliegerwohnung Wohnzimmer VA0111093248,
Einliegerwohnung Küche VA1695753472. Entitäts-IDs: `climate.tado_smart_radiator_thermostat_va<Nummer>`.

## Offene Punkte

1. Hintergrund auf dem iPhone: Bleibt das Bild fest, passt der unscharfe untere Bereich? Rückmeldung fehlt. Ideal wäre ein Handy-Bild im Format des iPhones (z. B. 1320×2868), dann wieder `cover`.
2. Aufräumen: alte Designs/Themes/Dateien (A–G, `zuhause_glas*.yaml`, CSS-Ressource `dfda6344b60a4461adcffe2eb66d916f`, Ordner `www/zuhause`), nur nach Rückfrage; Design H eventuell zum Haupt-Dashboard machen.
3. Kleinere Fragen: Welche Haustür-Lampe bleibt (`light.haustur_2` oder `switch.homee_358_switch_1105`)? Was ist der Tracker `Base` bei `person.marlon`? Foto `studio.jpg` fehlt; `light.schlafzimmer_2/_3` unbekannt.
4. Cloudflare-Tunnel absichern (Cloudflare Access, ip_ban, Bot-Schutz).
5. Speicher-Manager (nur ein Schreiber auf den Fronius, erst Trockenlauf, EOS-Plan als Eingang); EOS-Ladezustand im Plan stimmt nicht (0 statt echter Wert); EOS-PV-Reihe nachführen. Teilstück vorhanden: `speicher_netzladen_tibber` (siehe oben), noch nicht dauerhaft eingeschaltet.
6. Ladeprotokoll mit echter Ladung prüfen. EV-Lade-Steuerung läuft; offen ist, warum Stop bei Preisanstieg nicht ankam (Traces ansehen), und die Ursache für das Umschalten auf Instant nach dem Abstecken.
8. Cloudflare-Cache-Regel für `/local/` (Bypass cache) anlegen.
9. Speicher-Netzladen: Dashboard-Elemente (Schalter, Max-Preis, Ziel, Leistung), Leistungsänderung im laufenden Betrieb übernehmen, Hysterese für den Preis, dann dauerhaft einschalten.
7. Aufräumen im System: alte Tibber-Testansichten, ~185 nicht verfügbare Sensoren, verklemmtes Schloss `lock.home`.

## Technische Hinweise (ha-mcp)

- Schreibende Aufrufe verlangen einen `BestPracticeKey` (Quittung aus `ha_get_skill_guide`, rotiert stündlich) und `MandatoryBPS=false`.
- Dashboard ändern: `ha_config_set_dashboard(url_path=…, config_hash=…, python_transform=…)`. Der Transform-Python ist eingeschränkt (kein `def`, kein `while`, keine Imports; Lambdas sehen keine Variablen von außen).
- Datei-Editor-API (POST) für Dateien: `ha_manage_app(slug="core_configurator", path="/api/save", method="POST", request_headers={"Content-Type":"application/x-www-form-urlencoded"}, body="filename=…&text=…")`, **mit** `python_transform="response = str(response)[:200]"`, sonst schlägt der Aufruf fehl. Nach Theme-Änderung `frontend.reload_themes`.
- Dashboard-Screenshots sind im ha-mcp nicht aktiviert.
- Große Tool-Ergebnisse speichert die Umgebung in Dateien; mit `python3` auslesen.

## Änderungen seit der ersten Übergabe (2026-10-24)

- **Hausverbrauch:** `sensor.solarnet_leistung_verbrauch` ist nur der Netzbezug (0 W bei Einspeisung), **nicht** der Hausverbrauch.
  Neuer Hilfssensor `sensor.hausverbrauch_berechnet` (Template-Helper) = max(0, Netz + PV + Batterie, Batterie positiv = Entladung).
  Eingesetzt in der Energiefluss-Karte (`home: {entity: …}` in der Karten-Konfiguration) und in der Kachel auf der Startseite.
  Der Dashboard-Export in `dashboards/design-h-klar.json` ist aktualisiert.
- **EV-Lade-Steuerung** (`automation.ev_laden_steuerung_openwb`, aktuell **aktiv**, Modus „Günstig" lief gerade): Beim Netzladen wird die Batterie-Entladung nur noch auf den Teil des
  Hausverbrauchs begrenzt, den die PV nicht deckt. Variablen im Skript: `house_w` (openWB-Hausverbrauch `sensor.openwb_controller_hausverbrauch`),
  `pv_w` (`sensor.power_photovoltaics`), `deficit_w = max(house_w - pv_w, 0)`, `out_rate = 0 if deficit_w < 50 else (deficit_w + 100) / wchamax_w * 10000`;
  `needs_write` schreibt auch beim Wechsel von/auf 0. Register: Modbus 40348 (Modus 2 = Entladung begrenzt), 40355 (Entladerate in 0,01 %).
  Gemessen: Batterie von rund 2000 W auf rund 0 W. Beobachten bei Wolken (Hin- und Herschalten), Schwelle 50 W und Reserve 100 W sind einstellbar.
- Die Automation enthält inzwischen auch eine von der Nutzer:in ergänzte Absicherung (Günstig, Preis über Limit, openWB steht auf Instant → Stop).
- Die Datei `automations/ev_ladeprotokoll.yaml` ist weiter aktuell. Die EV-Steuerung selbst liegt nur in Home Assistant (nicht hier exportiert).
