"""Instanzen (Server) verwalten: anlegen, starten, stoppen, Einstellungen, Mods/Plugins."""
import json
import shutil
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import config
from .games import get_game
from .util import SLUG_RE, parse_memory_mb, safe_filename, safe_join

DEFAULT_BACKUP = {"enabled": False, "interval_hours": 24, "keep": 7, "scope": "full"}


class Busy(RuntimeError):
    pass


@dataclass
class Instance:
    id: str
    name: str
    game: str
    kind: str
    version: str
    memory: str = "2G"
    port: int = 25565
    loader_version: str | None = None
    launch: dict = field(default_factory=dict)
    java_major: int | None = None
    created: str = ""
    auto_start: bool = False
    backup: dict = field(default_factory=lambda: dict(DEFAULT_BACKUP))
    root: Path = field(default=None, repr=False)

    @property
    def data_dir(self):
        return self.root / "data"

    def to_json(self):
        d = asdict(self)
        d.pop("root")
        return d


class CreateContext:
    def __init__(self, log, run_java):
        self.log, self.run_java = log, run_java


class Manager:
    def __init__(self, settings, runtime):
        self.settings, self.runtime = settings, runtime
        self._busy, self._lock = {}, threading.Lock()

    # --- Speicherung --------------------------------------------------------------
    def _load(self, root):
        data = json.loads((root / "instance.json").read_text(encoding="utf-8"))
        data["backup"] = {**DEFAULT_BACKUP, **data.get("backup", {})}
        return Instance(**data, root=root)

    def save(self, inst):
        tmp = inst.root / "instance.json.tmp"
        tmp.write_text(json.dumps(inst.to_json(), indent=2), encoding="utf-8")
        tmp.replace(inst.root / "instance.json")

    def list(self):
        base = config.instances_dir()
        if not base.exists():
            return []
        return [self._load(p) for p in sorted(base.iterdir()) if (p / "instance.json").exists()]

    def get(self, inst_id):
        root = config.instances_dir() / inst_id
        if not SLUG_RE.match(inst_id) or not (root / "instance.json").exists():
            raise KeyError(f"Server '{inst_id}' existiert nicht")
        return self._load(root)

    # --- Sperren ------------------------------------------------------------------
    @contextmanager
    def busy(self, inst, label):
        with self._lock:
            if inst.id in self._busy:
                raise Busy(f"'{inst.name}' ist beschäftigt: {self._busy[inst.id]}")
            self._busy[inst.id] = label
        try:
            yield
        finally:
            with self._lock:
                self._busy.pop(inst.id, None)

    def busy_label(self, inst_id):
        return self._busy.get(inst_id)

    def status(self, inst):
        return {"state": self.runtime.status(inst), "busy": self.busy_label(inst.id)}

    # --- Anlegen / Löschen ----------------------------------------------------------
    def validate_settings(self, memory, port, ignore=None):
        parse_memory_mb(memory)
        if not 1024 <= int(port) <= 65535:
            raise ValueError("Port muss zwischen 1024 und 65535 liegen")
        for other in self.list():
            if other.id != ignore and other.port == int(port):
                raise ValueError(f"Port {port} wird bereits von '{other.name}' genutzt")

    def create(self, name, game_id, kind, version, memory="2G", port=25565, accept_terms=False,
               loader_version=None, log=print, prepare=None):
        """Legt einen Server an und installiert ihn. prepare(inst) kann danach Zusatzdateien einspielen."""
        inst_id = name.strip().lower().replace(" ", "-")
        if not SLUG_RE.match(inst_id):
            raise ValueError("Name: nur Buchstaben, Zahlen, - und _ (max. 32 Zeichen)")
        game = get_game(game_id)
        if game.terms and not accept_terms:
            raise ValueError(f"Bitte {game.terms['label']} akzeptieren ({game.terms['url']})")
        self.validate_settings(memory, port)
        root = config.instances_dir() / inst_id
        if root.exists():
            raise ValueError(f"Server '{inst_id}' existiert bereits")
        inst = Instance(id=inst_id, name=name.strip(), game=game_id, kind=kind,
                        version=game.resolve_version(kind, version), memory=memory, port=int(port),
                        loader_version=loader_version, created=datetime.now().isoformat(timespec="seconds"),
                        root=root)
        (root / "data").mkdir(parents=True)
        try:
            with self.busy(inst, "Wird installiert"):
                ctx = CreateContext(log, lambda args: self.runtime.run_java(inst, inst.java_major, args, log))
                log(f"Installiere {game.label} {kind} {inst.version} ...")
                game.create(inst, ctx)
                for rel, text in game.default_properties(inst).items():
                    target = inst.data_dir / rel
                    if not target.exists():
                        target.write_text(text, encoding="utf-8")
                if game.terms:
                    game.accept_terms(inst)
                if prepare:
                    prepare(inst)
                self.save(inst)
        except BaseException:
            shutil.rmtree(root, ignore_errors=True)
            raise
        log("Fertig.")
        return inst

    def delete(self, inst, delete_backups=False):
        with self.busy(inst, "Wird gelöscht"):
            game = get_game(inst.game)
            self.runtime.stop(inst, game.launch_spec(inst), timeout=30)
            self.runtime.remove(inst)
            shutil.rmtree(inst.root)
            if delete_backups:
                shutil.rmtree(config.backups_dir() / inst.id, ignore_errors=True)

    # --- Betrieb ----------------------------------------------------------------------
    def start(self, inst, log=print):
        with self.busy(inst, "Startet"):
            if self.runtime.status(inst) == "running":
                raise RuntimeError("Server läuft bereits")
            self.runtime.start(inst, get_game(inst.game).launch_spec(inst))
            log("Gestartet.")

    def stop(self, inst, log=print):
        with self.busy(inst, "Wird gestoppt"):
            log("Fahre Server herunter ...")
            self.runtime.stop(inst, get_game(inst.game).launch_spec(inst))
            log("Gestoppt.")

    def restart(self, inst, log=print):
        self.stop(inst, log)
        self.start(inst, log)

    def kill(self, inst):
        self.runtime.kill(inst)

    def send(self, inst, line):
        self.runtime.send(inst, line)

    def update(self, inst, patch):
        memory = patch.get("memory", inst.memory)
        port = patch.get("port", inst.port)
        self.validate_settings(memory, port, ignore=inst.id)
        inst.memory, inst.port = memory, int(port)
        if "auto_start" in patch:
            inst.auto_start = bool(patch["auto_start"])
        if "backup" in patch:
            b = {**inst.backup, **patch["backup"]}
            if b["scope"] not in ("full", "world"):
                raise ValueError("Backup-Umfang muss 'full' oder 'world' sein")
            b["interval_hours"] = max(1, int(b["interval_hours"]))
            b["keep"] = max(1, int(b["keep"]))
            b["enabled"] = bool(b["enabled"])
            inst.backup = b
        self.save(inst)
        self.sync_port(inst)
        return inst

    def sync_port(self, inst):
        """server.properties-Port an den Host-Port anpassen (Container mappt Port 1:1)."""
        props = inst.data_dir / "server.properties"
        if inst.game == "minecraft":
            lines = props.read_text(encoding="utf-8").splitlines() if props.exists() else []
            lines = [l for l in lines if not l.startswith("server-port=")] + [f"server-port={inst.port}"]
            props.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- Mods / Plugins ------------------------------------------------------------------
    def _addon_dir(self, inst):
        sub = get_game(inst.game).addon_dir(inst)
        if not sub:
            raise ValueError("Dieser Server-Typ unterstützt keine Mods oder Plugins")
        path = inst.data_dir / sub
        path.mkdir(exist_ok=True)
        return path

    def list_addons(self, inst):
        from .games import modrinth
        folder = self._addon_dir(inst)
        registry = modrinth.read_registry(inst.data_dir)
        out = []
        for f in sorted(folder.iterdir()):
            if f.is_file() and (f.name.endswith(".jar") or f.name.endswith(".jar.disabled")):
                info = registry.get(f.name.removesuffix(".disabled"), {})
                out.append({"file": f.name, "enabled": f.suffix == ".jar", "size": f.stat().st_size,
                            "title": info.get("title") or f.name, "version": info.get("version", "")})
        return out

    def save_addon(self, inst, filename, stream):
        filename = safe_filename(filename)
        if not filename.endswith(".jar"):
            raise ValueError("Nur .jar-Dateien erlaubt")
        target = safe_join(self._addon_dir(inst), filename)
        with open(target, "wb") as out:
            shutil.copyfileobj(stream, out)
        if target.stat().st_size < 4 or open(target, "rb").read(2) != b"PK":
            target.unlink()
            raise ValueError(f"{filename} ist keine gültige .jar-Datei")
        return filename

    def remove_addon(self, inst, filename):
        safe_join(self._addon_dir(inst), safe_filename(filename)).unlink()

    def toggle_addon(self, inst, filename, enabled):
        path = safe_join(self._addon_dir(inst), safe_filename(filename))
        target = path.with_name(path.name.removesuffix(".disabled")) if enabled else \
            path.with_name(path.name.removesuffix(".disabled") + ".disabled")
        if path != target:
            path.rename(target)
