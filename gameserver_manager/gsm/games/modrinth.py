"""Modrinth-API: Mods suchen/installieren und .mrpack-Modpacks einspielen."""
import json
import re
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path

from ..util import download, http_json, safe_filename, safe_join

API = "https://api.modrinth.com/v2"
ALLOWED_HOSTS = {"cdn.modrinth.com", "github.com", "raw.githubusercontent.com", "gitlab.com"}
MAX_PACK_BYTES = 4 * 1024 ** 3


def _q(value):
    return urllib.parse.quote(json.dumps(value), safe="")


def search(query, loaders, mc_version=None, project_type="mod", limit=20, offset=0):
    facets = [[f"project_type:{project_type}"], ["server_side:required", "server_side:optional"]]
    if loaders and project_type == "mod":
        facets.append([f"categories:{loader}" for loader in loaders])
    if mc_version:
        facets.append([f"versions:{mc_version}"])
    url = (f"{API}/search?query={urllib.parse.quote(query or '')}&limit={limit}&offset={offset}"
           f"&facets={_q(facets)}")
    data = http_json(url)
    return {"total": data["total_hits"], "hits": [
        {"id": h["project_id"], "slug": h["slug"], "title": h["title"], "description": h["description"],
         "downloads": h["downloads"], "icon": h.get("icon_url"), "author": h.get("author")}
        for h in data["hits"]]}


def project_versions(project, loaders=None, mc_version=None):
    params = []
    if loaders:
        params.append(f"loaders={_q(list(loaders))}")
    if mc_version:
        params.append(f"game_versions={_q([mc_version])}")
    versions = http_json(f"{API}/project/{urllib.parse.quote(project)}/version?" + "&".join(params))
    # release vor beta vor alpha, innerhalb gleicher Stufe die neueste (API liefert neueste zuerst)
    order = {"release": 0, "beta": 1, "alpha": 2}
    return sorted(versions, key=lambda v: order.get(v["version_type"], 3))


def _primary_file(version):
    files = version["files"]
    return next((f for f in files if f.get("primary")), files[0])


def check_url(url):
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise RuntimeError(f"Download-Host nicht erlaubt: {host}")


def read_registry(data_dir):
    try:
        return json.loads((data_dir / ".gsm" / "addons.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_registry(data_dir, registry):
    path = data_dir / ".gsm" / "addons.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def install_project(data_dir, addon_dir, project, loaders, mc_version, log, _seen=None):
    """Installiert ein Projekt samt Pflicht-Abhängigkeiten. Gibt die installierten Dateinamen zurück."""
    seen = _seen if _seen is not None else set()
    registry = read_registry(data_dir)
    installed = []

    def install(project_ref, version_id=None):
        if project_ref in seen:
            return
        seen.add(project_ref)
        if any(e.get("project_id") == project_ref or e.get("slug") == project_ref for e in registry.values()):
            log(f"{project_ref}: bereits installiert")
            return
        if version_id:
            version = http_json(f"{API}/version/{version_id}")
        else:
            candidates = project_versions(project_ref, loaders, mc_version)
            if not candidates:
                raise RuntimeError(f"Keine passende Version von '{project_ref}' für "
                                   f"{'/'.join(loaders)} {mc_version}")
            version = candidates[0]
        file = _primary_file(version)
        check_url(file["url"])
        name = safe_filename(file["filename"])
        title = http_json(f"{API}/project/{version['project_id']}")
        log(f"Installiere {title['title']} ({version['version_number']})")
        download(file["url"], safe_join(data_dir, f"{addon_dir}/{name}"),
                 file["hashes"]["sha512"], "sha512", log)
        registry[name] = {"project_id": version["project_id"], "slug": title["slug"],
                          "title": title["title"], "version": version["version_number"]}
        installed.append(name)
        seen.add(version["project_id"])
        for dep in version.get("dependencies", []):
            if dep["dependency_type"] == "required" and (dep.get("project_id") or dep.get("version_id")):
                if dep.get("project_id"):
                    install(dep["project_id"], dep.get("version_id"))
                else:
                    install(http_json(f"{API}/version/{dep['version_id']}")["project_id"], dep["version_id"])

    install(project)
    write_registry(data_dir, registry)
    return installed


# --- Modpacks (.mrpack) ------------------------------------------------------

LOADER_KEYS = {"fabric-loader": "fabric", "forge": "forge", "neoforge": "neoforge", "quilt-loader": "quilt"}


def read_index(mrpack):
    with zipfile.ZipFile(mrpack) as z:
        if sum(i.file_size for i in z.infolist()) > MAX_PACK_BYTES:
            raise RuntimeError("Modpack ist entpackt zu groß")
        try:
            index = json.loads(z.read("modrinth.index.json"))
        except KeyError:
            raise RuntimeError("Keine gültige .mrpack-Datei (modrinth.index.json fehlt)") from None
    if index.get("game") != "minecraft":
        raise RuntimeError(f"Modpack ist für '{index.get('game')}', unterstützt wird nur Minecraft")
    return index


def pack_requirements(index):
    """-> (kind, mc_version, loader_version) aus den Abhängigkeiten des Packs."""
    deps = index.get("dependencies", {})
    mc = deps.get("minecraft")
    if not mc:
        raise RuntimeError("Modpack nennt keine Minecraft-Version")
    for key, kind in LOADER_KEYS.items():
        if key in deps:
            if kind == "quilt":
                raise RuntimeError("Quilt-Modpacks werden noch nicht unterstützt")
            return kind, mc, deps[key]
    return "vanilla", mc, None


def extract_overrides(mrpack, data_dir, log):
    with zipfile.ZipFile(mrpack) as z:
        for prefix in ("overrides/", "server-overrides/"):
            for info in z.infolist():
                if not info.filename.startswith(prefix) or info.is_dir():
                    continue
                target = safe_join(data_dir, info.filename[len(prefix):])
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
        log("Overrides entpackt")


def install_pack_files(mrpack, data_dir, log):
    index = read_index(mrpack)
    files = [f for f in index.get("files", []) if f.get("env", {}).get("server") != "unsupported"]
    log(f"{len(files)} Dateien werden geladen ({len(index.get('files', [])) - len(files)} nur für Clients übersprungen)")
    registry = read_registry(data_dir)
    for i, f in enumerate(files, 1):
        target = safe_join(data_dir, f["path"])
        url = f["downloads"][0]
        check_url(url)
        algo = "sha512" if "sha512" in f["hashes"] else "sha1"
        download(url, target, f["hashes"][algo], algo)
        registry.setdefault(target.name, {"title": target.name, "version": "", "source": "modpack"})
        log(f"[{i}/{len(files)}] {f['path']}")
    write_registry(data_dir, registry)
    extract_overrides(mrpack, data_dir, log)


def fetch_modrinth_pack(project, log):
    """Lädt die neueste Version eines Modrinth-Modpacks als .mrpack in eine Temp-Datei."""
    versions = project_versions(project)
    if not versions:
        raise RuntimeError(f"Modpack '{project}' hat keine Versionen")
    file = _primary_file(versions[0])
    check_url(file["url"])
    log(f"Lade Modpack {project} {versions[0]['version_number']}")
    tmp = Path(tempfile.mkdtemp(prefix="gsm-pack-")) / "pack.mrpack"
    download(file["url"], tmp, file["hashes"]["sha512"], "sha512", log)
    return tmp


def parse_project_ref(text):
    """Akzeptiert Slug, ID oder modrinth.com-URL."""
    text = text.strip()
    m = re.search(r"modrinth\.com/(?:modpack|mod|plugin)/([A-Za-z0-9_.-]+)", text)
    return m.group(1) if m else text
