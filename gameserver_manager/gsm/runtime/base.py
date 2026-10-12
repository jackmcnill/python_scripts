"""Gemeinsame Schnittstelle der Runtimes (Docker, lokal)."""
import time


class LogStream:
    """Fortlaufender Log-Strom; close() beendet das Lesen."""

    def __init__(self, lines, closer):
        self._lines, self._closer = lines, closer

    def __iter__(self):
        return iter(self._lines)

    def close(self):
        self._closer()


class Runtime:
    name = ""

    def available(self):
        """-> (bool, Hinweistext)"""
        raise NotImplementedError

    def start(self, inst, spec):
        raise NotImplementedError

    def status(self, inst):
        """'running' | 'stopped'"""
        raise NotImplementedError

    def send(self, inst, line):
        raise NotImplementedError

    def kill(self, inst):
        raise NotImplementedError

    def remove(self, inst):
        """Räumt Reste (z.B. beendeten Container) auf."""

    def recent_logs(self, inst, lines=200):
        raise NotImplementedError

    def log_stream(self, inst, tail=200):
        raise NotImplementedError

    def run_java(self, inst, java_major, args, on_line):
        """Führt `java <args>` im Datenordner aus (Installer). -> Exit-Code"""
        raise NotImplementedError

    def stop(self, inst, spec, timeout=60):
        """Sauber herunterfahren (Stop-Befehl), nach timeout hart beenden."""
        if self.status(inst) != "running":
            return
        try:
            self.send(inst, spec.stop_command)
        except Exception:  # noqa: BLE001 - dann direkt hart beenden
            pass
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.status(inst) != "running":
                return
            time.sleep(1)
        self.kill(inst)
