"""Konfiguration: Datenordner, Einstellungen, Passwort."""
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("GSM_DATA") or Path.home() / "gameserver-manager").expanduser()

DEFAULTS = {
    "runtime": "auto",                       # auto | docker | local
    "java_image": "eclipse-temurin:{java}-jre",
    "docker_extra_args": [],                 # z.B. ["--network", "host"]
}


def instances_dir():
    return DATA_DIR / "instances"


def backups_dir():
    return DATA_DIR / "backups"


def _settings_path():
    return DATA_DIR / "settings.json"


def load_settings():
    settings = dict(DEFAULTS)
    try:
        settings.update(json.loads(_settings_path().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    for env, key in (("GSM_RUNTIME", "runtime"), ("GSM_JAVA_IMAGE", "java_image")):
        if os.environ.get(env):
            settings[key] = os.environ[env]
    if os.environ.get("GSM_DOCKER_ARGS"):
        settings["docker_extra_args"] = os.environ["GSM_DOCKER_ARGS"].split()
    return settings


def save_settings(updates):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        current = json.loads(_settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        current = {}
    current.update(updates)
    path = _settings_path()
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    os.chmod(path, 0o600)
    return current


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def ensure_secret():
    """Stellt das Cookie-Secret sicher und gibt es zurück."""
    try:
        secret = json.loads(_settings_path().read_text(encoding="utf-8")).get("secret")
    except (OSError, ValueError):
        secret = None
    if not secret:
        secret = secrets.token_hex(32)
        save_settings({"secret": secret})
    return secret


def legacy_password_hash():
    """Passwort-Hash aus der Einzelnutzer-Version (wird beim ersten Start übernommen)."""
    try:
        return json.loads(_settings_path().read_text(encoding="utf-8")).get("password_hash")
    except (OSError, ValueError):
        return None


def make_session_token(secret, username, version, ttl=7 * 24 * 3600):
    body = f"{username}:{version}:{int(time.time()) + ttl}"
    return f"{body}:{hmac.new(secret.encode(), body.encode(), 'sha256').hexdigest()}"


def parse_session_token(secret, token):
    """-> (username, version) oder None, wenn ungültig/abgelaufen."""
    try:
        body, sig = token.rsplit(":", 1)
        username, version, expires = body.rsplit(":", 2)
        good = hmac.new(secret.encode(), body.encode(), "sha256").hexdigest()
        if hmac.compare_digest(sig, good) and int(expires) > time.time():
            return username, int(version)
    except (ValueError, AttributeError):
        pass
    return None
