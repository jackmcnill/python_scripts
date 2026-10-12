# Game Server Manager

Spieleserver (zuerst Minecraft) über eine Webseite erstellen und verwalten. Jeder Server läuft in einem
eigenen **Docker-Container**, damit jede Java-Version (8, 17, 21, 25) unabhängig von der Distribution
funktioniert. Backups laufen regelmäßig automatisch.

## Funktionen

- **Moderne Oberfläche**: Dashboard mit Server-Karten, Terminal-Konsole mit farbigen Log-Ebenen, Befehlsverlauf (Pfeiltasten) und Schnellbefehlen, Drag-and-drop für Mods, Hell/Dunkel-Design (folgt dem System, umschaltbar), Toasts statt Pop-ups, Fortschrittsanzeige für Hintergrundaufgaben und eine mobile Ansicht. Direkte Links wie `#/server/survival/console` funktionieren. Alles ohne Build-Schritt und ohne externe Ressourcen, also auch im LAN ohne Internet.

- **Server anlegen**: Vanilla, Paper, Fabric, Forge, NeoForge, jeweils in beliebiger (auch älterer) Minecraft-Version.
  Die passende Java-Version wird automatisch gewählt (aus den Mojang-Daten).
- **Konsole** im Browser (Live-Log, Befehle senden), Start/Stopp/Neustart, Autostart.
- **Mods/Plugins**: `.jar` hochladen, auf/von **Modrinth** suchen und mit Abhängigkeiten installieren,
  einzeln deaktivieren oder löschen.
- **Modpacks**: Modrinth-Modpacks (`.mrpack`, per Datei oder Link/Slug) werden als neuer Server eingespielt.
  Loader und Versionen kommen aus dem Pack, Client-only-Mods werden übersprungen.
- **Backups**: manuell und per Zeitplan (alle N Stunden, die letzten N behalten), kompletter Server oder nur
  Welten. Läuft der Server, wird vorher die Welt gespeichert (`save-off`/`save-all`). Download und
  Wiederherstellung über die Oberfläche (vor einer Wiederherstellung wird der aktuelle Stand gesichert).

## Voraussetzungen

- Python 3.12+ und Docker (der Nutzer muss `docker` ausführen dürfen, z.B. Gruppe `docker`)
- Ohne Docker fällt der Manager auf eine lokal installierte Java-Version zurück (nur für Tests gedacht).

## Start

```bash
cd gameserver_manager
pip install -r requirements.txt
python -m gsm serve                 # http://127.0.0.1:8080
```

Beim ersten Start wird der Administrator `admin` mit einem Zufallspasswort angelegt und einmalig angezeigt
(oder vorher `GSM_PASSWORD` setzen). Weitere Benutzer legst du in der Oberfläche unter **Benutzer & Protokoll** an.

Auf der Kommandozeile (z.B. bei vergessenem Passwort):
`python -m gsm passwd [NAME]` und `python -m gsm adduser NAME [--admin]`.

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

Weitere Schutzmaßnahmen: Passwörter werden mit scrypt gehasht (mind. 8 Zeichen), nach einer Passwortänderung
oder Sperrung werden bestehende Sitzungen ungültig, Fehlversuche beim Login werden zunehmend gebremst,
Cookies sind `HttpOnly` und `SameSite=Strict`, Anfragen von fremden Webseiten werden abgelehnt, und der letzte
aktive Administrator kann nicht gelöscht oder gesperrt werden. Alle Änderungen und Konsolenbefehle landen im
**Protokoll** (`audit.log` im Datenordner, Ansicht für Admins in der Oberfläche).

Daten (Server, Backups, Einstellungen) liegen in `~/gameserver-manager`, änderbar mit `GSM_DATA`.

### Auf einem Server installieren und von außen erreichbar machen

Auf einem Debian/Ubuntu-Server (Python 3.12+, z. B. Ubuntu 24.04):

```bash
git clone -b minecraft-servermanager https://github.com/jackmcnill/python_scripts.git
cd python_scripts/gameserver_manager
sudo ./deploy/install.sh --domain manager.deine-domain.de
```

Das Skript installiert Docker und die Python-Umgebung, legt den Administrator an (das Passwort wird einmalig
angezeigt), richtet den Systemdienst `gsm` ein und setzt **Caddy** als HTTPS-Proxy davor. Das Zertifikat holt
Caddy automatisch. Mit `--dry-run` zeigt das Skript nur, was es tun würde.

Voraussetzungen für den Zugriff von außen:

1. Ein DNS-Eintrag (A/AAAA) der Domain zeigt auf den Server (bei wechselnder IP z. B. per DynDNS).
2. Die Ports **80 und 443** sind in Firewall und Router erreichbar (nur für den Manager).
3. Die Minecraft-Ports der Server (Standard 25565, je Server eigener Port) sind separat freigegeben.

Der Manager selbst lauscht dabei nur auf `127.0.0.1`; von außen ist er nur über HTTPS erreichbar. Er erkennt
den Proxy (`X-Forwarded-*`): Cookies werden `Secure`, im Protokoll steht die echte Client-IP. Ein anderer
Proxy als lokal wird mit `--trusted-proxies` freigegeben.

Ohne eigene Domain oder ohne offene Ports: Tailscale/WireGuard (VPN) oder ein Cloudflare Tunnel; dann den
Manager mit `sudo ./deploy/install.sh` (ohne `--domain`) installieren und den Port nicht ins Internet freigeben.

Nutzt du nginx statt Caddy, brauchst du für die Konsole WebSocket-Header:
`proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`
sowie `proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $remote_addr;`
und für Uploads ein hohes `client_max_body_size` (Modpacks, Mods).

Update: `git pull && sudo systemctl restart gsm`. Daten liegen in `~/gameserver-manager`.

## Einstellungen (`settings.json` im Datenordner)

| Schlüssel | Standard | Bedeutung |
|---|---|---|
| `runtime` | `auto` | `docker`, `local` oder `auto` (Docker, wenn erreichbar) |
| `java_image` | `eclipse-temurin:{java}-jre` | Container-Image je Java-Version, z.B. für eine Mirror-Registry |
| `docker_extra_args` | `[]` | zusätzliche Argumente für `docker run` |

Umgebungsvariablen: `GSM_DATA`, `GSM_PASSWORD`, `GSM_RUNTIME`, `GSM_JAVA_IMAGE`, `GSM_DOCKER_ARGS`.

## Aufbau

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
  deploy/install.sh Installation als Systemdienst + HTTPS-Proxy
  static/           Oberfläche: index.html, app.js (Router, Ansichten), style.css (Designsystem)
tests/              python -m unittest discover -s tests
```

### Weiteres Spiel hinzufügen

1. In `gsm/games/` eine Klasse von `Game` ableiten: `describe()`, `versions()`, `create()` (Server-Dateien
   installieren), `launch_spec()` (Startkommando, Port, Container-Image/Java) und optional
   `backup_prepare()`/`backup_paths()`.
2. In `gsm/games/__init__.py` eintragen. Runtime, Backups, Konsole und Instanzverwaltung funktionieren
   unverändert; die Oberfläche ist für Minecraft-Felder (Typ, Version) noch fest verdrahtet und müsste für
   weitere Spiele aus `describe()` generiert werden.

## Einschränkungen

- Nur Modrinth-Modpacks (`.mrpack`); CurseForge-Packs brauchen einen API-Key und fehlen noch. Quilt fehlt ebenfalls.
- Hat der Manager einen Container gestartet, bleibt dieser auch bei Manager-Neustart bestehen; nach einem
  Neustart des Rechners helfen "Autostart" und der Manager.
- Eine Instanz pro Port; Docker-Container werden mit einem Speicherlimit (Heap + 768 MB) gestartet.
