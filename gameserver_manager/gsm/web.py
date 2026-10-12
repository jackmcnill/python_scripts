"""Weboberfläche und JSON-API (Starlette)."""
import asyncio
import functools
import shutil
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from . import audit, config, modpacks
from .backup import BackupService
from .games import GAMES, get_game
from .instances import Busy, Manager
from .jobs import Jobs
from .runtime import get_runtime
from .users import LEVELS, UserError, UserStore

COOKIE = "gsm_session"
STATIC = Path(__file__).parent / "static"


class Context:
    def __init__(self):
        self.settings = config.load_settings()
        self.runtime = get_runtime(self.settings)
        self.manager = Manager(self.settings, self.runtime)
        self.jobs = Jobs()
        self.backups = BackupService(self.manager, self.jobs)
        self.users = UserStore()
        self.fails = {}   # (ip, benutzer) -> (Fehlversuche, gesperrt bis)

    def start_background(self):
        self.backups.start_scheduler()
        for inst in self.manager.list():
            if inst.auto_start and self.runtime.status(inst) != "running":
                self.jobs.start(f"Autostart: {inst.name}", lambda job, i=inst: self.manager.start(i, job.log))


def create_app(ctx=None):
    ctx = ctx or Context()
    secret = config.ensure_secret()
    reading = ("GET", "HEAD", "OPTIONS")

    # --- Anmeldung & Rechte --------------------------------------------------------
    def current_user(conn):
        parsed = config.parse_session_token(secret, conn.cookies.get(COOKIE, ""))
        if not parsed:
            return None
        user = ctx.users.get(parsed[0])
        if not user or user["disabled"] or user["tv"] != parsed[1]:
            return None
        return user

    def client_ip(conn):
        return conn.client.host if conn.client else "?"

    def same_origin(request):
        origin = request.headers.get("origin")
        if not origin:
            return True
        allowed = {request.headers.get("host"), request.headers.get("x-forwarded-host")}
        return urlparse(origin).netloc in allowed

    def api(need=None):
        """need: None (angemeldet), 'admin' oder ein Server-Recht ('viewer'/'operator'/'manager')."""
        def decorator(fn):
            @functools.wraps(fn)
            async def wrapper(request):
                user = current_user(request)
                if not user:
                    return JSONResponse({"error": "Nicht angemeldet"}, 401)
                if request.method not in reading and not same_origin(request):
                    return JSONResponse({"error": "Anfrage von fremder Herkunft"}, 403)
                if need == "admin" and user["role"] != "admin" or \
                        need in LEVELS and not UserStore.can(user, request.path_params.get("id", ""), need):
                    return JSONResponse({"error": "Keine Berechtigung"}, 403)
                request.state.user = user
                status = 200
                try:
                    result = await fn(request)
                    if isinstance(result, Response):
                        status = result.status_code
                    else:
                        result = JSONResponse(result)
                except Busy as exc:
                    status, result = 409, JSONResponse({"error": str(exc)}, 409)
                except KeyError as exc:
                    status, result = 404, JSONResponse({"error": str(exc.args[0])}, 404)
                except (ValueError, RuntimeError, OSError) as exc:     # UserError ist ein ValueError
                    status, result = 400, JSONResponse({"error": str(exc)}, 400)
                if request.method not in reading:
                    audit.log(user["username"], f"{request.method} {request.url.path}", client_ip(request), status)
                return result
            return wrapper
        return decorator

    def inst_of(request):
        return ctx.manager.get(request.path_params["id"])

    def inst_dict(inst, user):
        level = UserStore.level_for(user, inst.id)
        permission = next(name for name, rank in LEVELS.items() if rank == level)
        return {**inst.to_json(), **ctx.manager.status(inst), "permission": permission}

    def start_job(request, title, fn):
        return {"job": ctx.jobs.start(title, fn, owner=request.state.user["username"]).id}

    def session_info(user):
        return {"username": user["username"], "role": user["role"]}

    async def login(request):
        ip = client_ip(request)
        count, until = ctx.fails.get(ip, (0, 0))
        if until > time.time():
            return JSONResponse({"error": "Zu viele Fehlversuche, bitte später erneut versuchen"}, 429)
        if not same_origin(request):
            return JSONResponse({"error": "Anfrage von fremder Herkunft"}, 403)
        body = await request.json()
        user = await run_in_threadpool(ctx.users.verify, str(body.get("username", "")), str(body.get("password", "")))
        if not user:
            count += 1
            ctx.fails[ip] = (count, time.time() + min(900, 30 * 2 ** (count - 5)) if count >= 5 else 0)
            audit.log(str(body.get("username", ""))[:32], "Anmeldung fehlgeschlagen", ip)
            return JSONResponse({"error": "Benutzername oder Passwort falsch"}, 401)
        ctx.fails.pop(ip, None)
        audit.log(user["username"], "Angemeldet", ip)
        resp = JSONResponse(session_info(user))
        secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        resp.set_cookie(COOKIE, config.make_session_token(secret, user["username"], user["tv"]),
                        httponly=True, samesite="strict", secure=secure, max_age=7 * 24 * 3600)
        return resp

    async def logout(request):
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(COOKIE)
        return resp

    async def session(request):
        user = current_user(request)
        return JSONResponse({"authenticated": bool(user), "user": session_info(user) if user else None})

    @api()
    async def change_password(request):
        b = await request.json()
        await run_in_threadpool(ctx.users.change_own_password, request.state.user["username"],
                                str(b.get("current", "")), str(b.get("new", "")))
        resp = JSONResponse({"ok": True})
        user = ctx.users.get(request.state.user["username"])     # neue Sitzung, alte werden ungültig
        resp.set_cookie(COOKIE, config.make_session_token(secret, user["username"], user["tv"]),
                        httponly=True, samesite="strict", max_age=7 * 24 * 3600)
        return resp

    # --- Benutzerverwaltung (nur Admin) ---------------------------------------------------
    @api("admin")
    async def list_users(request):
        return ctx.users.list()

    @api("admin")
    async def create_user(request):
        b = await request.json()
        return await run_in_threadpool(ctx.users.create, str(b.get("username", "")), str(b.get("password", "")),
                                       b.get("role", "user"), b.get("servers"))

    @api("admin")
    async def update_user(request):
        b = await request.json()
        name = request.path_params["name"]
        if name.lower() == request.state.user["username"].lower() and (b.get("disabled") or b.get("role") == "user"):
            raise ValueError("Du kannst dir nicht selbst die Admin-Rechte entziehen oder dich sperren")
        return await run_in_threadpool(lambda: ctx.users.update(
            name, b.get("password"), b.get("role"), b.get("servers"), b.get("disabled")))

    @api("admin")
    async def delete_user(request):
        name = request.path_params["name"]
        if name.lower() == request.state.user["username"].lower():
            raise ValueError("Du kannst dich nicht selbst löschen")
        await run_in_threadpool(ctx.users.delete, name)
        return {"ok": True}

    @api("admin")
    async def audit_log(request):
        return audit.tail(int(request.query_params.get("limit", 200)))

    # --- System / Spiele -------------------------------------------------------------
    @api()
    async def system(request):
        ok, message = ctx.runtime.available()
        admin = request.state.user["role"] == "admin"
        usage = shutil.disk_usage(config.DATA_DIR if config.DATA_DIR.exists() else Path.home())
        info = {"runtime": ctx.runtime.name, "runtime_ok": ok}
        if admin:
            info.update(runtime_info=message, data_dir=str(config.DATA_DIR), disk_free_gb=round(usage.free / 1024 ** 3, 1))
        return info

    @api("admin")
    async def games(request):
        return [g.describe() for g in GAMES.values()]

    @api("admin")
    async def versions(request):
        game = get_game(request.path_params["game"])
        kind = request.query_params.get("kind", "")
        everything = request.query_params.get("all") == "1"
        return await run_in_threadpool(game.versions, kind, everything)

    # --- Jobs -------------------------------------------------------------------------
    @api()
    async def job(request):
        job = ctx.jobs.get(request.path_params["job"])
        user = request.state.user
        if job is None or (user["role"] != "admin" and job.owner != user["username"]):
            raise KeyError("Aufgabe nicht gefunden")
        return job.to_dict(int(request.query_params.get("since", 0)))

    # --- Server ------------------------------------------------------------------------
    @api()
    async def list_instances(request):
        user = request.state.user
        return await run_in_threadpool(lambda: [inst_dict(i, user) for i in ctx.manager.list()
                                                if UserStore.can(user, i.id, "viewer")])

    @api("admin")
    async def create_instance(request):
        b = await request.json()
        return start_job(request, f"Server erstellen: {b.get('name')}", lambda job: ctx.manager.create(
            b["name"], b.get("game", "minecraft"), b["kind"], b.get("version", "latest"),
            b.get("memory", "2G"), b.get("port", 25565), bool(b.get("accept_terms")), None, job.log).id)

    @api("viewer")
    async def get_instance(request):
        return inst_dict(inst_of(request), request.state.user)

    @api("manager")
    async def patch_instance(request):
        inst = inst_of(request)
        updated = await run_in_threadpool(ctx.manager.update, inst, await request.json())
        return inst_dict(updated, request.state.user)

    @api("admin")
    async def delete_instance(request):
        inst = inst_of(request)
        keep = (await request.json()).get("delete_backups", False) if await request.body() else False

        def run(job):
            ctx.manager.delete(inst, keep)
            ctx.users.forget_server(inst.id)
        return start_job(request, f"Server löschen: {inst.name}", run)

    def action(name):
        @api("operator")
        async def handler(request):
            inst = inst_of(request)
            fn = {"start": ctx.manager.start, "stop": ctx.manager.stop, "restart": ctx.manager.restart}[name]
            label = {"start": "starten", "stop": "stoppen", "restart": "neu starten"}[name]
            return start_job(request, f"{inst.name} {label}", lambda job: fn(inst, job.log))
        return handler

    @api("operator")
    async def kill(request):
        await run_in_threadpool(ctx.manager.kill, inst_of(request))
        return {"ok": True}

    # --- Konsole ------------------------------------------------------------------------
    async def console(ws: WebSocket):
        user = current_user(ws)
        if not user:
            await ws.close(4401)
            return
        origin = ws.headers.get("origin")
        if origin and urlparse(origin).netloc not in {ws.headers.get("host"), ws.headers.get("x-forwarded-host")}:
            await ws.close(4403)
            return
        if not UserStore.can(user, ws.path_params["id"], "viewer"):
            await ws.close(4403)
            return
        try:
            inst = ctx.manager.get(ws.path_params["id"])
        except KeyError:
            await ws.close(4404)
            return
        may_send = UserStore.can(user, inst.id, "operator")
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
                if not command:
                    continue
                if not may_send:
                    await ws.send_text("[Manager] Keine Berechtigung, Befehle zu senden")
                    continue
                audit.log(user["username"], f"Konsole {inst.id}: {command}", client_ip(ws))
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
    @api("viewer")
    async def addons(request):
        return await run_in_threadpool(ctx.manager.list_addons, inst_of(request))

    @api("manager")
    async def upload_addons(request):
        inst = inst_of(request)
        form = await request.form()
        saved = []
        for upload in form.getlist("files"):
            saved.append(await run_in_threadpool(ctx.manager.save_addon, inst, upload.filename, upload.file))
        return {"saved": saved}

    @api("manager")
    async def delete_addon(request):
        await run_in_threadpool(ctx.manager.remove_addon, inst_of(request), request.path_params["file"])
        return {"ok": True}

    @api("manager")
    async def toggle_addon(request):
        enabled = bool((await request.json()).get("enabled"))
        await run_in_threadpool(ctx.manager.toggle_addon, inst_of(request), request.path_params["file"], enabled)
        return {"ok": True}

    @api("manager")
    async def catalog_search(request):
        inst = inst_of(request)
        game = get_game(inst.game)
        return await run_in_threadpool(game.catalog_search, inst, request.query_params.get("q", ""),
                                       int(request.query_params.get("offset", 0)))

    @api("manager")
    async def catalog_install(request):
        inst = inst_of(request)
        project = (await request.json())["project"]
        game = get_game(inst.game)
        return start_job(request, f"Mod installieren: {project}", lambda job: game.catalog_install(inst, project, job.log))

    # --- Modpacks ---------------------------------------------------------------------------
    @api("admin")
    async def modpack_search(request):
        from .games import modrinth
        return await run_in_threadpool(modrinth.search, request.query_params.get("q", ""), (), None, "modpack",
                                       20, int(request.query_params.get("offset", 0)))

    @api("admin")
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
        return start_job(request, "Modpack importieren", run)

    # --- Backups --------------------------------------------------------------------------------
    @api("viewer")
    async def backups(request):
        return await run_in_threadpool(ctx.backups.list, inst_of(request))

    @api("operator")
    async def backup_create(request):
        inst = inst_of(request)
        return start_job(request, f"Backup: {inst.name}", lambda job: ctx.backups.create(inst, job.log))

    @api("manager")
    async def backup_restore(request):
        inst = inst_of(request)
        name = request.path_params["name"]
        return start_job(request, f"Wiederherstellen: {inst.name}", lambda job: ctx.backups.restore(inst, name, job.log))

    @api("manager")
    async def backup_delete(request):
        await run_in_threadpool(ctx.backups.delete, inst_of(request), request.path_params["name"])
        return {"ok": True}

    @api("manager")
    async def backup_download(request):
        path = ctx.backups.path(inst_of(request), request.path_params["name"])
        return FileResponse(path, filename=path.name)

    routes = [
        Route("/api/login", login, methods=["POST"]),
        Route("/api/logout", logout, methods=["POST"]),
        Route("/api/session", session),
        Route("/api/me/password", change_password, methods=["POST"]),
        Route("/api/users", list_users),
        Route("/api/users", create_user, methods=["POST"]),
        Route("/api/users/{name}", update_user, methods=["PATCH"]),
        Route("/api/users/{name}", delete_user, methods=["DELETE"]),
        Route("/api/audit", audit_log),
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
