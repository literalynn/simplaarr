
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from .settings import load_app, save_app, load_bitrates, save_bitrates
from .db import get_stats, list_recent, list_jobs, retry_failed, purge_failed, delete_pending, upsert_job
from .gpu import system_summary, list_gpus
from .logs import tail as tail_logs
from .scan import scan_once, mirrored_dst, VIDEO_EXT
from .auth import require_session, validate_admin_credentials, is_setup_needed, setup_admin

router = APIRouter(prefix="/api")

@router.post("/login")
def login(body: dict, request: Request):
    username = (body or {}).get("username") or ""
    password = (body or {}).get("password") or ""
    if not validate_admin_credentials(username, password):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="invalid_credentials")
    request.session["user"] = {"username": username}
    return {"ok": True, "user": {"username": username}}

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@router.get("/auth/status")
def auth_status(request: Request):
    user = (request.session or {}).get("user") if hasattr(request, "session") else None
    return {"setup_needed": is_setup_needed(), "authenticated": bool(user), "user": user}

@router.post("/auth/setup")
def auth_setup(body: dict):
    if not is_setup_needed():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="already_setup")
    u = (body or {}).get("username") or ""
    p = (body or {}).get("password") or ""
    if not u or not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="missing_fields")
    setup_admin(u, p)
    return {"ok": True}

@router.post("/auth/change")
def auth_change(body: dict, _: bool = Depends(require_session)):
    u = (body or {}).get("username")
    p = (body or {}).get("password")
    from .auth import setup_admin
    # Si les champs sont manquants, conserver ceux existants
    cfg = load_app()
    cur_u = (cfg.get("admin",{}).get("username") or "")
    new_u = u or cur_u
    if not p and not u:
        return {"ok": True, "user": {"username": cur_u}}
    setup_admin(new_u, p or "")
    return {"ok": True, "user": {"username": new_u}}

@router.get("/stats")
def stats(_: bool = Depends(require_session)):
    return get_stats()

@router.get("/gpus")
def gpus(_: bool = Depends(require_session)):
    return {"gpus": list_gpus()}

@router.get("/system")
def sys(_: bool = Depends(require_session)):
    return system_summary()

@router.get("/jobs")
def jobs(status: str | None = Query(default=None), limit: int = Query(default=200, ge=1, le=1000), _: bool = Depends(require_session)):
    return {"recent": list_jobs(limit=limit, status=status)}

@router.post("/scan")
def scan(_: bool = Depends(require_session)):
    return scan_once()

@router.post("/control/pause")
def pause(_: bool = Depends(require_session)):
    cfg = load_app(); cfg["paused"] = True; save_app(cfg)
    return {"ok": True, "paused": True}

@router.post("/control/resume")
def resume(_: bool = Depends(require_session)):
    cfg = load_app(); cfg["paused"] = False; save_app(cfg)
    return {"ok": True, "paused": False}

@router.post("/jobs/retry")
def jobs_retry(body: dict, _: bool = Depends(require_session)):
    srcs = body.get("srcs") or []
    all_failed = bool(body.get("all_failed"))
    n = retry_failed(srcs=srcs, all_failed=all_failed)
    return {"ok": True, "updated": n}

@router.post("/jobs/purge_failed")
def jobs_purge_failed(_: bool = Depends(require_session)):
    n = purge_failed()
    return {"ok": True, "deleted": n}

@router.post("/jobs/delete_pending")
def jobs_delete_pending(body: dict, _: bool = Depends(require_session)):
    srcs = body.get("srcs") or []
    n = delete_pending(srcs)
    return {"ok": True, "deleted": n}

@router.post("/queue")
def queue(body: dict, _: bool = Depends(require_session)):
    import os
    path = (body or {}).get("path") or ""
    if not path:
        return {"ok": False, "error": "path_required"}
    cfg = load_app()
    queued = 0
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in VIDEO_EXT: continue
                src = os.path.join(root, fn)
                dst = mirrored_dst(cfg, src)
                upsert_job(src, dst); queued += 1
    else:
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXT:
            src = path
            dst = mirrored_dst(cfg, src)
            upsert_job(src, dst); queued += 1
    return {"ok": True, "queued": queued}

@router.get("/settings")
def get_settings(_: bool = Depends(require_session)):
    app = load_app()
    # Sanitize admin
    app_sanitized = {**app, "admin": {"username": app.get("admin",{}).get("username",""), "password_hash": bool(app.get("admin",{}).get("password_hash"))}}
    app_sanitized.pop("api_key", None)
    return {"app": app_sanitized, "bitrates": load_bitrates()}

@router.post("/settings/app")
def set_app(data: dict, _: bool = Depends(require_session)):
    cfg = load_app()
    incoming = data or {}
    # Empêcher de modifier le hash/mot de passe ici
    if "admin" in incoming:
        incoming = {**incoming}
        adm = incoming.pop("admin") or {}
        if adm.get("username"):
            cfg_admin = cfg.get("admin") or {}
            cfg_admin["username"] = adm.get("username")
            cfg["admin"] = cfg_admin
    cfg.update(incoming)
    save_app(cfg)
    return {"ok": True, "app": cfg}

@router.post("/settings/bitrates")
def set_bitrates(data: dict, _: bool = Depends(require_session)):
    save_bitrates(data or {"defaults": [], "overrides": []})
    return {"ok": True, "bitrates": data}

@router.get("/logs", response_class=PlainTextResponse)
def logs(_: bool = Depends(require_session)):
    return tail_logs(400)

@router.get("/logs/stream")
def logs_stream(_: bool = Depends(require_session)):
    def gen():
        import time
        from .logs import LOG_PATH
        pos = 0
        while True:
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
                if chunk:
                    yield chunk
            except FileNotFoundError:
                pass
            time.sleep(1)
    return StreamingResponse(gen(), media_type="text/plain")
