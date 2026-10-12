"""Hintergrundaufgaben (Installation, Backup, Import) mit Log für die Weboberfläche."""
import threading
import time
import uuid


class Job:
    def __init__(self, title):
        self.id = uuid.uuid4().hex[:12]
        self.title = title
        self.state = "running"          # running | done | error
        self.lines = []
        self.error = None
        self.result = None
        self.started = time.time()
        self._lock = threading.Lock()

    def log(self, message):
        with self._lock:
            self.lines.append(str(message))
            del self.lines[:-500]

    def to_dict(self, since=0):
        with self._lock:
            return {"id": self.id, "title": self.title, "state": self.state, "error": self.error,
                    "result": self.result, "lines": self.lines[since:], "total": len(self.lines)}


class Jobs:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    def start(self, title, fn):
        """Führt fn(job) in einem Thread aus. fn darf ein Ergebnis zurückgeben."""
        job = Job(title)
        with self._lock:
            self._jobs[job.id] = job
            for old in sorted(self._jobs.values(), key=lambda j: j.started)[:-50]:
                if old.state != "running":
                    self._jobs.pop(old.id, None)

        def run():
            try:
                job.result = fn(job)
                job.state = "done"
            except Exception as exc:  # noqa: BLE001 - jede Ursache soll im Job-Log landen
                job.error = str(exc) or exc.__class__.__name__
                job.log(f"FEHLER: {job.error}")
                job.state = "error"

        threading.Thread(target=run, daemon=True, name=f"job-{job.id}").start()
        return job

    def get(self, job_id):
        return self._jobs.get(job_id)
