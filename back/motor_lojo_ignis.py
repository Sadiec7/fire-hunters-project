import os
import time
import json
import socket
import hashlib
import numpy as np
import pandas as pd
import ray


def algoritmo_cientifico_ignis(df_train: pd.DataFrame, df_val: pd.DataFrame, jornada_excluida: int, n_bootstrap: int = 200):
    """
    Aquí se conectan las funciones de BN-01, BN-02, BN-03 y SCM del equipo científico.
    Usa semilla determinista por jornada para garantizar reproducibilidad exacta
    entre ejecución secuencial y distribuida.
    """
    rng = np.random.default_rng(seed=10000 + int(jornada_excluida))
    
    x_flujo = df_train["flujo_mfc"].to_numpy()
    x_o2 = df_train["oxigeno_pct"].to_numpy()
    x_efield = df_train["efield_v"].to_numpy()
    y_temp = df_train["temp_termopar"].to_numpy()
    y_ion = df_train["ion_current"].to_numpy()

    
    bn01_prob_ignicion = float(np.mean((x_o2 > 15.0) & (x_flujo < 25.0)))
    bn02_prob_llama_fria = float(np.mean((y_temp >= 500.0) & (y_temp <= 1000.0)))
    bn03_acoplamiento_efield = float(np.corrcoef(x_efield, y_ion)[0, 1])

    
    n_train = len(df_train)
    boot_ates = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = rng.integers(0, n_train, size=n_train)
        
        boot_ates[b] = np.mean(y_temp[idx] * 0.015 - x_flujo[idx] * 0.42 + x_o2[idx] * 1.18)

    scm_ate_mean = float(np.mean(boot_ates))
    scm_ci_low, scm_ci_high = [float(v) for v in np.percentile(boot_ates, [2.5, 97.5])]

    
    pred_val = df_val["oxigeno_pct"].to_numpy() * 38.5 - df_val["flujo_mfc"].to_numpy() * 4.1
    rmse_lojo = float(np.sqrt(np.mean((df_val["temp_termopar"].to_numpy() - pred_val) ** 2)))

    return {
        "modelo_id": f"M_-{jornada_excluida}",
        "jornada_excluida": int(jornada_excluida),
        "ensayos_entrenamiento": int(len(df_train)),
        "ensayos_validacion": int(len(df_val)),
        "BN_01_prob_ignicion": round(bn01_prob_ignicion, 8),
        "BN_02_prob_llama_fria": round(bn02_prob_llama_fria, 8),
        "BN_03_corr_efield_ion": round(bn03_acoplamiento_efield, 8),
        "SCM_ate_mean": round(scm_ate_mean, 8),
        "SCM_ci95_low": round(scm_ci_low, 8),
        "SCM_ci95_high": round(scm_ci_high, 8),
        "LOJO_val_rmse": round(rmse_lojo, 8)
    }



def obtener_dataset_282_ensayos() -> pd.DataFrame:
    rng = np.random.default_rng(seed=2026)
    total_ensayos = 282
    total_jornadas = 18
    # Repartir exactamente 282 ensayos en las 18 jornadas (15 o 16 ensayos por jornada)
    jornadas = np.array([(i % total_jornadas) + 1 for i in range(total_ensayos)])
    jornadas.sort()

    df = pd.DataFrame({
        "ensayo_id": [f"ENS-{i+1:03d}" for i in range(total_ensayos)],
        "jornada_id": jornadas,
        "flujo_mfc": rng.uniform(1.5, 33.0, size=total_ensayos),
        "oxigeno_pct": rng.uniform(12.5, 21.0, size=total_ensayos),
        "efield_v": rng.uniform(-0.2, 1.8, size=total_ensayos),
        "ion_current": rng.uniform(0.3, 1.2, size=total_ensayos),
        "temp_termopar": rng.uniform(480.0, 1380.0, size=total_ensayos)
    })
    return df


@ray.remote
def entrenar_lojo_worker(df_compartido: pd.DataFrame, jornada_k: int, n_bootstrap: int):
    t0 = time.perf_counter()
    df_train = df_compartido[df_compartido["jornada_id"] != jornada_k]
    df_val = df_compartido[df_compartido["jornada_id"] == jornada_k]
    
    resultado = algoritmo_cientifico_ignis(df_train, df_val, jornada_k, n_bootstrap)
    resultado["worker_hostname"] = socket.gethostname()
    resultado["worker_time_s"] = round(time.perf_counter() - t0, 5)
    return resultado


def ejecutar_validacion_lojo_completa(n_bootstrap: int = 500, incluir_estudio_crossover: bool = True):
    if not ray.is_initialized():
        ray.init(address="auto", ignore_reinit_error=True)

    df_282 = obtener_dataset_282_ensayos()
    snapshot_bytes = df_282.to_csv(index=False).encode("utf-8")
    input_hash = hashlib.sha256(snapshot_bytes).hexdigest()

    jornadas = list(range(1, 19)) # Jornadas 1 a 18

   
    t_seq_0 = time.perf_counter()
    resultados_seq = []
    for k in jornadas:
        df_train = df_282[df_282["jornada_id"] != k]
        df_val = df_282[df_282["jornada_id"] == k]
        resultados_seq.append(algoritmo_cientifico_ignis(df_train, df_val, k, n_bootstrap))
    t_seq = time.perf_counter() - t_seq_0

    
    t_dist_0 = time.perf_counter()
    df_ref = ray.put(df_282)
    futuros = [entrenar_lojo_worker.remote(df_ref, k, n_bootstrap) for k in jornadas]
    resultados_dist = ray.get(futuros)
    t_dist = time.perf_counter() - t_dist_0

   
    resultados_seq.sort(key=lambda x: x["jornada_excluida"])
    resultados_dist.sort(key=lambda x: x["jornada_excluida"])

    
    metricas_comparar = [
        "BN_01_prob_ignicion", "BN_02_prob_llama_fria", "BN_03_corr_efield_ion",
        "SCM_ate_mean", "SCM_ci95_low", "SCM_ci95_high", "LOJO_val_rmse"
    ]
    max_diff = 0.0
    equivalencia_exacta = True
    for r_s, r_d in zip(resultados_seq, resultados_dist):
        for m in metricas_comparar:
            diff = abs(r_s[m] - r_d[m])
            if diff > max_diff:
                max_diff = diff
            if not np.isclose(r_s[m], r_d[m], rtol=1e-12, atol=1e-12):
                equivalencia_exacta = False

    
    estudio_crossover = []
    if incluir_estudio_crossover:
        for b_iter in [20, 200, 1000, 3000]:
            ts0 = time.perf_counter()
            for k in jornadas:
                algoritmo_cientifico_ignis(
                    df_282[df_282["jornada_id"] != k],
                    df_282[df_282["jornada_id"] == k],
                    k, b_iter
                )
            t1_b = time.perf_counter() - ts0

            td0 = time.perf_counter()
            ref_b = ray.put(df_282)
            ray.get([entrenar_lojo_worker.remote(ref_b, k, b_iter) for k in jornadas])
            tp_b = time.perf_counter() - td0

            speedup_b = round(t1_b / tp_b, 4) if tp_b > 0 else 0.0
            estudio_crossover.append({
                "bootstrap_iteraciones_por_modelo": b_iter,
                "total_re_muestreos_18_modelos": b_iter * 18,
                "tiempo_secuencial_s": round(t1_b, 4),
                "tiempo_distribuido_ray_s": round(tp_b, 4),
                "speedup_S_p": speedup_b,
                "conviene_distribuir": bool(tp_b < t1_b)
            })

    workers_usados = sorted(list({r["worker_hostname"] for r in resultados_dist}))
    num_workers = max(1, len(workers_usados))
    speedup = round(t_seq / t_dist, 4) if t_dist > 0 else 0.0
    eficiencia = round(speedup / num_workers, 4)

    return {
        "project": "IGNIS-mu",
        "task": "LOJO_18_JORNADAS_CAUSAL",
        "ensayos_totales": int(len(df_282)),
        "jornadas_evaluadas": 18,
        "bootstrap_por_modelo": n_bootstrap,
        "input_sha256": input_hash,
        "tiempos": {
            "secuencial_T1_s": round(t_seq, 4),
            "distribuido_Tp_s": round(t_dist, 4),
            "speedup_S_p": speedup,
            "eficiencia_E_p": eficiencia,
            "contenedores_activos": workers_usados
        },
        "validacion_equivalencia": {
            "numerical_equivalence": equivalencia_exacta,
            "max_abs_diff": float(max_diff),
            "tolerancia": 1e-12
        },
        "punto_equilibrio_282_ensayos": estudio_crossover,
        "modelos_lojo": resultados_dist
    }


@ray.remote(max_retries=3, retry_exceptions=True)
def entrenar_lojo_resiliente(df_compartido: pd.DataFrame, jornada_k: int, n_bootstrap: int):
    t0 = time.perf_counter()
    df_train = df_compartido[df_compartido["jornada_id"] != jornada_k]
    df_val = df_compartido[df_compartido["jornada_id"] == jornada_k]
    resultado = algoritmo_cientifico_ignis(df_train, df_val, jornada_k, n_bootstrap)
    resultado["worker_hostname"] = socket.gethostname()
    resultado["worker_pid"] = os.getpid()
    resultado["worker_time_s"] = round(time.perf_counter() - t0, 5)
    return resultado

def ejecutar_lojo_resiliente_caos(n_bootstrap: int = 12000):
    if not ray.is_initialized():
        ray.init(address="auto", ignore_reinit_error=True)

    df_282 = obtener_dataset_282_ensayos()
    input_hash = hashlib.sha256(df_282.to_csv(index=False).encode("utf-8")).hexdigest()
    jornadas = list(range(1, 19))

    
    nodos_antes = sorted([
        n["NodeManagerHostname"] for n in ray.nodes()
        if n.get("Alive") and n.get("Resources", {}).get("CPU", 0) > 0
    ])

   
    t_dist_0 = time.perf_counter()
    df_ref = ray.put(df_282)
    futuros = [entrenar_lojo_resiliente.remote(df_ref, k, n_bootstrap) for k in jornadas]
    resultados_recuperados = ray.get(futuros)
    t_dist_caos = time.perf_counter() - t_dist_0


    nodos_despues = sorted([
        n["NodeManagerHostname"] for n in ray.nodes()
        if n.get("Alive") and n.get("Resources", {}).get("CPU", 0) > 0
    ])
    nodos_caidos = sorted(list(set(nodos_antes) - set(nodos_despues)))

    resultados_recuperados.sort(key=lambda x: x["jornada_excluida"])

    
    ids_modelos = [r["modelo_id"] for r in resultados_recuperados]
    duplicados = len(ids_modelos) - len(set(ids_modelos))
    faltantes = len(set(f"M_-{k}" for k in jornadas) - set(ids_modelos))

    
    reparto_por_worker = {}
    for r in resultados_recuperados:
        h = r["worker_hostname"]
        reparto_por_worker[h] = reparto_por_worker.get(h, 0) + 1

    
    t_ref_0 = time.perf_counter()
    resultados_sin_fallo = [
        algoritmo_cientifico_ignis(
            df_282[df_282["jornada_id"] != k],
            df_282[df_282["jornada_id"] == k],
            k, n_bootstrap
        )
        for k in jornadas
    ]
    t_ref_s = time.perf_counter() - t_ref_0

    metricas = [
        "BN_01_prob_ignicion", "BN_02_prob_llama_fria", "BN_03_corr_efield_ion",
        "SCM_ate_mean", "SCM_ci95_low", "SCM_ci95_high", "LOJO_val_rmse"
    ]
    max_diff = 0.0
    equivalencia_ok = True
    for r_ref, r_rec in zip(resultados_sin_fallo, resultados_recuperados):
        for m in metricas:
            diff = abs(r_ref[m] - r_rec[m])
            if diff > max_diff:
                max_diff = diff
            if not np.isclose(r_ref[m], r_rec[m], rtol=1e-12, atol=1e-12):
                equivalencia_ok = False

    return {
        "project": "IGNIS-mu",
        "experiment": "CHAOS_ENGINEERING_LOJO_FAILOVER",
        "input_sha256": input_hash,
        "bootstrap_por_modelo": n_bootstrap,
        "pruebas_caos": {
            "prueba_A_total_tareas_lojo": 18,
            "prueba_B_workers_iniciales": nodos_antes,
            "prueba_C_workers_caidos_detectados": nodos_caidos,
            "prueba_D_workers_sobrevivientes": nodos_despues,
            "prueba_D_tareas_completadas_por_worker": reparto_por_worker,
            "duplicados_detectados": duplicados,
            "trabajos_perdidos": faltantes,
            "prueba_E_numerical_equivalence": equivalencia_ok,
            "prueba_E_max_abs_diff": float(max_diff)
        },
        "tiempos": {
            "ejecucion_con_caida_y_recuperacion_s": round(t_dist_caos, 4),
            "referencia_sin_interrupciones_s": round(t_ref_s, 4)
        },
        "modelos_recuperados": resultados_recuperados
    }


if __name__ == "__main__":
    print(json.dumps(ejecutar_validacion_lojo_completa(), indent=2))