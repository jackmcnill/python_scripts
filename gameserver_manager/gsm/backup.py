"""Backups (tar.gz) mit Aufbewahrung und Zeitplan."""
import re
import shutil
import tarfile
import threading
import time
from datetime import datetime

from . import config
from .games import get_game
from .instances import Busy

NAME_RE = re.compile(r"^[a-z0-9_-]+-\d{8}-\d{6}-(full|world)\.tar\.gz$")


class BackupService:
    def __init__(self, manager, jobs):
        self.manager, self.jobs = manager, jobs
        self._stop = threading.Event()

    def folder(self, inst_id):
        return config.backups_dir() / inst_id

    def path(self, inst, name):
        if not NAME_RE.match(name) or not name.startswith(inst.id + "-"):
            raise ValueError("Ungültiger Backup-Name")
        path = self.folder(inst.id) / name
        if not path.exists():
            raise KeyError(f"Backup '{name}' existiert nicht")
        return path

    def list(self, inst):
        folder = self.folder(inst.id)
        if not folder.exists():
            return []
        items = [{"name": p.name, "size": p.stat().st_size, "created": datetime.fromtimestamp(p.stat().st_mtime)
                 .isoformat(timespec="seconds"), "scope": p.name.rsplit("-", 1)[1].split(".")[0]}
                 for p in folder.glob("*.tar.gz") if NAME_RE.match(p.name)]
        return sorted(items, key=lambda i: i["name"], reverse=True)

    def create(self, inst, log=print, scope=None, prune=True):
        scope = scope or inst.backup["scope"]
        game = get_game(inst.game)
        with self.manager.busy(inst, "Backup läuft"):
            runtime = self.manager.runtime
            finish = lambda: None  # noqa: E731
            if runtime.status(inst) == "running":
                log("Server läuft: speichere die Welt ...")
                finish = game.backup_prepare(lambda c: runtime.send(inst, c), lambda n: runtime.recent_logs(inst, n))
            try:
                name = f"{inst.id}-{datetime.now():%Y%m%d-%H%M%S}-{scope}.tar.gz"
                folder = self.folder(inst.id)
                folder.mkdir(parents=True, exist_ok=True)
                tmp = folder / (name + ".part")
                log(f"Erstelle Backup {name} ...")
                try:
                    with tarfile.open(tmp, "w:gz") as tar:
                        for rel in self._entries(inst, game, scope):
                            tar.add(inst.data_dir / rel, arcname=rel)
                    tmp.replace(folder / name)
                finally:
                    tmp.unlink(missing_ok=True)
            finally:
                finish()
            if prune:
                self.prune(inst, log)
            log(f"Backup fertig ({(folder / name).stat().st_size / 1048576:.1f} MB)")
            return name

    def _entries(self, inst, game, scope):
        selected = game.backup_paths(inst, scope)
        if selected is not None:
            return [p for p in selected if (inst.data_dir / p).exists()]
        return [p.name for p in sorted(inst.data_dir.iterdir()) if p.name not in game.BACKUP_EXCLUDE
                and not p.name.endswith(".part")]

    def prune(self, inst, log=print):
        for old in self.list(inst)[inst.backup["keep"]:]:
            (self.folder(inst.id) / old["name"]).unlink(missing_ok=True)
            log(f"Altes Backup gelöscht: {old['name']}")

    def delete(self, inst, name):
        self.path(inst, name).unlink()

    def restore(self, inst, name, log=print):
        archive = self.path(inst, name)
        scope = name.rsplit("-", 1)[1].split(".")[0]
        if self.manager.runtime.status(inst) == "running":
            raise RuntimeError("Server muss für die Wiederherstellung gestoppt sein")
        log("Sichere den aktuellen Stand vor der Wiederherstellung ...")
        self.create(inst, log, scope="full", prune=False)
        with self.manager.busy(inst, "Wird wiederhergestellt"):
            staging = inst.root / "restore-tmp"
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir()
            try:
                log(f"Entpacke {name} ...")
                with tarfile.open(archive) as tar:
                    tar.extractall(staging, filter="data")
                entries = list(staging.iterdir())
                if scope == "full":
                    for p in inst.data_dir.iterdir():
                        shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
                for src in entries:
                    dest = inst.data_dir / src.name
                    if dest.exists():
                        shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                    shutil.move(str(src), dest)
            finally:
                shutil.rmtree(staging, ignore_errors=True)
            log("Wiederherstellung abgeschlossen.")

    # --- Zeitplan ---------------------------------------------------------------------
    def last_backup_time(self, inst):
        folder = self.folder(inst.id)
        times = [p.stat().st_mtime for p in folder.glob("*.tar.gz")] if folder.exists() else []
        return max(times, default=0)

    def due(self, inst, now=None):
        b = inst.backup
        return b["enabled"] and (now or time.time()) - self.last_backup_time(inst) >= b["interval_hours"] * 3600

    def tick(self):
        for inst in self.manager.list():
            if self.due(inst) and not self.manager.busy_label(inst.id):
                self.jobs.start(f"Geplantes Backup: {inst.name}", lambda job, i=inst: self._scheduled(i, job))

    def _scheduled(self, inst, job):
        try:
            return self.create(inst, job.log)
        except Busy:
            job.log("Übersprungen: Server ist beschäftigt")

    def start_scheduler(self, interval=60):
        def loop():
            while not self._stop.wait(interval):
                try:
                    self.tick()
                except Exception as exc:  # noqa: BLE001 - Scheduler darf nie sterben
                    print(f"Backup-Scheduler: {exc}")

        threading.Thread(target=loop, daemon=True, name="backup-scheduler").start()

    def stop_scheduler(self):
        self._stop.set()
