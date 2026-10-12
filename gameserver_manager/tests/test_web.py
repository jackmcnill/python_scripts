import json
import threading
import time
import unittest
import urllib.error
import urllib.request

import helpers  # noqa: F401
from helpers import FakeRuntime, make_instance, make_manager

import uvicorn

from gsm import config
from gsm.backup import BackupService
from gsm.jobs import Jobs
from gsm.web import Context, create_app


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.ensure_auth()
        config.set_password("testpasswort")
        cls.ctx = Context.__new__(Context)
        cls.ctx.settings = config.load_settings()
        cls.ctx.runtime = FakeRuntime()
        cls.ctx.manager = make_manager(cls.ctx.runtime)
        cls.ctx.jobs = Jobs()
        cls.ctx.backups = BackupService(cls.ctx.manager, cls.ctx.jobs)
        cls.ctx.fails = {}
        make_instance(cls.ctx.manager, "web")
        cls.server = uvicorn.Server(uvicorn.Config(create_app(cls.ctx), host="127.0.0.1", port=18765, log_level="error"))
        threading.Thread(target=cls.server.run, daemon=True).start()
        for _ in range(50):
            if cls.server.started:
                break
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True

    def call(self, method, path, body=None, cookie=None):
        req = urllib.request.Request("http://127.0.0.1:18765/api" + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"Cookie": cookie} if cookie else {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read()), r.headers.get("Set-Cookie")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read()), None

    def login(self):
        status, _, cookie = self.call("POST", "/login", {"password": "testpasswort"})
        self.assertEqual(status, 200)
        return cookie.split(";")[0]

    def test_requires_login(self):
        for path in ("/instances", "/system", "/instances/web/backups", "/games"):
            self.assertEqual(self.call("GET", path)[0], 401, path)
        self.assertEqual(self.call("POST", "/instances/web/start")[0], 401)
        self.assertEqual(self.call("GET", "/instances", cookie="gsm_session=9999999999.abc")[0], 401)

    def test_wrong_password(self):
        self.assertEqual(self.call("POST", "/login", {"password": "falsch"})[0], 401)

    def test_instances_and_lifecycle(self):
        cookie = self.login()
        status, items, _ = self.call("GET", "/instances", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn("web", [i["id"] for i in items])
        self.assertEqual(self.call("GET", "/instances/nope", cookie=cookie)[0], 404)
        _, started, _ = self.call("POST", "/instances/web/start", cookie=cookie)
        for _ in range(20):
            _, job, _ = self.call("GET", f"/jobs/{started['job']}", cookie=cookie)
            if job["state"] != "running":
                break
            time.sleep(0.1)
        self.assertEqual(job["state"], "done")
        self.assertEqual(self.call("GET", "/instances/web", cookie=cookie)[1]["state"], "running")

    def test_validation_errors(self):
        cookie = self.login()
        status, body, _ = self.call("PATCH", "/instances/web", {"memory": "abc"}, cookie)
        self.assertEqual(status, 400)
        self.assertIn("Speicher", body["error"])

    def test_static_index_served(self):
        with urllib.request.urlopen("http://127.0.0.1:18765/") as r:
            self.assertIn("Game Server Manager", r.read().decode())


if __name__ == "__main__":
    unittest.main()
