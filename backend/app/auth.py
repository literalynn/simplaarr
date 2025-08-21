
from fastapi import Depends, HTTPException, Request
from .settings import load_app, save_app
import bcrypt


def require_session(req: Request):
    user = (req.session or {}).get("user") if hasattr(req, "session") else None
    if not user:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return True

def validate_admin_credentials(username: str, password: str) -> bool:
    cfg = load_app()
    adm = cfg.get("admin") or {}
    u = (adm.get("username") or "").strip()
    ph = (adm.get("password_hash") or "").encode("utf-8")
    if not u or not ph:
        return False
    try:
        return username == u and bcrypt.checkpw(password.encode("utf-8"), ph)
    except Exception:
        return False

def is_setup_needed() -> bool:
    adm = (load_app().get("admin") or {})
    return not (adm.get("username") and adm.get("password_hash"))

def setup_admin(username: str, password: str):
    salt = bcrypt.gensalt(rounds=12)
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    cfg = load_app()
    adm = cfg.get("admin") or {}
    adm["username"] = username
    adm["password_hash"] = pw_hash
    # Nettoyer ancien champ si présent
    if "password" in adm:
        adm.pop("password", None)
    cfg["admin"] = adm
    save_app(cfg)
