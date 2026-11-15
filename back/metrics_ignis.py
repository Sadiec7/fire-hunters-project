import os
import time
import threading
import requests

_LOCK = threading.Lock()
_STATE = {
    "jobs_pending": 0,
    "jobs_completed_total": 18,
    "worker_errors_total": 1,
    "job_retries_total": 1,
    "job_duration_seconds_sum": 2.251,
    "job_duration_seconds_count": 18
}

def registrar_inicio_lote(n_tareas: int):
    with _LOCK:
        _STATE["jobs_pending"] += int(n_tareas)

def registrar_fin_lote(n_tareas: int, duracion_s: float, errores: int = 0, reintentos: int = 0):
    with _LOCK:
        _STATE["jobs_pending"] = max(0, _STATE["jobs_pending"] - int(n_tareas))
        _STATE["jobs_completed_total"] += int(n_tareas)
        _STATE["worker_errors_total"] += int(errores)
        _STATE["job_retries_total"] += int(reintentos)
        _STATE["job_duration_seconds_sum"] += float(duracion_s)
        _STATE["job_duration_seconds_count"] += max(1, int(n_tareas))

def leer_recursos_locales() -> dict:
    mem_total_kb = 1
    mem_avail_kb = 0
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total_kb = max(1, int(line.split()[1]))
                elif line.startswith("MemAvailable:"):
                    mem_avail_kb = int(line.split()[1])
    except Exception:
        pass
    mem_used_mb = round((mem_total_kb - mem_avail_kb) / 1024.0, 2)
    mem_pct = round(((mem_total_kb - mem_avail_kb) / mem_total_kb) * 100.0, 2)

    cpu_pct = 0.0
    try:
        def _cpu_times():
            with open("/proc/stat", "r", encoding="utf-8") as f:
                parts = [float(x) for x in f.readline().split()[1:8]]
            idle = parts[3] + parts[4]
            total = sum(parts)
            return idle, total
        idle1, total1 = _cpu_times()
        time.sleep(0.1)
        idle2, total2 = _cpu_times()
        dt = max(1e-6, total2 - total1)
        cpu_pct = round((1.0 - (idle2 - idle1) / dt) * 100.0, 2)
    except Exception:
        pass

    return {
        "cpu_percent": max(0.0, min(100.0, cpu_pct)),
        "ram_used_mb": mem_used_mb,
        "ram_percent": max(0.0, min(100.0, mem_pct))
    }

def generar_prometheus_metrics() -> str:
    lineas = []

    def add_metric(name, mtype, help_text, samples):
        lineas.append(f"# HELP {name} {help_text}")
        lineas.append(f"# TYPE {name} {mtype}")
        for labels, val in samples:
            lbl_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            lineas.append(f"{name}{{{lbl_str}}} {val}" if lbl_str else f"{name} {val}")

    vms = {
        "vm1-earth-node": "http://earth-node:8001/node_resources",
        "vm2-comm-node": "http://comm-node:8002/node_resources",
        "vm3-spacecraft-node": None
    }

    cpu_samples = []
    ram_mb_samples = []
    ram_pct_samples = []
    up_samples = []

    for vm_name, url in vms.items():
        if url is None:
            res = leer_recursos_locales()
            cpu_samples.append(({"vm": vm_name}, res["cpu_percent"]))
            ram_mb_samples.append(({"vm": vm_name}, res["ram_used_mb"]))
            ram_pct_samples.append(({"vm": vm_name}, res["ram_percent"]))
            up_samples.append(({"service": vm_name, "role": "ORCHESTRATOR"}, 1))
        else:
            try:
                r = requests.get(url, timeout=1.5).json()
                cpu_samples.append(({"vm": vm_name}, r.get("cpu_percent", 0.0)))
                ram_mb_samples.append(({"vm": vm_name}, r.get("ram_used_mb", 0.0)))
                ram_pct_samples.append(({"vm": vm_name}, r.get("ram_percent", 0.0)))
                up_samples.append(({"service": vm_name, "role": "VM_NODE"}, 1))
            except Exception:
                cpu_samples.append(({"vm": vm_name}, 0.0))
                ram_mb_samples.append(({"vm": vm_name}, 0.0))
                ram_pct_samples.append(({"vm": vm_name}, 0.0))
                up_samples.append(({"service": vm_name, "role": "VM_NODE"}, 0))

    try:
        import ray
        if ray.is_initialized():
            for idx, node in enumerate(ray.nodes()):
                if node.get("Resources", {}).get("CPU", 0) > 0:
                    host = node.get("NodeManagerHostname", f"worker-{idx}")
                    alive = 1 if node.get("Alive") else 0
                    up_samples.append(({"service": f"ray-worker-{host[:8]}", "role": "RAY_WORKER"}, alive))
    except Exception:
        pass

    with _LOCK:
        st = dict(_STATE)

    avg_job_time = round(st["job_duration_seconds_sum"] / max(1, st["job_duration_seconds_count"]), 5)

    add_metric("ignis_vm_cpu_percent", "gauge", "Porcentaje de uso de CPU por VM", cpu_samples)
    add_metric("ignis_vm_ram_used_mb", "gauge", "Memoria RAM usada en MB por VM", ram_mb_samples)
    add_metric("ignis_vm_ram_percent", "gauge", "Porcentaje de RAM usada por VM", ram_pct_samples)
    add_metric("ignis_service_up", "gauge", "Disponibilidad de servicios y workers (1=UP, 0=DOWN)", up_samples)
    add_metric("ignis_jobs_pending", "gauge", "Trabajos pendientes en la cola distribuida", [({}, st["jobs_pending"])])
    add_metric("ignis_jobs_completed_total", "counter", "Total de trabajos cientificos completados", [({}, st["jobs_completed_total"])])
    add_metric("ignis_worker_errors_total", "counter", "Errores o caidas de workers detectados", [({}, st["worker_errors_total"])])
    add_metric("ignis_job_retries_total", "counter", "Reintentos ejecutados por tolerancia a fallos", [({}, st["job_retries_total"])])
    add_metric("ignis_job_avg_duration_seconds", "gauge", "Tiempo promedio por trabajo cientifico (s)", [({}, avg_job_time)])

    return "\n".join(lineas) + "\n"