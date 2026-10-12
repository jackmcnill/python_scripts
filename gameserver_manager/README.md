# Game Server Manager

Spieleserver (zuerst Minecraft) über eine Webseite erstellen und verwalten. Jeder Server läuft in einem
eigenen **Docker-Container**, damit jede Java-Version (8, 17, 21, 25) unabhängig von der Distribution
funktioniert. Backups laufen regelmäßig automatisch.

## Funktionen

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

Beim ersten Start wird ein Passwort erzeugt und einmalig angezeigt (oder vorher `GSM_PASSWORD` setzen).
Ändern: `python -m gsm passwd`.

Daten (Server, Backups, Einstellungen) liegen in `~/gameserver-manager`, änderbar mit `GSM_DATA`.

### Aus dem Netzwerk erreichbar machen

Standardmäßig lauscht die Oberfläche nur auf `127.0.0.1`. Die Oberfläche kann Container starten und
Befehle an Server senden, schütze sie deshalb: am besten per Reverse-Proxy mit HTTPS (nginx, Caddy) oder
SSH-Tunnel/VPN. `--host 0.0.0.0` schaltet den direkten Zugriff (unverschlüsselt) frei.
Die Minecraft-Ports der Server (Standard 25565, je Server eigener Port) müssen in der Firewall offen sein.

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
  web.py            Weboberfläche + JSON-API (Starlette), Anmeldung
  instances.py      Server anlegen/starten/stoppen, Mods/Plugins
  backup.py         Backups, Aufbewahrung, Zeitplan
  modpacks.py       .mrpack-Import
  jobs.py           Hintergrundaufgaben mit Log
  runtime/          docker.py (Container), local.py (ohne Container)
  games/            ein Spiel = eine Klasse (base.py beschreibt die Schnittstelle)
    minecraft.py, minecraft_providers.py, modrinth.py
  static/           Oberfläche (HTML/JS/CSS ohne Build-Schritt)
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
