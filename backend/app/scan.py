
import os, time, threading
from .settings import load_app
from .db import upsert_job, get_stats, fetch_next_pending, mark_status
from .logs import write as log
from .encode import process_file

VIDEO_EXT = {".mkv",".mp4",".avi",".mov",".m4v",".webm",".ts",".m2ts",".wmv"}

def mirrored_dst(cfg, src_path):
    rel = os.path.relpath(src_path, cfg["library_path"])
    return os.path.join(cfg["output_path"], rel)

def scan_once():
    cfg = load_app()
    base = cfg["library_path"]
    for root, dirs, files in os.walk(base):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in VIDEO_EXT:
                continue
            src = os.path.join(root, fn)
            dst = mirrored_dst(cfg, src)
            upsert_job(src, dst)
    s = get_stats()
    log(f"[scan] queued: {s.get('pending',0)}; total done={s.get('done',0)}, failed={s.get('failed',0)}")
    return s

def worker_loop(stop_event):
    cfg = load_app()
    gpus = cfg.get("gpu_indices") or []
    workers = max(1, int(cfg.get("workers_per_gpu", 1)))
    gpu_cycle = [None] if not gpus else gpus[:]
    gpu_index = 0

    while not stop_event.is_set():
        batch = fetch_next_pending(limit=workers if gpus else 1)
        if not batch:
            time.sleep(2)
            continue
        for src, dst in batch:
            assigned_gpu = None
            if gpus:
                assigned_gpu = gpu_cycle[gpu_index % len(gpu_cycle)]
                gpu_index += 1
            mark_status(src, "processing", assigned_gpu=assigned_gpu)
            ok, msg = process_file(src, dst, assigned_gpu=assigned_gpu)
            if ok:
                mark_status(src, "done", assigned_gpu=assigned_gpu)
            else:
                mark_status(src, "failed", error=msg, assigned_gpu=assigned_gpu)

def scheduler_loop(stop_event):
    while not stop_event.is_set():
        try:
            scan_once()
        except Exception as e:
            log(f"[error] scan failed: {e}")
        from .settings import load_app
        hours = int(load_app().get("scan_interval_hours", 6))
        for _ in range(hours*60):
            if stop_event.is_set():
                break
            time.sleep(60)
