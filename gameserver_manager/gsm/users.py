"""Benutzerverwaltung: Rollen, Rechte pro Server, Passwörter."""
import json
import os
import re
import secrets
import threading
import time

from . import config

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{2,32}$")
ROLES = ("admin", "user")
# Rechte pro Server (aufsteigend): viewer = ansehen, operator = bedienen, manager = verwalten
LEVELS = {"viewer": 1, "operator": 2, "manager": 3}
MIN_PASSWORD = 8


class UserError(ValueError):
    pass


def _check_password(password):
    if len(password or "") < MIN_PASSWORD:
        raise UserError(f"Das Passwort muss mindestens {MIN_PASSWORD} Zeichen lang sein")


def _check_servers(servers):
    servers = servers or {}
    for server, level in servers.items():
        if level not in LEVELS:
            raise UserError(f"Ungültiges Recht '{level}' (erlaubt: {', '.join(LEVELS)})")
    return dict(servers)


class UserStore:
    def __init__(self, path=None):
        self.path = path or (config.DATA_DIR / "users.json")
        self._lock = threading.RLock()

    # --- Speicherung --------------------------------------------------------------
    def _read(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write(self, users):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(users, indent=2), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(self.path)

    @staticmethod
    def public(user):
        return {k: user[k] for k in ("username", "role", "servers", "disabled", "created")}

    # --- Abfragen ---------------------------------------------------------------------
    def list(self):
        with self._lock:
            return [self.public(u) for u in sorted(self._read().values(), key=lambda u: u["username"].lower())]

    def get(self, username):
        return self._read().get(str(username).lower())

    def count_admins(self, users):
        return sum(1 for u in users.values() if u["role"] == "admin" and not u["disabled"])

    # --- Änderungen ---------------------------------------------------------------------
    def create(self, username, password, role="user", servers=None):
        if not NAME_RE.match(username or ""):
            raise UserError("Benutzername: 2-32 Zeichen aus Buchstaben, Zahlen, . _ -")
        if role not in ROLES:
            raise UserError(f"Rolle muss {' oder '.join(ROLES)} sein")
        _check_password(password)
        with self._lock:
            users = self._read()
            if username.lower() in users:
                raise UserError(f"Benutzer '{username}' existiert bereits")
            users[username.lower()] = {"username": username, "password_hash": config.hash_password(password),
                                       "role": role, "servers": _check_servers(servers), "disabled": False,
                                       "tv": 0, "created": time.strftime("%Y-%m-%dT%H:%M:%S")}
            self._write(users)
            return self.public(users[username.lower()])

    def update(self, username, password=None, role=None, servers=None, disabled=None):
        with self._lock:
            users = self._read()
            user = users.get(username.lower())
            if not user:
                raise KeyError(f"Benutzer '{username}' existiert nicht")
            if password is not None:
                _check_password(password)
                user["password_hash"] = config.hash_password(password)
                user["tv"] += 1                       # meldet bestehende Sitzungen ab
            if role is not None:
                if role not in ROLES:
                    raise UserError(f"Rolle muss {' oder '.join(ROLES)} sein")
                user["role"] = role
            if servers is not None:
                user["servers"] = _check_servers(servers)
            if disabled is not None:
                user["disabled"] = bool(disabled)
                user["tv"] += 1
            if self.count_admins(users) == 0:
                raise UserError("Es muss mindestens ein aktiver Administrator übrig bleiben")
            self._write(users)
            return self.public(user)

    def delete(self, username):
        with self._lock:
            users = self._read()
            if username.lower() not in users:
                raise KeyError(f"Benutzer '{username}' existiert nicht")
            del users[username.lower()]
            if self.count_admins(users) == 0:
                raise UserError("Es muss mindestens ein aktiver Administrator übrig bleiben")
            self._write(users)

    def forget_server(self, server_id):
        """Entzieht allen Benutzern die Rechte an einem gelöschten Server."""
        with self._lock:
            users = self._read()
            for user in users.values():
                user["servers"].pop(server_id, None)
            self._write(users)

    # --- Anmeldung -------------------------------------------------------------------------
    def verify(self, username, password):
        """-> Benutzer (intern) oder None. Rechnet auch bei unbekanntem Namen, gegen Timing-Angriffe."""
        user = self.get(username or "")
        stored = user["password_hash"] if user else config.hash_password("dummy-password")
        ok = config.check_password(password or "", stored)
        return user if user and ok and not user["disabled"] else None

    def change_own_password(self, username, current, new):
        if not self.verify(username, current):
            raise UserError("Aktuelles Passwort ist falsch")
        return self.update(username, password=new)

    def ensure_admin(self):
        """Legt beim ersten Start einen Administrator an. Gibt (name, passwort) zurück, wenn neu erzeugt."""
        with self._lock:
            if self._read():
                return None
            legacy = config.legacy_password_hash()
            password = os.environ.get("GSM_PASSWORD") or secrets.token_urlsafe(12)
            users = {"admin": {"username": "admin", "password_hash": legacy or config.hash_password(password),
                               "role": "admin", "servers": {}, "disabled": False, "tv": 0,
                               "created": time.strftime("%Y-%m-%dT%H:%M:%S")}}
            self._write(users)
            return ("admin", None if legacy else password)

    # --- Rechte ------------------------------------------------------------------------------
    @staticmethod
    def level_for(user, server_id):
        """Höchstes Recht des Benutzers für einen Server: 0 (keins) bis 3."""
        if user["role"] == "admin":
            return LEVELS["manager"]
        return LEVELS.get(user["servers"].get(server_id), 0)

    @staticmethod
    def can(user, server_id, needed):
        return UserStore.level_for(user, server_id) >= LEVELS[needed]
