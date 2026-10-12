"""Schnittstelle für Spiele. Ein neues Spiel = eine Unterklasse von Game + Eintrag in games/__init__.py."""
from dataclasses import dataclass, field


@dataclass
class LaunchSpec:
    """Alles, was eine Runtime braucht, um den Server zu starten."""
    argv: list                      # Startkommando, z.B. ["java", "-Xmx2G", "-jar", "server.jar"]
    port: int                       # Host-Port (wird 1:1 in den Container gemappt)
    memory_mb: int                  # Speicherlimit des Containers (Heap + Overhead)
    stop_command: str = "stop"      # Konsolenbefehl für ein sauberes Herunterfahren
    protocols: tuple = ("tcp",)
    java_major: int | None = None   # Java-Version für Container-Image bzw. lokalen Start
    env: dict = field(default_factory=dict)


class Game:
    id = ""
    label = ""

    def describe(self):
        """Beschreibung für die Weboberfläche: Server-Typen, Felder, Standardwerte."""
        raise NotImplementedError

    def versions(self, kind, everything=False):
        raise NotImplementedError

    def create(self, inst, ctx):
        """Installiert den Server in inst.data_dir. ctx: siehe instances.CreateContext."""
        raise NotImplementedError

    def launch_spec(self, inst):
        raise NotImplementedError

    # --- optionale Erweiterungspunkte ---------------------------------------
    def addon_dir(self, inst):
        """Ordner für Mods/Plugins relativ zum Datenordner (oder None)."""
        return None

    def backup_paths(self, inst, scope):
        """Relative Pfade, die in ein Backup gehören (None = alles außer Logs)."""
        return None

    BACKUP_EXCLUDE = ("logs", "crash-reports", ".gsm", "cache")

    def backup_prepare(self, send, recent_logs):
        """Vor dem Backup eines laufenden Servers (z.B. Welt speichern). Gibt Funktion für danach zurück."""
        return lambda: None

    terms = None   # {"label": ..., "url": ...}, wenn der Nutzer Bedingungen akzeptieren muss

    def accept_terms(self, inst):
        """Schreibt die Zustimmung (z.B. eula.txt), nachdem der Nutzer zugestimmt hat."""

    def default_properties(self, inst):
        """Dateien, die vor dem ersten Start vorbelegt werden: {relativer Pfad: Text}."""
        return {}
