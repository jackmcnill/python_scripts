"""Weboberfläche und JSON-API (Starlette)."""
import asyncio
import functools
import shutil
import tempfile
import threading
import time
from pathlib import Path

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from . import config, modpacks
from .backup import BackupService
from .games import GAMES, get_game
from .instances import Busy, Manager
from .jobs import Jobs
from .runtime import get_runtime

COOKIE = "gsm_session"
STATIC = Path(__file__).parent / "static"


class Context:
    def __init__(self):
        self.settings = config.load_settings()
        self.runtime = get_runtime(self.settings)
        self.manager = Manager(self.settings, self.runtime)
        self.jobs = Jobs()
        self.backups = BackupService(self.manager, self.jobs)
        self.fails = {}   # ip -> (Fehlversuche, gesperrt bis)

    def start_background(self):
        self.backups.start_scheduler()
        for inst in self.manager.list():
            if inst.auto_start and self.runtime.status(inst) != "running":
                self.jobs.start(f"Autostart: {inst.name}", lambda job, i=inst: self.manager.start(i, job.log))


def create_app(ctx=None):
    ctx = ctx or Context()
    _, secret = config.auth_state()

    def authed(conn):
        return config.check_session_token(secret, conn.cookies.get(COOKIE, ""))

    def api(fn):
        @functools.wraps(fn)
        async def wrapper(request):
            if not authed(request):
                return JSONResponse({"error": "Nicht angemeldet"}, 401)
            try:
                result = await fn(request)
            except Busy as exc:
                return JSONResponse({"error": str(exc)}, 409)
            except KeyError as exc:
                return JSONResponse({"error": str(exc.args[0])}, 404)
            except (ValueError, RuntimeError, OSError) as exc:
                return JSONResponse({"error": str(exc)}, 400)
            return result if isinstance(result, Response) else JSONResponse(result)
        return wrapper

    def inst_of(request):
        return ctx.manager.get(request.path_params["id"])

    def inst_dict(inst):
        return {**inst.to_json(), **ctx.manager.status(inst)}

    def start_job(title, fn):
        return {"job": ctx.jobs.start(title, fn).id}

    # --- Anmeldung ---------------------------------------------------------------
    async def login(request):
        ip = request.client.host if request.client else "?"
        count, until = ctx.fails.get(ip, (0, 0))
        if until > time.time():
            return JSONResponse({"error": "Zu viele Versuche, bitte kurz warten"}, 429)
        body = await request.json()
        stored, _ = config.auth_state()
        if not config.check_password(str(body.get("password", "")), stored):
            count += 1
            ctx.fails[ip] = (count, time.time() + 30 if count >= 5 else 0)
            return JSONResponse({"error": "Falsches Passwort"}, 401)
        ctx.fails.pop(ip, None)
        resp = JSONResponse({"ok": True})
        resp.set_cookie(COOKIE, config.make_session_token(secret), httponly=True, samesite="strict",
                        max_age=7 * 24 * 3600)
        return resp

    async def logout(request):
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(COOKIE)
        return resp

    async def session(request):
        return JSONResponse({"authenticated": authed(request)})

    # --- System / Spiele -------------------------------------------------------------
    @api
    async def system(request):
        ok, message = ctx.runtime.available()
        usage = shutil.disk_usage(config.DATA_DIR if config.DATA_DIR.exists() else Path.home())
        return {"runtime": ctx.runtime.name, "runtime_ok": ok, "runtime_info": message,
                "data_dir": str(config.DATA_DIR), "disk_free_gb": round(usage.free / 1024 ** 3, 1)}

    @api
    async def games(request):
        return [g.describe() for g in GAMES.values()]

    @api
    async def versions(request):
        game = get_game(request.path_params["game"])
        kind = request.query_params.get("kind", "")
        everything = request.query_params.get("all") == "1"
        return await run_in_threadpool(game.versions, kind, everything)

    # --- Jobs -------------------------------------------------------------------------
    @api
    async def job(request):
        job = ctx.jobs.get(request.path_params["job"])
        if job is None:
            raise KeyError("Aufgabe nicht gefunden")
        return job.to_dict(int(request.query_params.get("since", 0)))

    # --- Server ------------------------------------------------------------------------
    @api
    async def list_instances(request):
        return await run_in_threadpool(lambda: [inst_dict(i) for i in ctx.manager.list()])

    @api
    async def create_instance(request):
        b = await request.json()
        return start_job(f"Server erstellen: {b.get('name')}", lambda job: ctx.manager.create(
            b["name"], b.get("game", "minecraft"), b["kind"], b.get("version", "latest"),
            b.get("memory", "2G"), b.get("port", 25565), bool(b.get("accept_terms")), None, job.log).id)

    @api
    async def get_instance(request):
        return inst_dict(inst_of(request))

    @api
    async def patch_instance(request):
        inst = inst_of(request)
        return inst_dict(await run_in_threadpool(ctx.manager.update, inst, await request.json()))

    @api
    async def delete_instance(request):
        inst = inst_of(request)
        keep = (await request.json()).get("delete_backups", False) if await request.body() else False
        return start_job(f"Server löschen: {inst.name}", lambda job: ctx.manager.delete(inst, keep))

    def action(name):
        @api
        async def handler(request):
            inst = inst_of(request)
            fn = {"start": ctx.manager.start, "stop": ctx.manager.stop, "restart": ctx.manager.restart}[name]
            label = {"start": "starten", "stop": "stoppen", "restart": "neu starten"}[name]
            return start_job(f"{inst.name} {label}", lambda job: fn(inst, job.log))
        return handler

    @api
    async def kill(request):
        await run_in_threadpool(ctx.manager.kill, inst_of(request))
        return {"ok": True}

    # --- Konsole ------------------------------------------------------------------------
    async def console(ws: WebSocket):
        if not authed(ws):
            await ws.close(4401)
            return
        try:
            inst = ctx.manager.get(ws.path_params["id"])
        except KeyError:
            await ws.close(4404)
            return
        await ws.accept()
        loop, queue = asyncio.get_running_loop(), asyncio.Queue()
        stream = ctx.runtime.log_stream(inst)

        def pump():
            for line in stream:
                loop.call_soon_threadsafe(queue.put_nowait, line)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=pump, daemon=True).start()

        async def sender():
            while (line := await queue.get()) is not None:
                await ws.send_text(line)

        task = asyncio.create_task(sender())
        try:
            while True:
                command = (await ws.receive_text()).strip()
                if command:
                    try:
                        await run_in_threadpool(ctx.manager.send, inst, command)
                    except RuntimeError as exc:
                        await ws.send_text(f"[Manager] {exc}")
        except WebSocketDisconnect:
            pass
        finally:
            stream.close()
            task.cancel()

    # --- Mods / Plugins -------------------------------------------------------------------
    @api
    async def addons(request):
        return await run_in_threadpool(ctx.manager.list_addons, inst_of(request))

    @api
    async def upload_addons(request):
        inst = inst_of(request)
        form = await request.form()
        saved = []
        for upload in form.getlist("files"):
            saved.append(await run_in_threadpool(ctx.manager.save_addon, inst, upload.filename, upload.file))
        return {"saved": saved}

    @api
    async def delete_addon(request):
        await run_in_threadpool(ctx.manager.remove_addon, inst_of(request), request.path_params["file"])
        return {"ok": True}

    @api
    async def toggle_addon(request):
        enabled = bool((await request.json()).get("enabled"))
        await run_in_threadpool(ctx.manager.toggle_addon, inst_of(request), request.path_params["file"], enabled)
        return {"ok": True}

    @api
    async def catalog_search(request):
        inst = inst_of(request)
        game = get_game(inst.game)
        return await run_in_threadpool(game.catalog_search, inst, request.query_params.get("q", ""),
                                       int(request.query_params.get("offset", 0)))

    @api
    async def catalog_install(request):
        inst = inst_of(request)
        project = (await request.json())["project"]
        game = get_game(inst.game)
        return start_job(f"Mod installieren: {project}", lambda job: game.catalog_install(inst, project, job.log))

    # --- Modpacks ---------------------------------------------------------------------------
    @api
    async def modpack_search(request):
        from .games import modrinth
        return await run_in_threadpool(modrinth.search, request.query_params.get("q", ""), (), None, "modpack",
                                       20, int(request.query_params.get("offset", 0)))

    @api
    async def modpack_import(request):
        form = await request.form()
        name, memory = form.get("name", ""), form.get("memory") or "2G"
        port, terms = int(form.get("port") or 25565), form.get("accept_terms") in ("1", "true", "on")
        upload, ref = form.get("file"), (form.get("modrinth") or "").strip()
        if not upload and not ref:
            raise ValueError("Bitte eine .mrpack-Datei hochladen oder ein Modrinth-Modpack angeben")
        if upload:
            tmp = Path(tempfile.mkdtemp(prefix="gsm-upload-"))
            path = tmp / "pack.mrpack"
            with open(path, "wb") as f:
                shutil.copyfileobj(upload.file, f)

            def run(job):
                try:
                    return modpacks.import_modpack(ctx.manager, path, name, memory, port, terms, job.log)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)
        else:
            def run(job):
                return modpacks.import_from_modrinth(ctx.manager, ref, name, memory, port, terms, job.log)
        return start_job("Modpack importieren", run)

    # --- Backups --------------------------------------------------------------------------------
    @api
    async def backups(request):
        return await run_in_threadpool(ctx.backups.list, inst_of(request))

    @api
    async def backup_create(request):
        inst = inst_of(request)
        return start_job(f"Backup: {inst.name}", lambda job: ctx.backups.create(inst, job.log))

    @api
    async def backup_restore(request):
        inst = inst_of(request)
        name = request.path_params["name"]
        return start_job(f"Wiederherstellen: {inst.name}", lambda job: ctx.backups.restore(inst, name, job.log))

    @api
    async def backup_delete(request):
        await run_in_threadpool(ctx.backups.delete, inst_of(request), request.path_params["name"])
        return {"ok": True}

    @api
    async def backup_download(request):
        path = ctx.backups.path(inst_of(request), request.path_params["name"])
        return FileResponse(path, filename=path.name)

    routes = [
        Route("/api/login", login, methods=["POST"]),
        Route("/api/logout", logout, methods=["POST"]),
        Route("/api/session", session),
        Route("/api/system", system),
        Route("/api/games", games),
        Route("/api/games/{game}/versions", versions),
        Route("/api/jobs/{job}", job),
        Route("/api/instances", list_instances),
        Route("/api/instances", create_instance, methods=["POST"]),
        Route("/api/instances/{id}", get_instance),
        Route("/api/instances/{id}", patch_instance, methods=["PATCH"]),
        Route("/api/instances/{id}", delete_instance, methods=["DELETE"]),
        Route("/api/instances/{id}/start", action("start"), methods=["POST"]),
        Route("/api/instances/{id}/stop", action("stop"), methods=["POST"]),
        Route("/api/instances/{id}/restart", action("restart"), methods=["POST"]),
        Route("/api/instances/{id}/kill", kill, methods=["POST"]),
        WebSocketRoute("/api/instances/{id}/console", console),
        Route("/api/instances/{id}/addons", addons),
        Route("/api/instances/{id}/addons", upload_addons, methods=["POST"]),
        Route("/api/instances/{id}/addons/{file}", delete_addon, methods=["DELETE"]),
        Route("/api/instances/{id}/addons/{file}", toggle_addon, methods=["PATCH"]),
        Route("/api/instances/{id}/catalog", catalog_search),
        Route("/api/instances/{id}/catalog", catalog_install, methods=["POST"]),
        Route("/api/modpacks", modpack_search),
        Route("/api/modpacks/import", modpack_import, methods=["POST"]),
        Route("/api/instances/{id}/backups", backups),
        Route("/api/instances/{id}/backups", backup_create, methods=["POST"]),
        Route("/api/instances/{id}/backups/{name}/restore", backup_restore, methods=["POST"]),
        Route("/api/instances/{id}/backups/{name}", backup_delete, methods=["DELETE"]),
        Route("/api/instances/{id}/backups/{name}/download", backup_download),
        Mount("/", StaticFiles(directory=STATIC, html=True)),
    ]
    app = Starlette(routes=routes)
    app.state.ctx = ctx
    return app
