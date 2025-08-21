
import json, os, threading

CONFIG_DIR = os.environ.get("SIMPLAARR_CONFIG", "/config")
APP_JSON = os.path.join(CONFIG_DIR, "app.json")
BIT_JSON = os.path.join(CONFIG_DIR, "bitrates.json")

# Valeurs par défaut créées automatiquement si les fichiers manquent
DEFAULT_APP = {
    "library_path": "/media",
    "output_path": "/media-encoded",
    "cache_path": "/cache",
    "video_codec": "hevc",  # hevc | h264 | av1
    "gpu_indices": [],
    "workers_per_gpu": 1,
    "scan_interval_hours": 6,
    "paused": False,
    "api_key": "",  # obsolète
    "admin": {"username": "", "password_hash": ""},
}

DEFAULT_BITRATES = {
    "defaults": [
        {"width": 3840, "hdr": True,  "bitrate_kbps": 18000},
        {"width": 3840, "hdr": False, "bitrate_kbps": 16000},
        {"width": 1920, "hdr": True,  "bitrate_kbps": 10000},
        {"width": 1920, "hdr": False, "bitrate_kbps": 8000},
        {"width": 1280, "hdr": False, "bitrate_kbps": 4500},
    ],
    "overrides": []
}

_lock = threading.Lock()

def load_app():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with _lock:
        if not os.path.exists(APP_JSON):
            with open(APP_JSON, "w") as f:
                json.dump(DEFAULT_APP, f, indent=2)
            return DEFAULT_APP.copy()
        try:
            with open(APP_JSON, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        # Merge avec defaults (priorité au fichier)
        merged = DEFAULT_APP.copy()
        merged.update(data or {})
        # Merge admin (objet imbriqué)
        if isinstance(merged.get("admin"), dict):
            adm_in = merged.get("admin") or {}
            adm = DEFAULT_APP["admin"].copy()
            adm.update(adm_in)
            # Migration: si ancien champ 'password' existe, on le laisse pour migration ultérieure (login/setup)
            if "password" in adm_in and not adm.get("password_hash"):
                adm["password_hash"] = ""  # sera rempli lors du setup ou du premier changement
            merged["admin"] = adm
        else:
            merged["admin"] = DEFAULT_APP["admin"].copy()
        return merged

def save_app(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with _lock:
        with open(APP_JSON, "w") as f:
            json.dump(cfg, f, indent=2)

def load_bitrates():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with _lock:
        if not os.path.exists(BIT_JSON):
            with open(BIT_JSON, "w") as f:
                json.dump(DEFAULT_BITRATES, f, indent=2)
            return DEFAULT_BITRATES.copy()
        try:
            with open(BIT_JSON, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        # Merge simple avec defaults
        merged = {
            "defaults": data.get("defaults") if isinstance(data.get("defaults"), list) and data.get("defaults") else DEFAULT_BITRATES["defaults"],
            "overrides": data.get("overrides") if isinstance(data.get("overrides"), list) else [],
        }
        return merged

def save_bitrates(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with _lock:
        with open(BIT_JSON, "w") as f:
            json.dump(data, f, indent=2)

def bitrate_for(file_info, cfg, bitrates):
    import os
    path = file_info.get("src_path","")
    width = file_info.get("width", 1920) or 1920
    hdr = bool(file_info.get("hdr", False))
    dirname_parts = set(os.path.normpath(path).split(os.sep))
    for rule in bitrates.get("overrides", []):
        pat = rule.get("directory_pattern","")
        if not pat: continue
        if pat in dirname_parts or pat in path:
            if int(rule.get("width", 1920)) <= width and bool(rule.get("hdr", False)) == hdr:
                return int(rule.get("bitrate_kbps", 8000))
    candidates = []
    for rule in bitrates.get("defaults", []):
        rw = int(rule.get("width", 1920))
        rhdr = bool(rule.get("hdr", False))
        if rw <= width and rhdr == hdr:
            candidates.append((rw, rule))
    if candidates:
        _, best = sorted(candidates, key=lambda x: x[0], reverse=True)[0]
        return int(best.get("bitrate_kbps", 8000))
    return 8000
