
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, StreamingResponse
from .settings import load_app, save_app, load_bitrates, save_bitrates
from .db import get_stats, list_recent
from .gpu import system_summary, list_gpus
from .logs import tail as tail_logs
from .scan import scan_once
from .auth import require_api_key

router = APIRouter(prefix="/api")

@router.get("/stats")
def stats(_: bool = Depends(require_api_key)):
    return get_stats()

@router.get("/gpus")
def gpus(_: bool = Depends(require_api_key)):
    return {"gpus": list_gpus()}

@router.get("/system")
def sys(_: bool = Depends(require_api_key)):
    return system_summary()

@router.get("/jobs")
def jobs(_: bool = Depends(require_api_key)):
    return {"recent": list_recent(200)}

@router.post("/scan")
def scan(_: bool = Depends(require_api_key)):
    return scan_once()

@router.get("/settings")
def get_settings(_: bool = Depends(require_api_key)):
    return {"app": load_app(), "bitrates": load_bitrates()}

@router.post("/settings/app")
def set_app(data: dict, _: bool = Depends(require_api_key)):
    cfg = load_app()
    cfg.update(data or {})
    save_app(cfg)
    return {"ok": True, "app": cfg}

@router.post("/settings/bitrates")
def set_bitrates(data: dict, _: bool = Depends(require_api_key)):
    save_bitrates(data or {"defaults": [], "overrides": []})
    return {"ok": True, "bitrates": data}

@router.get("/logs", response_class=PlainTextResponse)
def logs(_: bool = Depends(require_api_key)):
    return tail_logs(400)

@router.get("/logs/stream")
def logs_stream(_: bool = Depends(require_api_key)):
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
