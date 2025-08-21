
import os, time
LOG_PATH = os.environ.get("SIMPLAARR_LOG", "/logs/simplaarr.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def write(line: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def tail(lines=200):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            data = f.readlines()
            return "".join(data[-lines:])
    except FileNotFoundError:
        return ""
