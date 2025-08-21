
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("SIMPLAARR_DB", "/data/simplaarr.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # Optimisations SQLite: WAL et synchronous NORMAL
        try:
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_path TEXT UNIQUE,
    dst_path TEXT,
    status TEXT,
    codec_out TEXT,
    bitrate_kbps INTEGER,
    width INTEGER,
    height INTEGER,
    hdr INTEGER,
    assigned_gpu INTEGER,
    error TEXT,
    created_at TEXT,
    updated_at TEXT
);
""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated ON jobs(updated_at DESC);")
        conn.commit()

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def upsert_job(src_path, dst_path):
    import datetime
    with db() as conn:
        cur = conn.cursor()
        now = datetime.datetime.utcnow().isoformat()
        cur.execute("SELECT id, status FROM jobs WHERE src_path=?", (src_path,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE jobs SET dst_path=?, updated_at=? WHERE id=?", (dst_path, now, row[0]))
            return row[0]
        cur.execute(
            "INSERT INTO jobs(src_path, dst_path, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
            (src_path, dst_path, now, now)
        )
        return cur.lastrowid

def mark_status(src_path, status, error=None, assigned_gpu=None):
    import datetime
    with db() as conn:
        cur = conn.cursor()
        now = datetime.datetime.utcnow().isoformat()
        cur.execute(
            "UPDATE jobs SET status=?, error=?, assigned_gpu=?, updated_at=? WHERE src_path=?",
            (status, error, assigned_gpu, now, src_path)
        )

def fetch_next_pending(limit=1):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT src_path, dst_path FROM jobs WHERE status='pending' LIMIT ?", (limit,))
        return cur.fetchall()

def claim_next_pending(limit=1):
    """Réservation atomique d'un lot de jobs en 'processing'.
    SQLite n'a pas RETURNING sur toutes versions; on fait en deux temps sous transaction.
    """
    claimed = []
    with db() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT src_path, dst_path FROM jobs WHERE status='pending' LIMIT ?", (limit,))
        rows = cur.fetchall()
        for src, dst in rows:
            cur.execute("UPDATE jobs SET status='processing' WHERE src_path=? AND status='pending'", (src,))
            claimed.append((src, dst))
    return claimed

def get_stats():
    with db() as conn:
        cur = conn.cursor()
        counts = {}
        for s in ['pending','processing','done','failed']:
            cur.execute("SELECT COUNT(*) FROM jobs WHERE status=?", (s,))
            counts[s] = cur.fetchone()[0]
        return counts

def list_recent(limit=100):
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT src_path, dst_path, status, error, updated_at FROM jobs ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        return [{
            "src": r[0], "dst": r[1], "status": r[2], "error": r[3], "updated_at": r[4]
        } for r in rows]

def list_jobs(limit=200, status: str | None = None):
    with db() as conn:
        cur = conn.cursor()
        if status:
            cur.execute(
                "SELECT src_path, dst_path, status, error, updated_at FROM jobs WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            cur.execute(
                "SELECT src_path, dst_path, status, error, updated_at FROM jobs ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
        rows = cur.fetchall()
        return [{
            "src": r[0], "dst": r[1], "status": r[2], "error": r[3], "updated_at": r[4]
        } for r in rows]

def retry_failed(srcs: list[str] | None = None, all_failed: bool = False):
    with db() as conn:
        cur = conn.cursor()
        if all_failed:
            cur.execute("UPDATE jobs SET status='pending', error=NULL WHERE status='failed'")
            return cur.rowcount
        if srcs:
            qmarks = ",".join(["?"] * len(srcs))
            cur.execute(f"UPDATE jobs SET status='pending', error=NULL WHERE status='failed' AND src_path IN ({qmarks})", tuple(srcs))
            return cur.rowcount
        return 0

def purge_failed():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jobs WHERE status='failed'")
        return cur.rowcount

def delete_pending(srcs: list[str]):
    with db() as conn:
        cur = conn.cursor()
        qmarks = ",".join(["?"] * len(srcs))
        cur.execute(f"DELETE FROM jobs WHERE status='pending' AND src_path IN ({qmarks})", tuple(srcs))
        return cur.rowcount
