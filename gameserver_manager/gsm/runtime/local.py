"""Lokale Runtime ohne Container (Fallback/Entwicklung): nutzt die auf dem Host installierte Java-Version."""
import glob
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from .base import LogStream, Runtime


def java_major(java):
    try:
        out = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'version "(\d+)(?:\.(\d+))?', out.stderr + out.stdout)
    if not m:
        return None
    major = int(m.group(1))
    return int(m.group(2)) if major == 1 and m.group(2) else major


def find_javas():
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(os.path.join(os.environ["JAVA_HOME"], "bin", "java"))
    if shutil.which("java"):
        candidates.append(shutil.which("java"))
    for pattern in ("/usr/lib/jvm/*/bin/java", "/opt/*/bin/java", "~/.sdkman/candidates/java/*/bin/java",
                    "/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java"):
        candidates.extend(glob.glob(os.path.expanduser(pattern)))
    javas, seen = {}, set()
    for c in candidates:
        real = os.path.realpath(c)
        if real not in seen and os.path.isfile(c):
            seen.add(real)
            if major := java_major(c):
                javas[c] = major
    return javas


def pick_java(needed):
    javas = find_javas()
    exact = [p for p, m in javas.items() if m == needed]
    if exact:
        return exact[0]
    higher = sorted((m, p) for p, m in javas.items() if m > needed)
    if higher:
        return higher[0][1]
    raise RuntimeError(f"Java {needed} wird benötigt, gefunden: {sorted(set(javas.values())) or 'keine'}. "
                       "Installiere Docker oder die passende Java-Version.")


class LocalRuntime(Runtime):
    name = "local"

    def __init__(self, settings=None):
        self._procs = {}

    def _meta(self, inst):
        return inst.data_dir / ".gsm"

    def _argv(self, spec_argv, java_major_needed):
        argv = list(spec_argv)
        if argv[0] == "java":
            argv[0] = pick_java(java_major_needed or 8)
        return argv

    def available(self):
        return True, "Lokale Java-Installation (ohne Container)"

    def start(self, inst, spec):
        meta = self._meta(inst)
        meta.mkdir(exist_ok=True)
        log = open(meta / "console.log", "ab")
        proc = subprocess.Popen(self._argv(spec.argv, spec.java_major), cwd=inst.data_dir, stdin=subprocess.PIPE,
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self._procs[inst.id] = proc
        (meta / "pid").write_text(str(proc.pid))

    def _pid(self, inst):
        proc = self._procs.get(inst.id)
        if proc is not None:
            return proc.pid if proc.poll() is None else None
        try:
            pid = int((self._meta(inst) / "pid").read_text())
            os.kill(pid, 0)
            return pid
        except (OSError, ValueError):
            return None

    def status(self, inst):
        return "running" if self._pid(inst) else "stopped"

    def send(self, inst, line):
        proc = self._procs.get(inst.id)
        if proc is None or proc.poll() is not None:
            raise RuntimeError("Konsole nur für Server verfügbar, die dieser Manager gestartet hat")
        proc.stdin.write((line.rstrip("\n") + "\n").encode())
        proc.stdin.flush()

    def kill(self, inst):
        if pid := self._pid(inst):
            os.killpg(os.getpgid(pid), signal.SIGKILL)

    def recent_logs(self, inst, lines=200):
        try:
            return (self._meta(inst) / "console.log").read_text(errors="replace").splitlines()[-lines:]
        except OSError:
            return []

    def log_stream(self, inst, tail=200):
        path = self._meta(inst) / "console.log"
        stop = threading.Event()

        def follow():
            for line in self.recent_logs(inst, tail):
                yield line
            try:
                with open(path, errors="replace") as f:
                    f.seek(0, os.SEEK_END)
                    while not stop.is_set():
                        line = f.readline()
                        if line:
                            yield line.rstrip("\n")
                        else:
                            time.sleep(0.3)
            except OSError:
                return

        return LogStream(follow(), stop.set)

    def run_java(self, inst, java_major, args, on_line):
        proc = subprocess.Popen([pick_java(java_major), *args], cwd=inst.data_dir, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, errors="replace")
        for line in proc.stdout:
            on_line(line.rstrip("\n"))
        return proc.wait()
