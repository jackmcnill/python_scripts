"""Docker-Runtime: jeder Server läuft in einem eigenen Container (Java-Version pro Server)."""
import os
import subprocess

from .base import LogStream, Runtime


def _run(args, **kwargs):
    return subprocess.run(["docker", *args], capture_output=True, text=True, **kwargs)


class DockerRuntime(Runtime):
    name = "docker"

    def __init__(self, settings):
        self.settings = settings

    # --- Hilfen -----------------------------------------------------------------
    def container(self, inst):
        return f"gsm-{inst.id}"

    def image(self, java_major):
        return self.settings["java_image"].format(java=java_major)

    def _user_args(self):
        if os.name != "nt" and hasattr(os, "getuid"):
            return ["--user", f"{os.getuid()}:{os.getgid()}"]
        return []

    def _ensure_image(self, image, on_line=None):
        if _run(["image", "inspect", image]).returncode == 0:
            return
        if on_line:
            on_line(f"Lade Container-Image {image} (nur beim ersten Mal) ...")
        result = _run(["pull", "-q", image])
        if result.returncode != 0:
            raise RuntimeError(f"Image {image} konnte nicht geladen werden: {result.stderr.strip()}")

    # --- Runtime ------------------------------------------------------------------
    def available(self):
        try:
            result = _run(["version", "--format", "{{.Server.Version}}"], timeout=15)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, f"Docker nicht gefunden: {exc}"
        if result.returncode != 0:
            return False, result.stderr.strip() or "Docker-Daemon nicht erreichbar"
        return True, f"Docker {result.stdout.strip()}"

    def start(self, inst, spec):
        image = self.image(spec.java_major)
        self._ensure_image(image)
        self.remove(inst)
        args = ["run", "-d", "-i", "--init", "--name", self.container(inst),
                "--label", "gsm.managed=true", "--label", f"gsm.instance={inst.id}",
                "--memory", f"{spec.memory_mb}m", "-w", "/data", "-v", f"{inst.data_dir.resolve()}:/data"]
        for proto in spec.protocols:
            args += ["-p", f"{spec.port}:{spec.port}/{proto}"]
        for key, value in spec.env.items():
            args += ["-e", f"{key}={value}"]
        args += self._user_args() + list(self.settings.get("docker_extra_args", []))
        result = _run(args + [image, *spec.argv])
        if result.returncode != 0:
            raise RuntimeError(f"Container konnte nicht starten: {result.stderr.strip()}")

    def status(self, inst):
        result = _run(["inspect", "-f", "{{.State.Running}}", self.container(inst)])
        return "running" if result.returncode == 0 and result.stdout.strip() == "true" else "stopped"

    def send(self, inst, line):
        result = subprocess.run(
            ["docker", "exec", "-i", self.container(inst), "sh", "-c", "cat > /proc/1/fd/0"],
            input=(line.rstrip("\n") + "\n").encode(), capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Befehl konnte nicht gesendet werden (läuft der Server?)")

    def kill(self, inst):
        _run(["kill", self.container(inst)])

    def remove(self, inst):
        _run(["rm", "-f", self.container(inst)])

    def recent_logs(self, inst, lines=200):
        result = _run(["logs", "--tail", str(lines), self.container(inst)])
        return (result.stdout + result.stderr).splitlines()

    def log_stream(self, inst, tail=200):
        proc = subprocess.Popen(["docker", "logs", "-f", "--tail", str(tail), self.container(inst)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        return LogStream((line.rstrip("\n") for line in proc.stdout), proc.terminate)

    def run_java(self, inst, java_major, args, on_line):
        image = self.image(java_major)
        self._ensure_image(image, on_line)
        cmd = ["docker", "run", "--rm", "-w", "/data", "-v", f"{inst.data_dir.resolve()}:/data",
               *self._user_args(), *self.settings.get("docker_extra_args", []), image, "java", *args]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        for line in proc.stdout:
            on_line(line.rstrip("\n"))
        return proc.wait()
