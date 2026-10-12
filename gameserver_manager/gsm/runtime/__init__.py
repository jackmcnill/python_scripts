from .docker import DockerRuntime
from .local import LocalRuntime


def get_runtime(settings):
    """Wählt die Runtime: 'docker', 'local' oder 'auto' (Docker, wenn erreichbar)."""
    choice = settings.get("runtime", "auto")
    if choice == "local":
        return LocalRuntime(settings)
    docker = DockerRuntime(settings)
    ok, message = docker.available()
    if ok or choice == "docker":
        return docker
    print(f"Hinweis: {message}. Nutze lokale Java-Installation ohne Container.")
    return LocalRuntime(settings)
