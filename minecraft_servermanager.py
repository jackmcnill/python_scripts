#!/usr/bin/env python3
"""Minecraft Server Manager

Erstellt und verwaltet mehrere Minecraft-Server (nur Python-Standardbibliothek).

Unterstützte Server-Typen:
    vanilla   Mojang-Server (alle Versionen mit offiziellem Server-Download)
    paper     Paper (Plugins)
    fabric    Fabric (Mods)
    forge     Forge (Mods)
    neoforge  NeoForge (Mods)

Beispiele:
    python minecraft_servermanager.py versions fabric
    python minecraft_servermanager.py create survival fabric 1.20.1 --memory 4G
    python minecraft_servermanager.py create alt vanilla 1.12.2
    python minecraft_servermanager.py list
    python minecraft_servermanager.py start survival

Die Server liegen standardmäßig in ~/minecraft-servers (änderbar mit --home
oder der Umgebungsvariable MCSM_HOME).
"""
import argparse
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

USER_AGENT = "python_scripts-minecraft-servermanager/1.0"
EULA_URL = "https://aka.ms/MinecraftEULA"
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def http_json(url):
    return json.loads(http_get(url))


def download(url, dest, checksum=None, algo="sha1"):
    """Lädt url nach dest (mit Fortschritt) und prüft optional die Prüfsumme."""
    dest = Path(dest)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.new(algo)
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total and sys.stdout.isatty():
                print(f"\r  {dest.name}: {done * 100 // total:3d}% "
                      f"({done / 1048576:.1f}/{total / 1048576:.1f} MB)", end="", flush=True)
    print(f"\r  {dest.name}: {done / 1048576:.1f} MB geladen" + " " * 20)
    if checksum and h.hexdigest().lower() != checksum.lower():
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Prüfsumme von {dest.name} stimmt nicht überein")


def ver_key(text):
    """Sortierschlüssel: '1.20.4' < '1.20.10' < '26.1'."""
    return tuple(int(n) for n in re.findall(r"\d+", text))


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


# --------------------------------------------------------------------------
# Mojang (wird auch für die benötigte Java-Version aller Typen genutzt)
# --------------------------------------------------------------------------

_manifest = None


def mojang_manifest():
    global _manifest
    if _manifest is None:
        _manifest = http_json("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
    return _manifest


def mojang_version_info(mc):
    for v in mojang_manifest()["versions"]:
        if v["id"] == mc:
            return http_json(v["url"])
    raise RuntimeError(f"Minecraft-Version '{mc}' ist Mojang nicht bekannt")


def required_java(mc):
    try:
        return mojang_version_info(mc).get("javaVersion", {}).get("majorVersion", 8)
    except RuntimeError:
        return 17


# --------------------------------------------------------------------------
# Java-Erkennung
# --------------------------------------------------------------------------

def java_major(java):
    try:
        out = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'version "(\d+)(?:\.(\d+))?', out.stderr + out.stdout)
    if not m:
        return None
    major = int(m.group(1))
    return int(m.group(2)) if major == 1 and m.group(2) else major  # 1.8 -> 8


def find_javas():
    exe = "java.exe" if os.name == "nt" else "java"
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(os.path.join(os.environ["JAVA_HOME"], "bin", exe))
    if shutil.which("java"):
        candidates.append(shutil.which("java"))
    patterns = [
        "/usr/lib/jvm/*/bin/java",
        "/usr/lib64/jvm/*/bin/java",
        "/opt/*/bin/java",
        "/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
        "~/.sdkman/candidates/java/*/bin/java",
        "~/.jdks/*/bin/java",
        "C:/Program Files/*/*/bin/java.exe",
        "C:/Program Files/Java/*/bin/java.exe",
    ]
    for pattern in patterns:
        candidates.extend(glob.glob(os.path.expanduser(pattern)))
    javas, seen = {}, set()
    for c in candidates:
        real = os.path.realpath(c)
        if real in seen or not os.path.isfile(c):
            continue
        seen.add(real)
        major = java_major(c)
        if major:
            javas.setdefault(c, major)
    return javas


def pick_java(needed):
    """Wählt die passendste installierte Java-Version (exakt, sonst die nächsthöhere)."""
    javas = find_javas()
    exact = [p for p, m in javas.items() if m == needed]
    if exact:
        return exact[0]
    higher = sorted((m, p) for p, m in javas.items() if m > needed)
    if higher:
        print(f"  Hinweis: Java {needed} nicht gefunden, nutze Java {higher[0][0]} "
              "(ältere Mod-Loader laufen damit evtl. nicht).")
        return higher[0][1]
    found = ", ".join(f"{m}" for m in sorted(set(javas.values()))) or "keine"
    raise RuntimeError(f"Java {needed} wird benötigt, gefunden: {found}. "
                       "Installiere es oder gib --java PFAD an.")


# --------------------------------------------------------------------------
# Server-Typen
# --------------------------------------------------------------------------

class Vanilla:
    label = "Vanilla"
    modded = False

    def versions(self, everything=False):
        types = {"release"} if not everything else {"release", "snapshot", "old_beta", "old_alpha"}
        return [v["id"] for v in mojang_manifest()["versions"] if v["type"] in types]

    def prepare(self, mc, dest, java):
        server = mojang_version_info(mc).get("downloads", {}).get("server")
        if not server:
            raise RuntimeError(f"Für {mc} bietet Mojang keinen Server-Download an")
        download(server["url"], dest / "server.jar", server["sha1"], "sha1")
        return {"loader_version": None, "launch": {"jar": "server.jar"}}


class Paper(Vanilla):
    label = "Paper"
    api = "https://fill.papermc.io/v3/projects/paper"

    def versions(self, everything=False):
        out = []
        for group in http_json(self.api)["versions"].values():
            out.extend(group)
        return out if everything else [v for v in out if "-" not in v]

    def prepare(self, mc, dest, java):
        build = http_json(f"{self.api}/versions/{mc}/builds/latest")
        dl = build["downloads"]["server:default"]
        download(dl["url"], dest / "server.jar", dl["checksums"]["sha256"], "sha256")
        return {"loader_version": str(build["id"]), "launch": {"jar": "server.jar"}}


class Fabric(Vanilla):
    label = "Fabric"
    meta = "https://meta.fabricmc.net/v2/versions"

    def versions(self, everything=False):
        return [v["version"] for v in http_json(f"{self.meta}/game") if everything or v["stable"]]

    def prepare(self, mc, dest, java):
        loader = next(v["version"] for v in http_json(f"{self.meta}/loader") if v["stable"])
        installer = next(v["version"] for v in http_json(f"{self.meta}/installer") if v["stable"])
        download(f"{self.meta}/loader/{mc}/{loader}/{installer}/server/jar", dest / "server.jar")
        return {"loader_version": loader, "launch": {"jar": "server.jar"}}


class InstallerBased(Vanilla):
    """Gemeinsame Logik für Forge/NeoForge: Installer laden und mit --installServer ausführen."""
    modded = True
    libs_glob = ""
    jar_glob = ""

    def mc_to_loader(self):
        """Gibt {mc_version: [loader_version, ...]} zurück (neueste zuerst)."""
        raise NotImplementedError

    def installer_url(self, loader_version):
        raise NotImplementedError

    def versions(self, everything=False):
        return sorted(self.mc_to_loader(), key=ver_key, reverse=True)

    def pick(self, mc):
        loaders = self.mc_to_loader().get(mc)
        if not loaders:
            raise RuntimeError(f"{self.label} bietet keine Version für Minecraft {mc}")
        return loaders[0]

    def prepare(self, mc, dest, java):
        loader = self.pick(mc)
        installer = dest / "installer.jar"
        download(self.installer_url(loader), installer)
        print(f"  Installiere {self.label} {loader} (das dauert einen Moment) ...")
        res = subprocess.run([java, "-jar", str(installer), "--installServer"], cwd=dest)
        if res.returncode != 0:
            raise RuntimeError(f"{self.label}-Installer ist fehlgeschlagen")
        installer.unlink(missing_ok=True)
        (dest / "installer.jar.log").unlink(missing_ok=True)
        return {"loader_version": loader, "launch": self.find_launch(dest)}

    def find_launch(self, dest):
        args = glob.glob(str(dest / self.libs_glob / "unix_args.txt"))
        if args:
            return {"args_dir": str(Path(args[0]).parent.relative_to(dest))}
        jars = [j for j in glob.glob(str(dest / self.jar_glob)) if "installer" not in j]
        if jars:
            return {"jar": Path(jars[0]).name}
        raise RuntimeError("Konnte nach der Installation keine Startdatei finden")


class Forge(InstallerBased):
    label = "Forge"
    libs_glob = "libraries/net/minecraftforge/forge/*"
    jar_glob = "forge-*.jar"
    maven = "https://maven.minecraftforge.net/net/minecraftforge/forge"

    def mc_to_loader(self):
        root = ET.fromstring(http_get(f"{self.maven}/maven-metadata.xml"))
        result = {}
        for v in root.iter("version"):
            mc = v.text.split("-", 1)[0]
            result.setdefault(mc, []).append(v.text)
        # Pro MC-Version: neueste Forge-Version zuerst (Teil nach dem ersten '-')
        for mc, vs in result.items():
            vs.sort(key=lambda x: ver_key(x.split("-", 1)[1]), reverse=True)
        return result

    def installer_url(self, loader_version):
        return f"{self.maven}/{loader_version}/forge-{loader_version}-installer.jar"


class NeoForge(InstallerBased):
    label = "NeoForge"
    libs_glob = "libraries/net/neoforged/neoforge/*"
    jar_glob = "neoforge-*.jar"
    maven = "https://maven.neoforged.net/releases/net/neoforged/neoforge"

    @staticmethod
    def to_mc(version):
        """21.4.100 -> 1.21.4, 21.0.5 -> 1.21, 26.3.0.76 -> 26.3 (letzte Zahl = Build)."""
        parts = version.split("-")[0].split(".")
        if not all(p.isdigit() for p in parts):
            return None  # z.B. '0.25w14craftmine.3-beta'
        nums = [int(p) for p in parts]
        if nums[0] >= 26:
            mc = nums[:3] if len(nums) > 3 else nums[:2]
            return ".".join(map(str, mc[:2] if mc[2:] == [0] else mc))
        mc = "1." + str(nums[0]) + (f".{nums[1]}" if nums[1] else "")
        return mc

    def mc_to_loader(self):
        data = http_json("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge")
        result = {}
        for v in data["versions"]:
            mc = self.to_mc(v)
            if mc:
                result.setdefault(mc, []).append(v)
        for mc, vs in result.items():
            # stabile vor Beta-Builds, danach nach Build-Nummer
            vs.sort(key=lambda x: ("beta" not in x, ver_key(x)), reverse=True)
        return result

    def installer_url(self, loader_version):
        return f"{self.maven}/{loader_version}/neoforge-{loader_version}-installer.jar"


TYPES = {"vanilla": Vanilla(), "paper": Paper(), "fabric": Fabric(),
         "forge": Forge(), "neoforge": NeoForge()}


# --------------------------------------------------------------------------
# Verwaltung
# --------------------------------------------------------------------------

def home_dir(args):
    path = Path(args.home or os.environ.get("MCSM_HOME") or Path.home() / "minecraft-servers")
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_server(home, name):
    cfg = home / name / "server.json"
    if not cfg.exists():
        sys.exit(f"Server '{name}' existiert nicht. 'list' zeigt alle Server.")
    return home / name, json.loads(cfg.read_text(encoding="utf-8"))


def save_server(path, cfg):
    (path / "server.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_property(path, key, value):
    props = path / "server.properties"
    lines = props.read_text(encoding="utf-8").splitlines() if props.exists() else []
    lines = [l for l in lines if not l.startswith(f"{key}=")] + [f"{key}={value}"]
    props.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_eula(path, accept=False):
    eula = path / "eula.txt"
    if eula.exists() and "eula=true" in eula.read_text(encoding="utf-8"):
        return True
    if not accept:
        accept = (input(f"Akzeptierst du die Minecraft-EULA ({EULA_URL})? [j/N]: ")
                  .strip().lower() in ("j", "ja", "y", "yes"))
    if accept:
        eula.write_text(f"# {EULA_URL}\neula=true\n", encoding="utf-8")
    return accept


def cmd_versions(args):
    provider = TYPES[args.type]
    versions = provider.versions(args.all)
    print(f"{provider.label}: {len(versions)} Versionen (neueste zuerst)")
    for i in range(0, len(versions), 8):
        print("  " + "  ".join(f"{v:<12}" for v in versions[i:i + 8]).rstrip())


def cmd_create(args):
    home = home_dir(args)
    name = args.name or ask("Name des Servers")
    if not name or not NAME_RE.match(name):
        sys.exit("Ungültiger Name (erlaubt: Buchstaben, Zahlen, _ . -)")
    path = home / name
    if path.exists():
        sys.exit(f"Server '{name}' existiert bereits ({path})")

    stype = args.type or ask(f"Typ ({'/'.join(TYPES)})", "vanilla")
    if stype not in TYPES:
        sys.exit(f"Unbekannter Typ '{stype}'")
    provider = TYPES[stype]

    print("Hole Versionsliste ...")
    available = provider.versions(everything=args.all)
    mc = args.version or ask("Minecraft-Version (oder 'latest')", "latest")
    if mc == "latest":
        mc = available[0]
    if mc not in available:
        if args.all or mc not in provider.versions(everything=True):
            sys.exit(f"Version '{mc}' gibt es für {provider.label} nicht. "
                     f"Siehe: versions {stype}")
    print(f"Erstelle {provider.label}-Server '{name}' für Minecraft {mc}")

    java = args.java or pick_java(required_java(mc))
    print(f"  Java: {java} (Version {java_major(java)})")

    path.mkdir(parents=True)
    try:
        result = provider.prepare(mc, path, java)
    except BaseException:
        shutil.rmtree(path, ignore_errors=True)
        raise

    if provider.modded:
        (path / "mods").mkdir(exist_ok=True)
    set_property(path, "server-port", args.port)
    cfg = {"name": name, "type": stype, "mc_version": mc, "java": java,
           "memory": args.memory, "port": args.port,
           "created": datetime.now().isoformat(timespec="seconds"), **result}
    save_server(path, cfg)
    ensure_eula(path, args.accept_eula)
    print(f"\nFertig: {path}")
    if provider.modded:
        print(f"Mods kommen in: {path / 'mods'}")
    print(f"Starten mit: python {Path(sys.argv[0]).name} start {name}")


def cmd_list(args):
    home = home_dir(args)
    servers = sorted(p for p in home.iterdir() if (p / "server.json").exists())
    if not servers:
        print(f"Keine Server in {home}")
        return
    print(f"{'Name':<20}{'Typ':<10}{'MC-Version':<14}{'Port':<7}{'RAM'}")
    for p in servers:
        c = json.loads((p / "server.json").read_text(encoding="utf-8"))
        print(f"{c['name']:<20}{c['type']:<10}{c['mc_version']:<14}{c['port']:<7}{c['memory']}")


def cmd_info(args):
    path, cfg = load_server(home_dir(args), args.name)
    print(f"Ordner: {path}")
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    mods = path / "mods"
    if mods.is_dir():
        jars = sorted(j.name for j in mods.glob("*.jar"))
        print(f"  Mods ({len(jars)}): " + (", ".join(jars) if jars else "-"))


def build_command(cfg, path):
    mem = cfg["memory"]
    cmd = [cfg["java"], f"-Xms{mem}", f"-Xmx{mem}"]
    launch = cfg["launch"]
    if "jar" in launch:
        cmd += ["-jar", launch["jar"]]
    else:
        args_file = "win_args.txt" if os.name == "nt" else "unix_args.txt"
        cmd.append("@" + str(Path(launch["args_dir"]) / args_file))
    return cmd + ["nogui"]


def cmd_start(args):
    path, cfg = load_server(home_dir(args), args.name)
    if args.java:
        cfg["java"] = args.java
    if args.memory:
        cfg["memory"] = args.memory
    if not ensure_eula(path):
        sys.exit("Ohne EULA-Zustimmung kann der Server nicht starten.")
    cmd = build_command(cfg, path)
    print(f"Starte '{cfg['name']}': {' '.join(cmd)}\n(Beenden mit 'stop' in der Server-Konsole)")
    try:
        sys.exit(subprocess.run(cmd, cwd=path).returncode)
    except KeyboardInterrupt:
        pass


def cmd_set(args):
    path, cfg = load_server(home_dir(args), args.name)
    if args.memory:
        cfg["memory"] = args.memory
    if args.port:
        cfg["port"] = args.port
        set_property(path, "server-port", args.port)
    if args.java:
        cfg["java"] = args.java
    save_server(path, cfg)
    print("Gespeichert.")


def cmd_delete(args):
    path, cfg = load_server(home_dir(args), args.name)
    if not args.yes:
        if input(f"Server '{args.name}' samt Welt unwiderruflich löschen? [j/N]: ").strip().lower() not in ("j", "ja"):
            sys.exit("Abgebrochen.")
    shutil.rmtree(path)
    print("Gelöscht.")


def main():
    parser = argparse.ArgumentParser(description="Minecraft Server Manager",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=__doc__)
    parser.add_argument("--home", help="Ordner für alle Server (Standard: ~/minecraft-servers)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("versions", help="Verfügbare Minecraft-Versionen eines Typs anzeigen")
    p.add_argument("type", choices=TYPES)
    p.add_argument("--all", action="store_true", help="auch Snapshots / alte Betas")
    p.set_defaults(func=cmd_versions)

    p = sub.add_parser("create", help="Neuen Server erstellen (fehlende Angaben werden abgefragt)")
    p.add_argument("name", nargs="?")
    p.add_argument("type", nargs="?", choices=TYPES)
    p.add_argument("version", nargs="?", help="z.B. 1.20.1 oder 'latest'")
    p.add_argument("--memory", default="2G", help="Arbeitsspeicher, z.B. 4G (Standard: 2G)")
    p.add_argument("--port", type=int, default=25565)
    p.add_argument("--java", help="Pfad zur Java-Installation (sonst automatisch)")
    p.add_argument("--all", action="store_true", help="auch Snapshots / alte Betas erlauben")
    p.add_argument("--accept-eula", action="store_true", help=f"Minecraft-EULA akzeptieren ({EULA_URL})")
    p.set_defaults(func=cmd_create)

    sub.add_parser("list", help="Alle Server anzeigen").set_defaults(func=cmd_list)

    p = sub.add_parser("info", help="Details und Mods eines Servers")
    p.add_argument("name")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("start", help="Server im Vordergrund starten")
    p.add_argument("name")
    p.add_argument("--memory")
    p.add_argument("--java")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("set", help="RAM, Port oder Java ändern")
    p.add_argument("name")
    p.add_argument("--memory")
    p.add_argument("--port", type=int)
    p.add_argument("--java")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("delete", help="Server löschen")
    p.add_argument("name")
    p.add_argument("-y", "--yes", action="store_true")
    p.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    try:
        args.func(args)
    except (RuntimeError, OSError) as e:
        sys.exit(f"Fehler: {e}")


if __name__ == "__main__":
    main()
