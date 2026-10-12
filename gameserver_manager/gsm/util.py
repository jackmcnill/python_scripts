"""Allgemeine Hilfsfunktionen (HTTP, Downloads, Dateinamen, Größen)."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = "python_scripts/gameserver-manager/0.1 (github.com/jackmcnill/python_scripts)"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_json(url, timeout=60):
    return json.loads(http_get(url, timeout))


def download(url, dest, checksum=None, algo="sha1", log=None):
    """Lädt url nach dest, prüft optional die Prüfsumme und meldet den Fortschritt an log."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.new(algo)
    part = dest.with_name(dest.name + ".part")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(part, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0)
            done, next_report = 0, 25
            while chunk := resp.read(1 << 16):
                out.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if log and total and done * 100 // total >= next_report:
                    log(f"{dest.name}: {done * 100 // total}% ({done / 1048576:.1f}/{total / 1048576:.1f} MB)")
                    next_report += 25
        if checksum and h.hexdigest().lower() != checksum.lower():
            raise RuntimeError(f"Prüfsumme von {dest.name} stimmt nicht überein")
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)
    return dest


def ver_key(text):
    """Sortierschlüssel: '1.20.4' < '1.20.10' < '26.1'."""
    return tuple(int(n) for n in re.findall(r"\d+", text))


def parse_memory_mb(text):
    """'4G' -> 4096, '512M' -> 512."""
    m = re.fullmatch(r"(\d+)\s*([MmGg])", str(text).strip())
    if not m:
        raise ValueError(f"Ungültige Speicherangabe '{text}' (Beispiel: 2G oder 1536M)")
    value = int(m.group(1))
    return value * 1024 if m.group(2).lower() == "g" else value


def safe_filename(name):
    """Nur den Dateinamen ohne Pfadanteile; lehnt ungültige Namen ab."""
    name = Path(str(name).replace("\\", "/")).name
    if not name or name in (".", "..") or name.startswith(".") or "\x00" in name:
        raise ValueError(f"Ungültiger Dateiname: {name!r}")
    return name


def safe_join(base, relative):
    """base/relative, garantiert innerhalb von base (sonst ValueError)."""
    base = Path(base).resolve()
    target = (base / str(relative).replace("\\", "/")).resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"Pfad außerhalb des Serverordners: {relative}")
    return target
