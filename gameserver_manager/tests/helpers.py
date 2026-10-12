import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GSM_DATA"] = tempfile.mkdtemp(prefix="gsm-test-")

from gsm import config  # noqa: E402
from gsm.instances import Instance, Manager  # noqa: E402
from gsm.runtime.base import Runtime  # noqa: E402


class FakeRuntime(Runtime):
    name = "fake"

    def __init__(self):
        self.state, self.sent, self.started = "stopped", [], []
        self.logs = []

    def available(self):
        return True, "fake"

    def start(self, inst, spec):
        self.state = "running"
        self.started.append(spec)

    def status(self, inst):
        return self.state

    def send(self, inst, line):
        self.sent.append(line)
        if line == "save-all flush":
            self.logs.append("[Server thread/INFO]: Saved the game")
        if line == self.sent[0] and line == "stop":
            self.state = "stopped"

    def kill(self, inst):
        self.state = "stopped"

    def recent_logs(self, inst, lines=200):
        return self.logs[-lines:]

    def log_stream(self, inst, tail=200):
        raise NotImplementedError

    def run_java(self, inst, java_major, args, on_line):
        return 0


def make_manager(runtime=None):
    config.DATA_DIR = Path(os.environ["GSM_DATA"])
    return Manager(config.load_settings(), runtime or FakeRuntime())


def make_instance(manager, inst_id="test", kind="vanilla"):
    root = config.instances_dir() / inst_id
    (root / "data" / "world").mkdir(parents=True, exist_ok=True)
    (root / "data" / "world" / "level.dat").write_bytes(b"level")
    (root / "data" / "logs").mkdir(exist_ok=True)
    (root / "data" / "logs" / "latest.log").write_text("log")
    (root / "data" / "server.properties").write_text("server-port=25565\n")
    inst = Instance(id=inst_id, name=inst_id, game="minecraft", kind=kind, version="1.21.4", java_major=21,
                    launch={"jar": "server.jar"}, root=root)
    manager.save(inst)
    return inst
