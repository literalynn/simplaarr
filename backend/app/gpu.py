
import psutil
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False

def list_gpus():
    gpus = []
    if NVML_AVAILABLE:
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(h).decode()
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            gpus.append({
                "index": i,
                "name": name,
                "utilization": getattr(util, "gpu", None),
                "mem_used": getattr(mem, "used", None),
                "mem_total": getattr(mem, "total", None),
            })
    return gpus

def system_summary():
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "mem": psutil.virtual_memory()._asdict(),
        "gpus": list_gpus()
    }
