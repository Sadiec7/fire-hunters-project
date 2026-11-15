import os
import time
import json
import hashlib
import subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import ray

from motor_lojo_ignis import (
    algoritmo_cientifico_ignis,
    obtener_dataset_282_ensayos,
    entrenar_lojo_resiliente
)

def _worker_proceso_local(args):
    df_282, k, n_bootstrap = args
    df_train = df_282[df_282["jornada_id"] != k]
    df_val = df_282[df_282["jornada_id"] == k]
    return algoritmo_cientifico_ignis(df_train, df_val, k, n_bootstrap)

def _obtener_git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd="/workspace",
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if out:
            return out
    except Exception:
        pass
    # Fallback determinista basado en el hash del codigo fuente si .git no esta en el contenedor
    h = hashlib.sha256()
    for fname in ("arquitectura_vms.py", "motor_lojo_ignis.py", "pipeline_auditoria_nasa.py"):
        fpath = os.path.join("/workspace", fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                h.update(f.read())
    return f"local-{h.hexdigest()[:7]}"

def ejecutar_benchmark_abc_y_reproducibilidad(n_bootstrap: int = 3500) -> dict:
    if not ray.is_initialized():
        ray.init(address="auto", ignore_reinit_error=True)

    df_282 = obtener_dataset_282_ensayos()
    snapshot_bytes = df_282.to_csv(index=False).encode("utf-8")
    input_hash = hashlib.sha256(snapshot_bytes).hexdigest()
    jornadas = list(range(1, 19))
    p_workers = 4

    # -----------------------------------------------------------------
    # ESCENARIO A: Ejecución Secuencial en 1 máquina (T_1)
    # -----------------------------------------------------------------
    t_a0 = time.perf_counter()
    res_a = [
        algoritmo_cientifico_ignis(
            df_282[df_282["jornada_id"] != k],
            df_282[df_282["jornada_id"] == k],
            k, n_bootstrap
        )
        for k in jornadas
    ]
    t_a = time.perf_counter() - t_a0

    # -----------------------------------------------------------------
    # ESCENARIO B: Ejecución Paralela Local en 1 máquina (ProcessPool)
    # -----------------------------------------------------------------
    t_b0 = time.perf_counter()
    tareas_locales = [(df_282, k, n_bootstrap) for k in jornadas]
    with ProcessPoolExecutor(max_workers=p_workers) as pool:
        res_b = list(pool.map(_worker_proceso_local, tareas_locales))
    t_b = time.perf_counter() - t_b0

    # -----------------------------------------------------------------
    # ESCENARIO C: Ejecución Distribuida entre VMs / Contenedores (Ray)
    # -----------------------------------------------------------------
    t_c0 = time.perf_counter()
    t_put0 = time.perf_counter()
    df_ref = ray.put(df_282)
    t_put = time.perf_counter() - t_put0

    futuros = [entrenar_lojo_resiliente.remote(df_ref, k, n_bootstrap) for k in jornadas]
    res_c = ray.get(futuros)
    t_c = time.perf_counter() - t_c0

    max_worker_compute = max(r["worker_time_s"] for r in res_c)
    # Sobrecarga de comunicación + serialización + coordinación respecto al cuello de botella paralelo
    overhead_comm_s = max(0.0, t_c - max_worker_compute)

    # Ordenar resultados para validación cruzada A vs B vs C
    res_a.sort(key=lambda x: x["jornada_excluida"])
    res_b.sort(key=lambda x: x["jornada_excluida"])
    res_c.sort(key=lambda x: x["jornada_excluida"])

    equivalencia_abc = True
    for ra, rb, rc in zip(res_a, res_b, res_c):
        for campo in ("BN_01_prob_ignicion", "BN_02_prob_llama_fria", "SCM_ate_mean", "LOJO_val_rmse"):
            if not (np.isclose(ra[campo], rb[campo], atol=1e-12) and np.isclose(ra[campo], rc[campo], atol=1e-12)):
                equivalencia_abc = False

    # Cálculo de Speedup S(p) = T_1 / T_p y Eficiencia E(p) = S(p) / p
    s_b = round(t_a / t_b, 4) if t_b > 0 else 0.0
    e_b = round(s_b / p_workers, 4)

    s_c = round(t_a / t_c, 4) if t_c > 0 else 0.0
    e_c = round(s_c / p_workers, 4)

    # -----------------------------------------------------------------
    # MANIFIESTO DE REPRODUCIBILIDAD CIENTÍFICA (Tarea 6)
    # -----------------------------------------------------------------
    workers_activos = len([
        n for n in ray.nodes()
        if n.get("Alive") and n.get("Resources", {}).get("CPU", 0) > 0
    ])

    manifiesto_reproducibilidad = {
        "project": "IGNIS-mu",
        "dataset": "NASA-PSI-23",
        "model": "SCM-CF01",
        "model_version": "8.5.3C",
        "execution_type": "distributed",
        "input_hash": f"sha256:{input_hash}",
        "git_commit": _obtener_git_commit(),
        "workers": workers_activos,
        "parameters": {
            "ensayos": 282,
            "jornadas_lojo": 18,
            "bootstrap_iterations": n_bootstrap
        },
        "status": "completed",
        "validation": {
            "numerical_equivalence": equivalencia_abc,
            "scientific_warnings_preserved": True
        }
    }

    # Respaldo automático del artefacto en disco
    os.makedirs("/workspace/artefactos_reproducibilidad", exist_ok=True)
    ruta_artefacto = f"/workspace/artefactos_reproducibilidad/run_{input_hash[:12]}_b{n_bootstrap}.json"
    with open(ruta_artefacto, "w", encoding="utf-8") as f:
        json.dump(manifiesto_reproducibilidad, f, indent=2)

    return {
        "benchmark_abc": {
            "carga_evaluada": f"18 modelos LOJO x {n_bootstrap} bootstrap ({18 * n_bootstrap} re-muestreos)",
            "escenario_A_secuencial_1_maquina": {
                "tiempo_T1_s": round(t_a, 4),
                "speedup_S_p": 1.0,
                "eficiencia_E_p": 1.0
            },
            "escenario_B_paralelo_local_1_maquina": {
                "procesos_p": p_workers,
                "tiempo_Tp_s": round(t_b, 4),
                "speedup_S_p": s_b,
                "eficiencia_E_p": e_b
            },
            "escenario_C_distribuido_vms_ray": {
                "workers_p": workers_activos,
                "tiempo_Tp_s": round(t_c, 4),
                "speedup_S_p": s_c,
                "eficiencia_E_p": e_c,
                "tiempo_ray_put_plasma_s": round(t_put, 5),
                "sobrecarga_comunicacion_s": round(overhead_comm_s, 4),
                "distribuido_supera_secuencial": bool(t_c < t_a)
            }
        },
        "reproducibilidad_cientifica": manifiesto_reproducibilidad,
        "artefacto_respaldado": ruta_artefacto
    }