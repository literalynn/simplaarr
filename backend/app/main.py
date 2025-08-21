
import os, threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .api import router as api_router
from .scan import worker_loop, scheduler_loop
from .logs import write as log

app = FastAPI(title="SimplAarr", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.environ.get("SIMPLAARR_STATIC", "/app/static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

app.include_router(api_router)

stop_event = threading.Event()
threads = []

@app.on_event("startup")
def on_start():
    init_db()
    log("[startup] SimplAarr starting")
    t1 = threading.Thread(target=worker_loop, args=(stop_event,), daemon=True)
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=scheduler_loop, args=(stop_event,), daemon=True)
    t2.start()
    threads.append(t2)

@app.on_event("shutdown")
def on_stop():
    stop_event.set()
    log("[shutdown] SimplAarr stopping")
