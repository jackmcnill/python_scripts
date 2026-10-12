# Game Server Manager

Spieleserver (zuerst Minecraft) über eine Webseite erstellen und verwalten. Jeder Server läuft in einem
eigenen **Docker-Container**, damit jede Java-Version (8, 17, 21, 25) unabhängig von der Distribution
funktioniert. Backups laufen regelmäßig automatisch.

Projektstand und offene Aufgaben: siehe [STATUS.md](STATUS.md).

## Funktionen

- **Moderne Oberfläche**: Dashboard mit Server-Karten, Terminal-Konsole mit farbigen Log-Ebenen, Befehlsverlauf
  (Pfeiltasten) und Schnellbefehlen, Drag-and-drop für Mods, Hell/Dunkel-Design, Fortschrittsanzeige für
  Hintergrundaufgaben, mobile Ansicht. Alles ohne Build-Schritt und ohne externe Ressourcen.
- **Server anlegen**: Vanilla, Paper, Fabric, Forge, NeoForge, jeweils in beliebiger (auch älterer)
  Minecraft-Version. Die passende Java-Version wird automatisch gewählt.
- **Konsole** im Browser (Live-Log, Befehle senden), Start/Stopp/Neustart, Autostart.
- **Mods/Plugins**: `.jar` hochladen, auf Modrinth suchen und mit Abhängigkeiten installieren,
  deaktivieren oder löschen.
- **Modpacks**: Modrinth-Modpacks (`.mrpack`, per Datei oder Link/Slug) werden als neuer Server eingespielt.
  Loader und Versionen kommen aus dem Pack, Client-only-Mods werden übersprungen.
- **Backups**: manuell und per Zeitplan (alle N Stunden, die letzten N behalten), kompletter Server oder nur
  Welten. Läuft der Server, wird vorher die Welt gespeichert. Download und Wiederherstellung über die
  Oberfläche (vor einer Wiederherstellung wird der aktuelle Stand gesichert).
- **Benutzerverwaltung**: Administratoren und Benutzer mit Rechten pro Server, Protokoll aller Änderungen.

---

## Installation

### Was du brauchst

- Einen **Linux-Server** (Debian oder Ubuntu, empfohlen **Ubuntu 24.04**) mit Root-Zugriff (`sudo`).
  Python muss mindestens Version **3.12** sein (`python3 --version`); Ubuntu 22.04 ist zu alt.
- Genug Arbeitsspeicher für die Minecraft-Server (pro Server 2 bis 8 GB, dazu etwas Reserve) und Festplatte
  für Welten und Backups.
- Für den Zugriff über das Internet eine **Domain**, die auf den Server zeigt (sonst siehe Variante B).

Windows und macOS werden für den Dauerbetrieb nicht unterstützt (das Install-Skript ist für Linux).

### Variante A: Server mit Domain und HTTPS (empfohlen)

1. **Domain vorbereiten:** Lege bei deinem Domain-Anbieter einen DNS-Eintrag (Typ `A`, bei IPv6 `AAAA`) an,
   z. B. `manager.deine-domain.de`, der auf die öffentliche IP deines Servers zeigt. Bei wechselnder IP
   brauchst du DynDNS.
2. **Ports öffnen:** In Firewall und (falls zuhause) Router müssen **80** und **443** zum Server weitergeleitet
   werden. Das braucht Caddy für das HTTPS-Zertifikat und den Zugriff.
3. **Per SSH auf dem Server anmelden** und den Code holen:
   ```bash
   sudo apt update && sudo apt install -y git
   git clone -b minecraft-servermanager https://github.com/jackmcnill/python_scripts.git
   cd python_scripts/gameserver_manager
   ```
   Ist das Repository privat, fragt Git nach Benutzername und Passwort. Als Passwort gibst du einen
   GitHub-Personal-Access-Token ein.
4. **Installieren:**
   ```bash
   sudo ./deploy/install.sh --domain manager.deine-domain.de
   ```
   Das Skript installiert Docker, richtet die Python-Umgebung und den Systemdienst `gsm` ein, setzt Caddy als
   HTTPS-Proxy davor und legt den Administrator an.
   **Am Ende wird das Admin-Passwort einmalig angezeigt. Notiere es dir.**
   (Zum Vorab-Test: `sudo ./deploy/install.sh --dry-run --domain ...` zeigt nur, was passieren würde.)
5. **Anmelden:** Öffne `https://manager.deine-domain.de` im Browser, Benutzer `admin` und das Passwort aus
   Schritt 4. Das Zertifikat holt Caddy beim ersten Aufruf automatisch, das kann einen Moment dauern.
6. **Passwort ändern und Benutzer anlegen:** Oben rechts im Konto-Menü *Passwort ändern*; weitere Benutzer
   unter *Benutzer & Protokoll* (siehe [Benutzer und Rechte](#benutzer-und-rechte)).
7. **Ersten Server erstellen:** *Neuer Server*, Typ und Version wählen, Namen und Port eingeben, die
   Minecraft-EULA akzeptieren. Beim ersten Mal lädt Docker das Java-Image, das dauert etwas.
8. **Minecraft-Ports freigeben:** Jeder Server hat einen eigenen Port (Standard 25565). Gib diese Ports in
   Firewall und Router frei (TCP), z. B. mit `sudo ufw allow 25565/tcp`. Spieler verbinden sich mit
   `deine-domain.de:PORT` (bei 25565 genügt die Domain).

### Variante B: ohne Domain oder ohne offene Ports (VPN/Tunnel)

```bash
git clone -b minecraft-servermanager https://github.com/jackmcnill/python_scripts.git
cd python_scripts/gameserver_manager
sudo ./deploy/install.sh
```

Der Manager läuft dann auf Port **8080 ohne HTTPS**. Gib diesen Port **nicht** ins Internet frei, sondern
erreiche ihn über ein VPN (Tailscale, WireGuard), einen SSH-Tunnel (`ssh -L 8080:localhost:8080 server`) oder
einen Cloudflare Tunnel. Aufruf dann z. B. `http://<VPN-IP>:8080`.

### Variante C: manuell (zum Ausprobieren, z. B. auf dem eigenen PC unter Linux)

```bash
sudo apt install -y git python3 python3-venv docker.io
sudo usermod -aG docker $USER          # danach einmal ab- und wieder anmelden
git clone -b minecraft-servermanager https://github.com/jackmcnill/python_scripts.git
cd python_scripts/gameserver_manager
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m gsm serve          # http://127.0.0.1:8080
```

Beim ersten Start steht das Admin-Passwort im Terminal. Zum Zugriff aus dem Netzwerk `--host 0.0.0.0`
anhängen (unverschlüsselt, nur im vertrauenswürdigen Netz).

### Updates, Betrieb, Deinstallation

| Aufgabe | Befehl |
|---|---|
| Update | `cd python_scripts/gameserver_manager && git pull && sudo systemctl restart gsm` |
| Status | `systemctl status gsm` |
| Logs | `journalctl -u gsm -f` |
| Neustart / Stopp | `sudo systemctl restart gsm` / `sudo systemctl stop gsm` |
| Passwort zurücksetzen | `.venv/bin/python -m gsm passwd admin` |
| Benutzer anlegen (CLI) | `.venv/bin/python -m gsm adduser NAME [--admin]` |
| Deinstallieren | `sudo systemctl disable --now gsm; sudo rm /etc/systemd/system/gsm.service` |

Die Daten (Server, Welten, Backups, Benutzer) liegen im Datenordner `~/gameserver-manager` des Dienst-Benutzers
(änderbar mit der Umgebungsvariable `GSM_DATA`). **Sichere diesen Ordner**, er enthält alles. Die Server laufen
als Docker-Container namens `gsm-<name>`; ein Neustart des Managers beendet sie nicht.

### Fehlersuche

| Problem | Lösung |
|---|---|
| `permission denied` beim Zugriff auf Docker | Benutzer in die Gruppe `docker` aufnehmen und neu anmelden: `sudo usermod -aG docker $USER`, danach `sudo systemctl restart gsm` |
| Server startet nicht, Image kann nicht geladen werden (`429 Too Many Requests`) | Docker Hub begrenzt Abrufe. In `settings.json` ein anderes Image eintragen, z. B. `"java_image": "mirror.gcr.io/library/eclipse-temurin:{java}-jre"` |
| Seite nicht erreichbar / Zertifikatsfehler | DNS-Eintrag und offene Ports 80/443 prüfen, `journalctl -u caddy -f` |
| Konsole bleibt leer (hinter nginx) | WebSocket-Header ergänzen (siehe [Proxy](#reverse-proxy-und-https)) |
| Spieler können nicht verbinden | Port des Servers in Firewall/Router freigeben (TCP), in der Übersicht den Port prüfen |
| Admin-Passwort vergessen | `.venv/bin/python -m gsm passwd admin` auf dem Server |
| Server stoppt sofort | Konsole und `docker logs gsm-<name>` ansehen; oft zu wenig RAM oder falsche Mod-Version |

---

## Benutzer und Rechte

Ohne Anmeldung ist nichts erreichbar. Es gibt zwei Rollen:

| Rolle | Darf |
|---|---|
| **Administrator** | alles: Server erstellen/löschen, Modpacks importieren, Benutzer und Protokoll |
| **Benutzer** | nur die zugewiesenen Server, je nach Recht pro Server |

Rechte pro Server (jedes schließt das vorherige ein):

| Recht | Darf zusätzlich |
|---|---|
| **Ansehen** | Server, Konsole (nur lesen), Mods und Backup-Liste sehen |
| **Bedienen** | Starten, Stoppen, Neustart, Konsolenbefehle, Backup erstellen |
| **Verwalten** | Einstellungen, Mods/Plugins, Backups wiederherstellen/löschen/herunterladen |

Schutzmaßnahmen: Passwörter werden mit scrypt gehasht (mind. 8 Zeichen), nach einer Passwortänderung oder
Sperrung werden bestehende Sitzungen ungültig, Fehlversuche beim Login werden zunehmend gebremst, Cookies sind
`HttpOnly` und `SameSite=Strict` (hinter HTTPS zusätzlich `Secure`), Anfragen von fremden Webseiten werden
abgelehnt, und der letzte aktive Administrator kann nicht gelöscht oder gesperrt werden. Alle Änderungen und
Konsolenbefehle landen im **Protokoll** (`audit.log` im Datenordner, Ansicht für Admins in der Oberfläche).

## Reverse-Proxy und HTTPS

Mit `--domain` richtet das Skript Caddy ein. Der Manager lauscht dann nur auf `127.0.0.1`, von außen geht es
nur über HTTPS. Er erkennt den Proxy (`X-Forwarded-*`): Cookies werden `Secure`, im Protokoll steht die echte
Client-IP. Ein anderer Proxy als lokal wird mit `--trusted-proxies` freigegeben.

Nutzt du nginx statt Caddy, brauchst du für die Konsole WebSocket-Header:
`proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`
sowie `proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $remote_addr;`
und für Uploads ein hohes `client_max_body_size` (Modpacks, Mods).

## Einstellungen (`settings.json` im Datenordner)

| Schlüssel | Standard | Bedeutung |
|---|---|---|
| `runtime` | `auto` | `docker`, `local` oder `auto` (Docker, wenn erreichbar; sonst lokales Java, nur für Tests) |
| `java_image` | `eclipse-temurin:{java}-jre` | Container-Image je Java-Version, z.B. für eine Mirror-Registry |
| `docker_extra_args` | `[]` | zusätzliche Argumente für `docker run` |

Umgebungsvariablen: `GSM_DATA`, `GSM_PASSWORD` (nur beim allerersten Start), `GSM_RUNTIME`, `GSM_JAVA_IMAGE`,
`GSM_DOCKER_ARGS`.

## Aufbau (für Entwickler)

```
gsm/
  web.py            Weboberfläche + JSON-API (Starlette), Anmeldung, Rechteprüfung
  users.py          Benutzer, Rollen, Rechte pro Server
  audit.py          Protokoll
  instances.py      Server anlegen/starten/stoppen, Mods/Plugins
  backup.py         Backups, Aufbewahrung, Zeitplan
  modpacks.py       .mrpack-Import
  jobs.py           Hintergrundaufgaben mit Log
  runtime/          docker.py (Container), local.py (ohne Container)
  games/            ein Spiel = eine Klasse (base.py beschreibt die Schnittstelle)
    minecraft.py, minecraft_providers.py, modrinth.py
  static/           Oberfläche: index.html, app.js (Router, Ansichten), style.css (Designsystem)
deploy/install.sh   Installation als Systemdienst + HTTPS-Proxy
tests/              python -m unittest discover -s tests
```

Entwicklung: `pip install -r requirements.txt`, Tests mit `python -m unittest discover -s tests`
(laufen ohne Docker und ohne Internet). Start mit `python -m gsm serve`.

### Weiteres Spiel hinzufügen

1. In `gsm/games/` eine Klasse von `Game` ableiten: `describe()`, `versions()`, `create()` (Server-Dateien
   installieren), `launch_spec()` (Startkommando, Port, Container-Image/Java) und optional
   `backup_prepare()`/`backup_paths()`.
2. In `gsm/games/__init__.py` eintragen. Runtime, Backups, Konsole und Instanzverwaltung funktionieren
   unverändert; die Oberfläche ist für Minecraft-Felder (Typ, Version) noch fest verdrahtet und müsste für
   weitere Spiele aus `describe()` generiert werden.

## Einschränkungen

- Nur Modrinth-Modpacks (`.mrpack`); CurseForge-Packs brauchen einen API-Key und fehlen noch. Quilt fehlt ebenfalls.
- Docker-Container laufen ohne Restart-Policy: Nach einem Neustart des Rechners startet nur, was auf
  *Automatisch starten* steht (der Manager startet diese Server beim Dienststart).
- Eine Instanz pro Port; Container bekommen ein Speicherlimit (Heap + 768 MB).
