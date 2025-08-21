
from fastapi import Depends, HTTPException, Header
from .settings import load_app

def require_api_key(x_api_key: str | None = Header(default=None)):
    cfg = load_app()
    key = (cfg.get("api_key") or "").strip()
    if not key:
        return True
    if x_api_key != key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
