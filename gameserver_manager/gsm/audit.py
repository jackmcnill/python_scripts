"""Protokoll aller Änderungen (wer hat wann was gemacht)."""
import json
import threading
import time

from . import config

_lock = threading.Lock()


def log(user, action, ip="", status=None):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "user": user, "ip": ip, "action": action}
    if status is not None:
        entry["status"] = status
    with _lock, open(config.DATA_DIR / "audit.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def tail(count=200):
    try:
        lines = (config.DATA_DIR / "audit.log").read_text(encoding="utf-8").splitlines()[-count:]
    except OSError:
        return []
    return [json.loads(l) for l in reversed(lines)]
