from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import psutil

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
def health():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disks = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disks.append({"mount": p.mountpoint, "fstype": p.fstype, "percent": round(usage.percent, 1), "used_gb": round(usage.used / 1e9, 1), "total_gb": round(usage.total / 1e9, 1)})
        except Exception:
            continue
    service_running = 0
    service_stopped = 0
    try:
        for s in psutil.win_service_iter():
            try:
                st = (s.status() or "other").lower()
            except Exception:
                st = "other"
            if st == "running":
                service_running += 1
            elif st == "stopped":
                service_stopped += 1
    except Exception:
        pass
    try:
        boot_ts = psutil.boot_time()
    except Exception:
        boot_ts = None
    try:
        net_addrs = [a._asdict() for a in psutil.net_if_addrs().get("Ethernet", [])][:8]
    except Exception:
        net_addrs = []
    return {
        "cpu": cpu,
        "memory": mem.percent,
        "memory_total_gb": round(mem.total / 1e9, 1),
        "memory_used_gb": round(mem.used / 1e9, 1),
        "disk": disks,
        "services": {"running": service_running, "stopped": service_stopped},
        "boot_ts": boot_ts,
        "network": net_addrs,
    }

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
<head>
  <title>System Health</title>
  <style>
    body { font-family: system-ui; padding: 24px; }
    .metric { padding: 12px; margin: 8px 0; border-radius: 8px; background: #0f172a; color: #e2e8f0; }
  </style>
</head>
<body>
  <h1>System Health</h1>
  <div id="metrics">Loading...</div>
  <script>
    async function load() {
      const res = await fetch('/api/health');
      const data = await res.json();
      document.getElementById('metrics').innerHTML = `
        <div class='metric'>CPU: ${data.cpu}%</div>
        <div class='metric'>Memory: ${data.memory}%</div>
        <div class='metric'>Disk C: ${data.disk}%</div>
      `;
    }
    load();
    setInterval(load, 3000);
  </script>
</body>
</html>
"""
