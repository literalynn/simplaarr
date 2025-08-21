
import json, os, threading

CONFIG_DIR = os.environ.get("SIMPLAARR_CONFIG", "/config")
APP_JSON = os.path.join(CONFIG_DIR, "app.json")
BIT_JSON = os.path.join(CONFIG_DIR, "bitrates.json")

_lock = threading.Lock()

def load_app():
    with _lock:
        with open(APP_JSON, "r") as f:
            return json.load(f)

def save_app(cfg):
    with _lock:
        with open(APP_JSON, "w") as f:
            json.dump(cfg, f, indent=2)

def load_bitrates():
    with _lock:
        with open(BIT_JSON, "r") as f:
            return json.load(f)

def save_bitrates(data):
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
