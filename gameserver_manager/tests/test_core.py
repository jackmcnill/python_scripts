import io
import json
import tarfile
import time
import unittest
import zipfile
from pathlib import Path

import helpers  # noqa: F401  (setzt GSM_DATA)
from helpers import FakeRuntime, make_instance, make_manager

from gsm import config
from gsm.backup import BackupService
from gsm.games import modrinth
from gsm.games.minecraft import Minecraft
from gsm.games.minecraft_providers import Forge, NeoForge
from gsm.instances import Busy
from gsm.jobs import Jobs
from gsm.runtime.docker import DockerRuntime
from gsm.users import UserError, UserStore
from gsm.util import parse_memory_mb, safe_filename, safe_join, ver_key


class UtilTests(unittest.TestCase):
    def test_memory(self):
        self.assertEqual(parse_memory_mb("4G"), 4096)
        self.assertEqual(parse_memory_mb("512m"), 512)
        with self.assertRaises(ValueError):
            parse_memory_mb("viel")

    def test_filenames(self):
        self.assertEqual(safe_filename("../../etc/evil.jar"), "evil.jar")
        for bad in ("", "..", ".hidden"):
            with self.assertRaises(ValueError):
                safe_filename(bad)

    def test_safe_join(self):
        base = Path(config.DATA_DIR)
        self.assertEqual(safe_join(base, "mods/a.jar"), (base / "mods/a.jar").resolve())
        with self.assertRaises(ValueError):
            safe_join(base, "../x")
        with self.assertRaises(ValueError):
            safe_join(base, "/etc/passwd")

    def test_ver_key(self):
        self.assertLess(ver_key("1.20.4"), ver_key("1.20.10"))
        self.assertLess(ver_key("1.21.11"), ver_key("26.1"))


class ProviderTests(unittest.TestCase):
    def test_neoforge_mapping(self):
        to_mc = NeoForge.to_mc
        self.assertEqual(to_mc("21.4.100"), "1.21.4")
        self.assertEqual(to_mc("21.0.5"), "1.21")
        self.assertEqual(to_mc("20.2.3-beta"), "1.20.2")
        self.assertEqual(to_mc("26.3.0.76"), "26.3")
        self.assertEqual(to_mc("26.1.2.5"), "26.1.2")
        self.assertIsNone(to_mc("0.25w14craftmine.3-beta"))

    def test_forge_full_version(self):
        self.assertEqual(Forge().full_version("1.20.1", "47.2.0"), "1.20.1-47.2.0")
        self.assertEqual(Forge().full_version("1.20.1", "1.20.1-47.2.0"), "1.20.1-47.2.0")

    def test_launch_spec(self):
        manager = make_manager()
        inst = make_instance(manager)
        spec = Minecraft().launch_spec(inst)
        self.assertEqual(spec.argv, ["java", "-Xms2G", "-Xmx2G", "-jar", "server.jar", "nogui"])
        self.assertEqual(spec.memory_mb, 2048 + 768)
        inst.launch = {"args_dir": "libraries/net/minecraftforge/forge/1.20.1-47.2.0"}
        argv = Minecraft().launch_spec(inst).argv
        self.assertIn("@libraries/net/minecraftforge/forge/1.20.1-47.2.0/unix_args.txt", argv)


def make_pack(path, files=(), overrides=None, deps=None):
    index = {"formatVersion": 1, "game": "minecraft", "name": "Test Pack", "files": list(files),
             "dependencies": deps or {"minecraft": "1.20.1", "fabric-loader": "0.15.7"}}
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("modrinth.index.json", json.dumps(index))
        for name, data in (overrides or {}).items():
            z.writestr(name, data)
    return path


class ModpackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(config.DATA_DIR) / "packs"
        self.tmp.mkdir(exist_ok=True)

    def test_requirements(self):
        pack = make_pack(self.tmp / "a.mrpack")
        self.assertEqual(modrinth.pack_requirements(modrinth.read_index(pack)), ("fabric", "1.20.1", "0.15.7"))
        pack = make_pack(self.tmp / "b.mrpack", deps={"minecraft": "1.20.1", "forge": "47.2.0"})
        self.assertEqual(modrinth.pack_requirements(modrinth.read_index(pack))[0], "forge")
        pack = make_pack(self.tmp / "c.mrpack", deps={"minecraft": "1.20.1", "quilt-loader": "0.2"})
        with self.assertRaises(RuntimeError):
            modrinth.pack_requirements(modrinth.read_index(pack))

    def test_overrides_extracted_and_traversal_blocked(self):
        target = self.tmp / "data1"
        target.mkdir(exist_ok=True)
        pack = make_pack(self.tmp / "d.mrpack", overrides={"overrides/config/a.toml": "x", "server-overrides/b.txt": "y"})
        modrinth.extract_overrides(pack, target, lambda m: None)
        self.assertEqual((target / "config/a.toml").read_text(), "x")
        self.assertEqual((target / "b.txt").read_text(), "y")
        evil = make_pack(self.tmp / "e.mrpack", overrides={"overrides/../../evil.txt": "z"})
        with self.assertRaises(ValueError):
            modrinth.extract_overrides(evil, target, lambda m: None)

    def test_pack_file_path_traversal_and_host_allowlist(self):
        target = self.tmp / "data2"
        target.mkdir(exist_ok=True)
        bad_path = make_pack(self.tmp / "f.mrpack", files=[{"path": "../x.jar", "hashes": {"sha1": "0"},
                                                               "downloads": ["https://cdn.modrinth.com/x.jar"]}])
        with self.assertRaises(ValueError):
            modrinth.install_pack_files(bad_path, target, lambda m: None)
        bad_host = make_pack(self.tmp / "g.mrpack", files=[{"path": "mods/x.jar", "hashes": {"sha1": "0"},
                                                               "downloads": ["https://evil.example.com/x.jar"]}])
        with self.assertRaises(RuntimeError):
            modrinth.install_pack_files(bad_host, target, lambda m: None)

    def test_client_only_files_skipped(self):
        target = self.tmp / "data3"
        target.mkdir(exist_ok=True)
        pack = make_pack(self.tmp / "h.mrpack", files=[{"path": "mods/c.jar", "hashes": {"sha1": "0"},
                         "downloads": ["https://evil.example.com/c.jar"], "env": {"client": "required", "server": "unsupported"}}])
        modrinth.install_pack_files(pack, target, lambda m: None)   # darf nichts laden
        self.assertFalse((target / "mods/c.jar").exists())

    def test_project_ref(self):
        self.assertEqual(modrinth.parse_project_ref("https://modrinth.com/modpack/fabulously-optimized/versions"),
                         "fabulously-optimized")
        self.assertEqual(modrinth.parse_project_ref(" slug "), "slug")


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()
        self.manager = make_manager(self.runtime)
        self.inst = make_instance(self.manager, "bk")
        self.backups = BackupService(self.manager, Jobs())

    def names(self, scope=None):
        with tarfile.open(self.backups.folder("bk") / self.backups.list(self.inst)[0]["name"]) as t:
            return t.getnames()

    def test_full_backup_excludes_logs(self):
        self.backups.create(self.inst, lambda m: None, scope="full")
        names = self.names()
        self.assertIn("world/level.dat", names)
        self.assertFalse(any(n.startswith("logs") for n in names))

    def test_world_scope(self):
        (self.inst.data_dir / "mods").mkdir(exist_ok=True)
        (self.inst.data_dir / "mods" / "a.jar").write_bytes(b"PK")
        self.backups.create(self.inst, lambda m: None, scope="world")
        names = self.names()
        self.assertIn("world/level.dat", names)
        self.assertIn("server.properties", names)
        self.assertFalse(any(n.startswith("mods") for n in names))

    def test_running_server_is_flushed_and_resumed(self):
        self.runtime.state = "running"
        self.backups.create(self.inst, lambda m: None)
        self.assertEqual(self.runtime.sent, ["save-off", "save-all flush", "save-on"])

    def test_prune_and_restore(self):
        self.inst.backup["keep"] = 2
        for i in range(3):
            time.sleep(1.1)
            self.backups.create(self.inst, lambda m: None)
        listed = self.backups.list(self.inst)
        self.assertEqual(len(listed), 2)
        (self.inst.data_dir / "world" / "level.dat").write_bytes(b"kaputt")
        (self.inst.data_dir / "extra.txt").write_text("weg")
        time.sleep(1.1)
        self.backups.restore(self.inst, listed[0]["name"], lambda m: None)
        self.assertEqual((self.inst.data_dir / "world" / "level.dat").read_bytes(), b"level")
        self.assertFalse((self.inst.data_dir / "extra.txt").exists())
        self.assertGreaterEqual(len(self.backups.list(self.inst)), 2)   # Sicherung vor dem Restore bleibt erhalten

    def test_restore_refused_while_running(self):
        self.backups.create(self.inst, lambda m: None)
        self.runtime.state = "running"
        with self.assertRaises(RuntimeError):
            self.backups.restore(self.inst, self.backups.list(self.inst)[0]["name"], lambda m: None)

    def test_names_validated(self):
        for bad in ("../x.tar.gz", "bk-1.tar.gz", "other-20260101-000000-full.tar.gz"):
            with self.assertRaises((ValueError, KeyError)):
                self.backups.path(self.inst, bad)

    def test_schedule_due(self):
        inst = make_instance(self.manager, "sched")                # frischer Server ohne Backups
        self.assertFalse(self.backups.due(inst))                   # nicht aktiviert
        inst.backup.update(enabled=True, interval_hours=1)
        self.assertTrue(self.backups.due(inst))                    # noch nie gesichert
        self.backups.create(inst, lambda m: None)
        self.assertFalse(self.backups.due(inst))
        self.assertTrue(self.backups.due(inst, now=time.time() + 3601))

    def test_tick_runs_due_backups(self):
        inst = make_instance(self.manager, "ticked")
        inst.backup.update(enabled=True, interval_hours=1)
        self.manager.save(inst)
        self.backups.tick()
        for _ in range(50):
            if self.backups.list(inst):
                break
            time.sleep(0.1)
        self.assertEqual(len(self.backups.list(inst)), 1)
        self.backups.tick()   # direkt danach nicht erneut fällig
        time.sleep(0.3)
        self.assertEqual(len(self.backups.list(inst)), 1)

    def test_busy_blocks_parallel_operations(self):
        with self.manager.busy(self.inst, "x"):
            with self.assertRaises(Busy):
                self.backups.create(self.inst, lambda m: None)


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = make_manager()
        self.inst = make_instance(self.manager, "mg", kind="fabric")
        (self.inst.data_dir / "mods").mkdir(exist_ok=True)

    def jar(self):
        buf = io.BytesIO()
        zipfile.ZipFile(buf, "w").writestr("x", "y")
        return io.BytesIO(buf.getvalue())

    def test_addons(self):
        self.assertEqual(self.manager.save_addon(self.inst, "../../a.jar", self.jar()), "a.jar")
        with self.assertRaises(ValueError):
            self.manager.save_addon(self.inst, "b.jar", io.BytesIO(b"kein zip"))
        with self.assertRaises(ValueError):
            self.manager.save_addon(self.inst, "c.txt", self.jar())
        self.manager.toggle_addon(self.inst, "a.jar", False)
        self.assertEqual([(a["file"], a["enabled"]) for a in self.manager.list_addons(self.inst)],
                         [("a.jar.disabled", False)])
        self.manager.toggle_addon(self.inst, "a.jar.disabled", True)
        self.manager.remove_addon(self.inst, "a.jar")
        self.assertEqual(self.manager.list_addons(self.inst), [])

    def test_vanilla_has_no_addons(self):
        vanilla = make_instance(self.manager, "van", kind="vanilla")
        with self.assertRaises(ValueError):
            self.manager.list_addons(vanilla)

    def test_update_validation_and_port_sync(self):
        self.manager.update(self.inst, {"memory": "4G", "port": 25570, "backup": {"enabled": True, "interval_hours": 6}})
        again = self.manager.get("mg")
        self.assertEqual((again.memory, again.port, again.backup["interval_hours"]), ("4G", 25570, 6))
        self.assertIn("server-port=25570", (self.inst.data_dir / "server.properties").read_text())
        with self.assertRaises(ValueError):
            self.manager.update(self.inst, {"port": 80})
        other = make_instance(self.manager, "other")
        with self.assertRaises(ValueError):
            self.manager.update(other, {"port": 25570})   # Port schon vergeben

    def test_get_rejects_bad_ids(self):
        for bad in ("../mg", "nope", "A B"):
            with self.assertRaises(KeyError):
                self.manager.get(bad)

    def test_start_stop(self):
        self.manager.start(self.inst)
        self.assertEqual(self.manager.status(self.inst)["state"], "running")
        with self.assertRaises(RuntimeError):
            self.manager.start(self.inst)
        self.manager.stop(self.inst)
        self.assertEqual(self.manager.status(self.inst)["state"], "stopped")


class DockerCommandTests(unittest.TestCase):
    def test_run_command(self):
        calls = []

        class Result:
            returncode, stdout, stderr = 0, "", ""

        import gsm.runtime.docker as dk
        original = dk._run
        dk._run = lambda args, **kw: (calls.append(args), Result())[1]
        try:
            manager = make_manager()
            inst = make_instance(manager, "dk")
            runtime = DockerRuntime({"java_image": "eclipse-temurin:{java}-jre", "docker_extra_args": ["--cpus", "2"]})
            runtime.start(inst, Minecraft().launch_spec(inst))
        finally:
            dk._run = original
        run = next(c for c in calls if c[0] == "run")
        joined = " ".join(run)
        self.assertIn("--name gsm-dk", joined)
        self.assertIn("-p 25565:25565/tcp", joined)
        self.assertIn("--memory 2816m", joined)
        self.assertIn("--cpus 2", joined)
        self.assertIn("eclipse-temurin:21-jre java -Xms2G -Xmx2G -jar server.jar nogui", joined)
        self.assertNotIn("--restart", joined)


class ConfigTests(unittest.TestCase):
    def test_password_and_token(self):
        stored = config.hash_password("geheim123")
        self.assertTrue(config.check_password("geheim123", stored))
        self.assertFalse(config.check_password("falsch", stored))
        token = config.make_session_token("s3cret", "anna", 4)
        self.assertEqual(config.parse_session_token("s3cret", token), ("anna", 4))
        self.assertIsNone(config.parse_session_token("other", token))
        self.assertIsNone(config.parse_session_token("s3cret", config.make_session_token("s3cret", "anna", 4, ttl=-5)))
        self.assertIsNone(config.parse_session_token("s3cret", "müll"))
        forged = token.replace("anna", "admin")
        self.assertIsNone(config.parse_session_token("s3cret", forged))


class UserStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = UserStore(Path(config.DATA_DIR) / f"users-{self.id().split('.')[-1]}.json")
        self.store.create("root", "passwort-root", "admin")

    def test_create_and_verify(self):
        self.store.create("Anna", "geheim-123", "user", {"srv": "operator"})
        self.assertIsNotNone(self.store.verify("anna", "geheim-123"))          # Name ohne Beachtung der Schreibweise
        self.assertIsNone(self.store.verify("anna", "falsch"))
        self.assertIsNone(self.store.verify("niemand", "geheim-123"))
        self.assertNotIn("password_hash", self.store.list()[0])

    def test_validation(self):
        for args in (("x", "passwort-123"), ("gut", "kurz"), ("bad name", "passwort-123")):
            with self.assertRaises(UserError):
                self.store.create(*args)
        with self.assertRaises(UserError):
            self.store.create("root", "passwort-root")                         # doppelt
        with self.assertRaises(UserError):
            self.store.create("neu", "passwort-123", "user", {"srv": "god"})   # ungültiges Recht

    def test_levels(self):
        user = self.store.create("bob", "passwort-123", "user", {"a": "operator"})
        user = self.store.get("bob")
        self.assertTrue(UserStore.can(user, "a", "viewer"))
        self.assertTrue(UserStore.can(user, "a", "operator"))
        self.assertFalse(UserStore.can(user, "a", "manager"))
        self.assertFalse(UserStore.can(user, "b", "viewer"))                   # fremder Server
        self.assertTrue(UserStore.can(self.store.get("root"), "irgendwas", "manager"))

    def test_last_admin_protected(self):
        with self.assertRaises(UserError):
            self.store.delete("root")
        with self.assertRaises(UserError):
            self.store.update("root", role="user")
        with self.assertRaises(UserError):
            self.store.update("root", disabled=True)
        self.store.create("zweiter", "passwort-123", "admin")
        self.store.delete("root")

    def test_password_change_invalidates_sessions(self):
        before = self.store.get("root")["tv"]
        self.store.change_own_password("root", "passwort-root", "neues-passwort")
        self.assertEqual(self.store.get("root")["tv"], before + 1)
        self.assertIsNone(self.store.verify("root", "passwort-root"))
        with self.assertRaises(UserError):
            self.store.change_own_password("root", "falsch", "nochmal-neu-123")

    def test_disabled_cannot_login(self):
        self.store.create("sperr", "passwort-123", "user")
        self.store.update("sperr", disabled=True)
        self.assertIsNone(self.store.verify("sperr", "passwort-123"))

    def test_forget_server(self):
        self.store.create("cc", "passwort-123", "user", {"a": "viewer", "b": "manager"})
        self.store.forget_server("a")
        self.assertEqual(self.store.get("cc")["servers"], {"b": "manager"})


if __name__ == "__main__":
    unittest.main()
