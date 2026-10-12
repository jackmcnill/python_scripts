"""Modpacks (.mrpack) als neuen Server einspielen."""
import re
import shutil

from .games import modrinth


def import_modpack(manager, pack_path, name, memory, port, accept_terms, log):
    """Legt aus einer .mrpack-Datei einen neuen Minecraft-Server an."""
    index = modrinth.read_index(pack_path)
    kind, mc, loader_version = modrinth.pack_requirements(index)
    name = name or re.sub(r"[^a-z0-9_-]+", "-", index.get("name", "modpack").lower()).strip("-")[:32] or "modpack"
    log(f"Modpack '{index.get('name', name)}': Minecraft {mc}, {kind}" + (f" {loader_version}" if loader_version else ""))

    def prepare(inst):
        modrinth.install_pack_files(pack_path, inst.data_dir, log)
        manager.sync_port(inst)   # Port aus dem Pack darf den gewählten Port nicht überschreiben

    inst = manager.create(name, "minecraft", kind, mc, memory, port, accept_terms, loader_version, log, prepare)
    return inst.id


def import_from_modrinth(manager, project_ref, name, memory, port, accept_terms, log):
    pack = modrinth.fetch_modrinth_pack(modrinth.parse_project_ref(project_ref), log)
    try:
        return import_modpack(manager, pack, name, memory, port, accept_terms, log)
    finally:
        shutil.rmtree(pack.parent, ignore_errors=True)
