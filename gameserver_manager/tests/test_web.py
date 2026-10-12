import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from pathlib import Path

import helpers  # noqa: F401
from helpers import FakeRuntime, make_instance, make_manager

import uvicorn

from gsm import config
from gsm.backup import BackupService
from gsm.jobs import Jobs
from gsm.users import UserStore
from gsm.web import Context, create_app


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.ensure_secret()
        cls.ctx = Context.__new__(Context)
        cls.ctx.settings = config.load_settings()
        cls.ctx.runtime = FakeRuntime()
        cls.ctx.manager = make_manager(cls.ctx.runtime)
        cls.ctx.jobs = Jobs()
        cls.ctx.backups = BackupService(cls.ctx.manager, cls.ctx.jobs)
        cls.ctx.users = UserStore(Path(config.DATA_DIR) / "users-web.json")
        cls.ctx.users.create("chef", "chef-passwort", "admin")
        cls.ctx.users.create("viewer", "viewer-passwort", "user", {"web": "viewer"})
        cls.ctx.users.create("op", "operator-passwort", "user", {"web": "operator"})
        cls.ctx.users.create("mgr", "manager-passwort", "user", {"web": "manager"})
        cls.ctx.users.create("fremd", "fremd-passwort1", "user", {"other": "manager"})
        cls.ctx.fails = {}
        for name, port in (("web", 25801), ("geheim", 25802)):    # eigene Ports, damit sich die Server nicht beißen
            inst = make_instance(cls.ctx.manager, name)
            inst.port = port
            cls.ctx.manager.save(inst)
        cls.server = uvicorn.Server(uvicorn.Config(create_app(cls.ctx), host="127.0.0.1", port=18765, log_level="error"))
        threading.Thread(target=cls.server.run, daemon=True).start()
        for _ in range(50):
            if cls.server.started:
                break
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True

    def call(self, method, path, body=None, cookie=None, headers=None):
        req = urllib.request.Request("http://127.0.0.1:18765/api" + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"Cookie": cookie} if cookie else {}),
                                              **(headers or {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read()), r.headers.get("Set-Cookie")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read()), None

    def login(self, user, password):
        status, _, cookie = self.call("POST", "/login", {"username": user, "password": password})
        self.assertEqual(status, 200, user)
        return cookie.split(";")[0]

    def wait_job(self, job_id, cookie):
        for _ in range(50):
            _, job, _ = self.call("GET", f"/jobs/{job_id}", cookie=cookie)
            if job["state"] != "running":
                return job
            time.sleep(0.1)

    def test_requires_login(self):
        for path in ("/instances", "/system", "/instances/web/backups", "/games", "/users", "/audit"):
            self.assertEqual(self.call("GET", path)[0], 401, path)
        self.assertEqual(self.call("POST", "/instances/web/start")[0], 401)
        self.assertEqual(self.call("GET", "/instances", cookie="gsm_session=chef:0:9999999999:abc")[0], 401)

    def test_wrong_login(self):
        self.assertEqual(self.call("POST", "/login", {"username": "chef", "password": "falsch"})[0], 401)
        self.assertEqual(self.call("POST", "/login", {"username": "gibtsnicht", "password": "egal-egal-1"})[0], 401)

    def test_server_visibility(self):
        admin = self.login("chef", "chef-passwort")
        self.assertEqual({i["id"] for i in self.call("GET", "/instances", cookie=admin)[1]} >= {"web", "geheim"}, True)
        viewer = self.login("viewer", "viewer-passwort")
        items = self.call("GET", "/instances", cookie=viewer)[1]
        self.assertEqual([(i["id"], i["permission"]) for i in items], [("web", "viewer")])
        self.assertEqual(self.call("GET", "/instances/geheim", cookie=viewer)[0], 403)
        self.assertEqual(self.call("GET", "/instances/geheim/backups", cookie=viewer)[0], 403)

    def test_permission_levels(self):
        viewer = self.login("viewer", "viewer-passwort")
        op = self.login("op", "operator-passwort")
        mgr = self.login("mgr", "manager-passwort")
        admin = self.login("chef", "chef-passwort")
        # ansehen
        self.assertEqual(self.call("GET", "/instances/web/backups", cookie=viewer)[0], 200)
        self.assertEqual(self.call("GET", "/instances/web/addons", cookie=viewer)[0], 400)   # vanilla: keine Addons, aber erlaubt
        # bedienen
        self.assertEqual(self.call("POST", "/instances/web/start", cookie=viewer)[0], 403)
        status, started, _ = self.call("POST", "/instances/web/start", cookie=op)
        self.assertEqual(status, 200)
        self.assertEqual(self.wait_job(started["job"], op)["state"], "done")
        self.assertEqual(self.call("PATCH", "/instances/web", {"memory": "3G"}, cookie=op)[0], 403)
        self.assertEqual(self.call("POST", "/instances/web/backups/x-20260101-000000-full.tar.gz/restore", cookie=op)[0], 403)
        # verwalten
        self.assertEqual(self.call("PATCH", "/instances/web", {"memory": "3G"}, cookie=mgr)[0], 200)
        self.assertEqual(self.call("PATCH", "/instances/web", {"memory": "2G"}, cookie=mgr)[0], 200)
        self.assertEqual(self.call("DELETE", "/instances/web", cookie=mgr)[0], 403)            # Löschen nur Admin
        self.assertEqual(self.call("POST", "/instances", {"name": "neu", "kind": "vanilla"}, cookie=mgr)[0], 403)
        self.assertEqual(self.call("GET", "/users", cookie=mgr)[0], 403)
        self.assertEqual(self.call("GET", "/audit", cookie=mgr)[0], 403)
        self.assertEqual(self.call("POST", "/modpacks/import", cookie=mgr)[0], 403)
        self.assertEqual(self.call("GET", "/users", cookie=admin)[0], 200)
        self.runtime_reset()

    def runtime_reset(self):
        self.ctx.runtime.state = "stopped"

    def test_jobs_only_visible_to_owner(self):
        op = self.login("op", "operator-passwort")
        admin = self.login("chef", "chef-passwort")
        other = self.login("mgr", "manager-passwort")
        _, started, _ = self.call("POST", "/instances/web/restart", cookie=op)
        self.assertEqual(self.call("GET", f"/jobs/{started['job']}", cookie=other)[0], 404)
        self.assertEqual(self.call("GET", f"/jobs/{started['job']}", cookie=admin)[0], 200)
        self.wait_job(started["job"], op)
        self.runtime_reset()

    def test_foreign_origin_rejected(self):
        admin = self.login("chef", "chef-passwort")
        status, body, _ = self.call("PATCH", "/instances/web", {"memory": "2G"}, cookie=admin,
                                    headers={"Origin": "https://boese.example.com"})
        self.assertEqual(status, 403)
        self.assertEqual(self.call("POST", "/login", {"username": "chef", "password": "chef-passwort"},
                                   headers={"Origin": "https://boese.example.com"})[0], 403)

    def test_user_management_and_session_invalidation(self):
        admin = self.login("chef", "chef-passwort")
        self.assertEqual(self.call("POST", "/users", {"username": "neu", "password": "neues-passwort", "role": "user",
                                                       "servers": {"web": "viewer"}}, cookie=admin)[0], 200)
        neu = self.login("neu", "neues-passwort")
        self.assertEqual(self.call("GET", "/instances", cookie=neu)[0], 200)
        self.assertEqual(self.call("PATCH", "/users/neu", {"password": "ganz-anderes-pw"}, cookie=admin)[0], 200)
        self.assertEqual(self.call("GET", "/instances", cookie=neu)[0], 401)           # alte Sitzung ungültig
        self.assertEqual(self.call("PATCH", "/users/neu", {"disabled": True}, cookie=admin)[0], 200)
        self.assertEqual(self.call("POST", "/login", {"username": "neu", "password": "ganz-anderes-pw"})[0], 401)
        self.assertEqual(self.call("DELETE", "/users/neu", cookie=admin)[0], 200)
        self.assertEqual(self.call("DELETE", "/users/chef", cookie=admin)[0], 400)      # nicht selbst löschen
        self.assertEqual(self.call("PATCH", "/users/chef", {"role": "user"}, cookie=admin)[0], 400)

    def test_own_password_change(self):
        cookie = self.login("fremd", "fremd-passwort1")
        self.assertEqual(self.call("POST", "/me/password", {"current": "falsch", "new": "irgendwas-123"}, cookie=cookie)[0], 400)
        status, _, new_cookie = self.call("POST", "/me/password", {"current": "fremd-passwort1", "new": "fremd-passwort2"}, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(self.call("GET", "/instances", cookie=cookie)[0], 401)
        self.assertEqual(self.call("GET", "/instances", cookie=new_cookie.split(";")[0])[0], 200)

    def test_audit_log_records_changes(self):
        admin = self.login("chef", "chef-passwort")
        self.call("PATCH", "/instances/web", {"memory": "2G"}, cookie=admin)
        entries = self.call("GET", "/audit", cookie=admin)[1]
        self.assertTrue(any(e["user"] == "chef" and e["action"] == "PATCH /api/instances/web" for e in entries))
        self.assertFalse(any("passwort" in json.dumps(e) for e in entries))

    def test_validation_errors(self):
        cookie = self.login("chef", "chef-passwort")
        status, body, _ = self.call("PATCH", "/instances/web", {"memory": "abc"}, cookie)
        self.assertEqual(status, 400)
        self.assertIn("Speicher", body["error"])

    def test_static_index_served(self):
        with urllib.request.urlopen("http://127.0.0.1:18765/") as r:
            self.assertIn("Game Server Manager", r.read().decode())


if __name__ == "__main__":
    unittest.main()
