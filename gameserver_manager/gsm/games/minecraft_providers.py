"""Server-Typen für Minecraft: Vanilla, Paper, Fabric, Forge, NeoForge.

Jeder Provider kennt die verfügbaren Minecraft-Versionen und kann einen Server in einen
Ordner installieren. Installer (Forge/NeoForge) laufen über ctx.run_java, also im Container.
"""
import glob
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..util import download, http_get, http_json, ver_key

JAVA_CHOICES = (8, 17, 21, 25)   # als Container-Images verfügbare LTS-Versionen (Temurin)
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
    """Kleinste Java-Version aus JAVA_CHOICES, die diese Minecraft-Version braucht."""
    try:
        needed = mojang_version_info(mc).get("javaVersion", {}).get("majorVersion", 8)
    except RuntimeError:
        needed = 21
    return next((j for j in JAVA_CHOICES if j >= needed), JAVA_CHOICES[-1])


class Vanilla:
    id = "vanilla"
    label = "Vanilla"
    addons = None            # Ordnername für Mods/Plugins
    modrinth_loaders = ()

    def versions(self, everything=False):
        types = {"release", "snapshot", "old_beta", "old_alpha"} if everything else {"release"}
        return [v["id"] for v in mojang_manifest()["versions"] if v["type"] in types]

    def install(self, mc, dest, ctx, loader_version=None):
        server = mojang_version_info(mc).get("downloads", {}).get("server")
        if not server:
            raise RuntimeError(f"Für {mc} bietet Mojang keinen Server-Download an")
        download(server["url"], dest / "server.jar", server["sha1"], "sha1", ctx.log)
        return {"loader_version": None, "launch": {"jar": "server.jar"}}


class Paper(Vanilla):
    id = "paper"
    label = "Paper (Plugins)"
    addons = "plugins"
    modrinth_loaders = ("paper", "spigot", "bukkit")
    api = "https://fill.papermc.io/v3/projects/paper"

    def versions(self, everything=False):
        out = [v for group in http_json(self.api)["versions"].values() for v in group]
        return out if everything else [v for v in out if "-" not in v]

    def install(self, mc, dest, ctx, loader_version=None):
        build = http_json(f"{self.api}/versions/{mc}/builds/latest")
        dl = build["downloads"]["server:default"]
        download(dl["url"], dest / "server.jar", dl["checksums"]["sha256"], "sha256", ctx.log)
        return {"loader_version": str(build["id"]), "launch": {"jar": "server.jar"}}


class Fabric(Vanilla):
    id = "fabric"
    label = "Fabric (Mods)"
    addons = "mods"
    modrinth_loaders = ("fabric",)
    meta = "https://meta.fabricmc.net/v2/versions"

    def versions(self, everything=False):
        return [v["version"] for v in http_json(f"{self.meta}/game") if everything or v["stable"]]

    def install(self, mc, dest, ctx, loader_version=None):
        loader = loader_version or next(v["version"] for v in http_json(f"{self.meta}/loader") if v["stable"])
        installer = next(v["version"] for v in http_json(f"{self.meta}/installer") if v["stable"])
        download(f"{self.meta}/loader/{mc}/{loader}/{installer}/server/jar", dest / "server.jar", log=ctx.log)
        return {"loader_version": loader, "launch": {"jar": "server.jar"}}


class InstallerBased(Vanilla):
    """Forge/NeoForge: Installer laden und mit --installServer im Container ausführen."""
    addons = "mods"
    libs_glob = ""
    jar_glob = ""

    def mc_to_loader(self):
        """{mc_version: [loader_version, ...]} mit der neuesten Version zuerst."""
        raise NotImplementedError

    def installer_url(self, loader_version):
        raise NotImplementedError

    def full_version(self, mc, loader_version):
        """Version aus einer Modpack-Angabe (z.B. nur '47.2.0') in die Maven-Version umrechnen."""
        return loader_version

    def versions(self, everything=False):
        return sorted(self.mc_to_loader(), key=ver_key, reverse=True)

    def install(self, mc, dest, ctx, loader_version=None):
        known = self.mc_to_loader().get(mc)
        if not known:
            raise RuntimeError(f"{self.label} bietet keine Version für Minecraft {mc}")
        loader = self.full_version(mc, loader_version) if loader_version else known[0]
        if loader not in known:
            raise RuntimeError(f"{self.label}-Version {loader} gibt es nicht für Minecraft {mc}")
        installer = dest / "installer.jar"
        download(self.installer_url(loader), installer, log=ctx.log)
        ctx.log(f"Installiere {self.label} {loader} (das dauert einen Moment) ...")
        code = ctx.run_java(["-jar", "installer.jar", "--installServer"])
        if code != 0:
            raise RuntimeError(f"{self.label}-Installer ist fehlgeschlagen (Exit-Code {code})")
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
    id = "forge"
    label = "Forge (Mods)"
    modrinth_loaders = ("forge",)
    libs_glob = "libraries/net/minecraftforge/forge/*"
    jar_glob = "forge-*.jar"
    maven = "https://maven.minecraftforge.net/net/minecraftforge/forge"

    def mc_to_loader(self):
        root = ET.fromstring(http_get(f"{self.maven}/maven-metadata.xml"))
        result = {}
        for v in root.iter("version"):
            result.setdefault(v.text.split("-", 1)[0], []).append(v.text)
        for vs in result.values():
            vs.sort(key=lambda x: ver_key(x.split("-", 1)[1]), reverse=True)
        return result

    def full_version(self, mc, loader_version):
        return loader_version if loader_version.startswith(mc + "-") else f"{mc}-{loader_version}"

    def installer_url(self, loader_version):
        return f"{self.maven}/{loader_version}/forge-{loader_version}-installer.jar"


class NeoForge(InstallerBased):
    id = "neoforge"
    label = "NeoForge (Mods)"
    modrinth_loaders = ("neoforge",)
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
        return "1." + str(nums[0]) + (f".{nums[1]}" if nums[1] else "")

    def mc_to_loader(self):
        data = http_json("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge")
        result = {}
        for v in data["versions"]:
            mc = self.to_mc(v)
            if mc:
                result.setdefault(mc, []).append(v)
        for vs in result.values():
            vs.sort(key=lambda x: ("beta" not in x, ver_key(x)), reverse=True)   # stabil vor Beta
        return result

    def installer_url(self, loader_version):
        return f"{self.maven}/{loader_version}/neoforge-{loader_version}-installer.jar"


PROVIDERS = {p.id: p for p in (Vanilla(), Paper(), Fabric(), Forge(), NeoForge())}
