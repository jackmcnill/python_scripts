"""Minecraft (Java Edition) als Spiel-Plugin."""
import re
import time
from pathlib import Path

from ..util import parse_memory_mb
from . import modrinth
from .base import Game, LaunchSpec
from .minecraft_providers import PROVIDERS, required_java

WORLD_FILES = ("server.properties", "ops.json", "whitelist.json", "banned-players.json",
               "banned-ips.json", "usercache.json")
SAVED = re.compile(r"Saved the (game|world)|Save complete")


class Minecraft(Game):
    id = "minecraft"
    label = "Minecraft (Java Edition)"
    terms = {"label": "Minecraft-EULA", "url": "https://aka.ms/MinecraftEULA"}

    def describe(self):
        return {
            "id": self.id, "label": self.label,
            "kinds": [{"id": p.id, "label": p.label, "addons": p.addons} for p in PROVIDERS.values()],
            "defaults": {"memory": "2G", "port": 25565},
            "catalog": True, "terms": self.terms,
        }

    def provider(self, kind):
        try:
            return PROVIDERS[kind]
        except KeyError:
            raise ValueError(f"Unbekannter Server-Typ '{kind}'") from None

    def versions(self, kind, everything=False):
        return self.provider(kind).versions(everything)

    def resolve_version(self, kind, version, everything=False):
        available = self.versions(kind, everything)
        if version in (None, "", "latest"):
            return available[0]
        if version not in available and version not in self.versions(kind, True):
            raise ValueError(f"Version '{version}' gibt es für {kind} nicht")
        return version

    def create(self, inst, ctx):
        inst.java_major = required_java(inst.version)
        ctx.log(f"Java {inst.java_major} (Container-Image)")
        result = self.provider(inst.kind).install(inst.version, inst.data_dir, ctx, inst.loader_version)
        inst.loader_version = result["loader_version"]
        inst.launch = result["launch"]
        addons = self.addon_dir(inst)
        if addons:
            (inst.data_dir / addons).mkdir(exist_ok=True)

    def launch_spec(self, inst):
        mem = inst.memory
        argv = ["java", f"-Xms{mem}", f"-Xmx{mem}"]
        if "jar" in inst.launch:
            argv += ["-jar", inst.launch["jar"]]
        else:
            argv.append("@" + str(Path(inst.launch["args_dir"]) / "unix_args.txt"))
        argv.append("nogui")
        return LaunchSpec(argv=argv, port=inst.port, memory_mb=parse_memory_mb(mem) + 768,
                          java_major=inst.java_major)

    def accept_terms(self, inst):
        (inst.data_dir / "eula.txt").write_text(f"# {self.terms['url']}\neula=true\n", encoding="utf-8")

    def default_properties(self, inst):
        return {"server.properties": f"server-port={inst.port}\n"}

    # --- Mods / Plugins -----------------------------------------------------
    def addon_dir(self, inst):
        return self.provider(inst.kind).addons

    def catalog_search(self, inst, query, offset=0):
        return modrinth.search(query, self.provider(inst.kind).modrinth_loaders, inst.version, offset=offset)

    def catalog_install(self, inst, project, log):
        provider = self.provider(inst.kind)
        if not provider.addons:
            raise RuntimeError("Vanilla-Server unterstützen keine Mods oder Plugins")
        return modrinth.install_project(inst.data_dir, provider.addons, project,
                                        provider.modrinth_loaders, inst.version, log)

    # --- Backups --------------------------------------------------------------
    def backup_paths(self, inst, scope):
        if scope != "world":
            return None
        data = inst.data_dir
        worlds = [p.parent.relative_to(data).as_posix() for p in data.glob("*/level.dat")]
        return worlds + [f for f in WORLD_FILES if (data / f).exists()]

    def backup_prepare(self, send, recent_logs):
        send("save-off")
        seen = sum(bool(SAVED.search(l)) for l in recent_logs(300))
        send("save-all flush")
        deadline = time.time() + 45
        while time.time() < deadline:
            time.sleep(1)
            if sum(bool(SAVED.search(l)) for l in recent_logs(300)) > seen:
                break
        return lambda: send("save-on")
