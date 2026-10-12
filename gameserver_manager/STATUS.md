# Projektstand und nächste Schritte

Stand: 2026-10-12. Dieses Dokument fasst zusammen, was bisher gebaut wurde, was getestet ist, was noch
fehlt und wie du am Computer weitermachst.

## Ziel

Ein Servermanager für **Minecraft-Server mit Mods**, bedienbar über eine **Webseite**, der später auch
**weitere Spiele** verwalten kann. Anforderungen aus dem Gespräch:

1. Server in beliebiger (auch älterer) Minecraft-Version und mit Mods (nicht nur Vanilla).
2. Mods einfach auf den Server bringen, auch vorhandene Modpacks.
3. Java-Versionen über Container (Docker) bereitstellen, weil nicht jede Java-Version auf jeder
   Distribution läuft.
4. Server und Welten regelmäßig sichern.
5. Webinterface mit **Anmeldung und Benutzerverwaltung** und modernem Aussehen.
6. Von außen über den Browser erreichbar, installierbar auf einem eigenen Server.
7. Später erweiterbar auf andere Spiele.

## Was bisher gemacht wurde

Alles liegt im Repository `jackmcnill/python_scripts` auf dem Branch **`minecraft-servermanager`** (noch nicht
nach `main` gemergt, kein Pull Request).

| Teil | Ort | Stand |
|---|---|---|
| Einfacher CLI-Servermanager (erste Version) | `minecraft_servermanager.py` im Repo-Hauptordner | fertig, wird vom neuen Manager nicht mehr gebraucht, kann gelöscht werden |
| Web-Servermanager | `gameserver_manager/` | siehe unten |

Funktionen des Web-Managers:

- **Server-Typen:** Vanilla, Paper, Fabric, Forge, NeoForge, jede Minecraft-Version, Java-Version wird aus den
  Mojang-Daten gewählt (8, 17, 21, 25).
- **Container-Runtime:** jeder Server in einem eigenen Docker-Container (`eclipse-temurin:<java>-jre`),
  auch die Forge-/NeoForge-Installer laufen im Container. Fallback ohne Docker: lokales Java (nur für Tests).
- **Mods/Plugins:** Upload (`.jar`, Drag-and-drop), Modrinth-Suche und -Installation mit Abhängigkeiten,
  Aktivieren/Deaktivieren/Löschen.
- **Modpacks:** Import von Modrinth-Modpacks (`.mrpack` als Datei oder per Modrinth-Link/Slug) als neuer Server.
- **Backups:** manuell und per Zeitplan, Aufbewahrung, Umfang (komplett/nur Welten), Welt wird bei laufendem
  Server vorher gespeichert, Download/Wiederherstellung (mit Sicherung vor dem Restore).
- **Benutzer und Rechte:** Rollen Administrator/Benutzer, Rechte pro Server (Ansehen/Bedienen/Verwalten),
  Passwort ändern, Sperren, Sitzungen werden ungültig, Login-Bremse, Origin-Prüfung, Protokoll (`audit.log`).
- **Oberfläche:** neu gestaltet (Dashboard, Terminal-Konsole, Hell/Dunkel, mobil), ohne Build-Schritt.
- **Betrieb:** `deploy/install.sh` (Systemdienst + Caddy-HTTPS), Proxy-Unterstützung, README mit
  Installationsanleitung.
- **Erweiterbarkeit:** Spiele sind Plugins (`gsm/games/base.py`), Runtime und Backups sind spielunabhängig.

## Was getestet ist

- **47 Unit-Tests** (`python -m unittest discover -s tests`, laufen ohne Docker/Internet): Rechte, Benutzer,
  Backups (Prune, Restore, Zeitplan), Modpack-Parser inkl. Schutz vor Pfad-Tricks, Docker-Kommando, Web-API
  inkl. Proxy-Betrieb.
- **Mit echtem Docker getestet** (in der Entwicklungsumgebung): Fabric 1.21.4, Forge 1.20.1 (Java 17,
  Installer im Container), ein Modrinth-Modpack mit Minecraft 26.3 (Java 25), Konsole per WebSocket,
  Backup bei laufendem Server, Restore, Mod-Installation von Modrinth, sauberes Stoppen.
- **Browser getestet** (Playwright): Login, alle Seiten, Dialoge, Konsole, mobile Ansicht, Hell/Dunkel,
  eingeschränkte Benutzer.

## Noch NICHT getestet (bitte auf dem echten Server prüfen)

1. **`deploy/install.sh` auf einem echten Server** (nur Trockenlauf): Systemdienst, Docker-Gruppe,
   Caddy/HTTPS, Zertifikat.
2. **Port-Weiterleitung der Container (`-p PORT:PORT`)**: in der Testumgebung ging nur `--network host`.
   Prüfen: Läuft ein Server, kann ein Spieler von einem anderen Rechner verbinden?
3. **Geplante Backups über echte Zeiträume** (nur Unit-Test des Zeitplans).
4. **Verhalten nach Neustart des Rechners** (Autostart der Server) und bei Neustart des Managers mit
   laufenden Containern.
5. Forge-/NeoForge-Server **sehr alter** Versionen (1.5 bis 1.12) und Server, die Java 8 brauchen.
6. Große Modpacks (Dauer, Speicher, Zeitüberschreitungen bei Downloads).
7. Betrieb hinter nginx statt Caddy.

## Offene Aufgaben

### Wichtig (aus dem ursprünglichen Ziel)

- [ ] **Mods für Spieler automatisch bereitstellen.** Das war die allererste Anforderung: Spieler sollen die
      Mods nicht einzeln suchen müssen. Idee: der Manager bietet pro Server ein **Client-Modpack
      (`.mrpack`) zum Download** an (Link in der Oberfläche) und/oder eine Packwiz-URL, damit der Launcher
      (Prism, Modrinth App) Updates selbst holt. Alternative: AutoModpack-Mod (lädt beim Verbinden nach),
      beachte dessen Lizenzgrenzen für Mods, die nicht frei verteilt werden dürfen.
- [ ] **Branch nach `main` mergen** (Pull Request) und `minecraft_servermanager.py` entfernen.
- [ ] Auf einem echten Server installieren und die Punkte oben prüfen.

### Funktionen

- [ ] Quilt als Server-Typ; CurseForge-Modpacks (braucht API-Key).
- [ ] `server.properties`, Whitelist und Ops in der Oberfläche bearbeiten (Datei-Editor/Formulare).
- [ ] Anzeige von Spielerliste, RAM/CPU-Auslastung, Server-Version-Updates.
- [ ] Absturz-Erkennung mit automatischem Neustart; Benachrichtigung (E-Mail/Discord).
- [ ] Recht „darf Server erstellen“ für normale Benutzer (aktuell nur Admins).
- [ ] CPU-Limit pro Server, Port-Vorschlag (nächster freier Port).
- [ ] Backup-Ziel außerhalb des Servers (S3, SFTP, Netzlaufwerk), Verschlüsselung.
- [ ] Zweifaktor-Anmeldung (TOTP); Protokoll-Rotation (wächst aktuell unbegrenzt).
- [ ] Export/Import einer kompletten Server-Konfiguration; Server klonen.

### Technik

- [ ] **Oberfläche für weitere Spiele verallgemeinern:** Die Dialoge (Server erstellen, Typ-Kacheln, Texte)
      sind noch auf Minecraft festgelegt; sie sollten aus `describe()` des jeweiligen Spiels entstehen.
- [ ] Zweites Spiel als Beweis der Schnittstelle (z. B. Terraria, Valheim oder ein generischer
      Docker-Spieleserver mit frei wählbarem Image).
- [ ] Jobs und Sperren liegen nur im Arbeitsspeicher: nach einem Neustart des Managers sind laufende
      Aufgaben weg. Optional persistieren.
- [ ] Manager selbst als Docker-Image/Compose-Datei anbieten (Achtung: Bind-Mount-Pfade und Docker-Socket).
- [ ] Mehr automatische Tests für Frontend (Playwright-Test im Repo) und Docker-Runtime (Integrationstest).

## Wichtige Entscheidungen und Eigenheiten

- **Nur Python-Standardbibliothek + Starlette/Uvicorn**, Frontend ohne Framework und ohne Build-Schritt.
- **Docker per CLI** (`docker run/exec/logs`), kein Docker-SDK. Konsolenbefehle gehen per
  `docker exec … cat > /proc/1/fd/0` an den Server-Prozess (Container läuft mit `-i --init`).
- **Kein Restart-Policy** der Container (sonst würde ein sauberes `stop` den Server neu starten); stattdessen
  *Automatisch starten* im Manager.
- Container laufen mit der UID des Manager-Benutzers, damit Dateien für Backups/Uploads zugreifbar bleiben.
- Port wird 1:1 gemappt (Host-Port = Server-Port in `server.properties`).
- Backups sind `tar.gz` im Datenordner (`backups/<server>/`), Namen `<server>-<Zeit>-<full|world>.tar.gz`.
- Passwörter: scrypt; Sitzungen: signiertes Cookie mit Benutzername und Versionszähler.
- Ältere Minecraft-Versionen lassen sich über „auch Snapshots / alte Betas“ wählen; ob jede sehr alte Version
  einen Server-Download bei Mojang hat, entscheidet Mojang.
- In der Entwicklungsumgebung brauchte Docker einen Image-Mirror (`mirror.gcr.io`, wegen Docker-Hub-Limit)
  und Proxy-Zertifikate. Das betrifft einen normalen Server nicht.

## Am Computer weitermachen

```bash
git clone -b minecraft-servermanager https://github.com/jackmcnill/python_scripts.git
cd python_scripts/gameserver_manager
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests        # 47 Tests, sollten grün sein
.venv/bin/python -m gsm serve                          # http://127.0.0.1:8080, Admin-Passwort steht im Terminal
```

- **Lokal entwickeln ohne Docker:** `GSM_RUNTIME=local` nutzt das Java des Rechners (Konsole nur für vom
  Manager gestartete Server).
- **Mit Docker entwickeln:** Benutzer in die Gruppe `docker`, dann läuft alles wie auf dem Server.
- **Daten für Experimente** in einen eigenen Ordner legen: `GSM_DATA=/tmp/gsm-test python -m gsm serve`.
- **Mit Claude Code weiterarbeiten:** Repository öffnen und z. B. sagen: „Lies gameserver_manager/STATUS.md und
  setze die Aufgabe *Client-Modpack zum Download anbieten* um.“

### Empfohlene Reihenfolge

1. Auf dem echten Server installieren (README, Variante A) und die „Nicht getestet“-Liste abarbeiten.
2. Client-Modpack-Download für Spieler bauen (Kernwunsch).
3. Branch per Pull Request nach `main` bringen, alten CLI-Manager löschen.
4. Danach nach Bedarf: Datei-/Property-Editor, Absturz-Neustart, weitere Spiele.
