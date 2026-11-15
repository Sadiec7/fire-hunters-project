import os
import time
import random
import sqlite3
import requests
import ray
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

VM_ROLE = os.getenv("VM_ROLE", "SPACECRAFT").upper()
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jhcegurjiqutptenqmxs.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_y3FAUHDRpQ0Vm9bTiZvUIQ_gGPmDtPF")

app = FastAPI(title=f"IGNIS ALFA - {VM_ROLE} NODE")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que el frontend en React consuma tu API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATALOGO_RESPALDO = [
    {"investigation_id": "SYN-BASS", "is_synthetic": True, "reference_family": "BASS-II-inspired", "psi_id": "PSI-25", "prior_risk": 0.78},
    {"investigation_id": "SYN-FLEX", "is_synthetic": True, "reference_family": "FLEX-inspired", "psi_id": "PSI-69", "prior_risk": 0.65},
    {"investigation_id": "SYN-SAFFIRE", "is_synthetic": True, "reference_family": "SAFFIRE-I-inspired", "psi_id": "PSI-98", "prior_risk": 0.89}
]

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }

# ==========================================
# VM 1: EARTH NODE (Supabase + Datos Reales PSI-23)
# ==========================================

from fastapi.responses import PlainTextResponse
from metrics_ignis import leer_recursos_locales, generar_prometheus_metrics, registrar_inicio_lote, registrar_fin_lote

@app.get("/node_resources")
def node_resources():
    return leer_recursos_locales()

@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    return generar_prometheus_metrics()

if VM_ROLE == "EARTH":
    class EvidenceItem(BaseModel):
        investigation_id: str
        is_synthetic: bool = False
        reference_family: str
        psi_id: str
        prior_risk: float

    @app.get("/earth/sync_evidence")
    def sync_evidence():
        db_status = "LOCAL_FALLBACK"
        records = CATALOGO_RESPALDO
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                url = f"{SUPABASE_URL}/rest/v1/evidence_records?select=investigation_id,is_synthetic,reference_family,psi_id,prior_risk"
                resp = requests.get(url, headers=supabase_headers(), timeout=5)
                if resp.status_code == 200:
                    records = resp.json()
                    db_status = "SUPABASE_CONNECTED"
            except Exception as e:
                db_status = f"SUPABASE_ERROR: {str(e)}"
        return {
            "source": "EARTH_NODE_VM1",
            "database_backend": db_status,
            "knowledge_graph_version": "2TBN-DBN-v1.4",
            "evidence_records": records
        }

    @app.get("/earth/psi23_batch")
    def get_psi23_batch(limit: int = 1000):
        if not (SUPABASE_URL and SUPABASE_KEY):
            return {"status": "NO_CREDENTIALS", "rows": []}
        try:
            url = f"{SUPABASE_URL}/rest/v1/psi23_datos_masivos_csv?select=*&limit={limit}"
            resp = requests.get(url, headers=supabase_headers(), timeout=15)
            if resp.status_code == 200:
                rows = resp.json()
                return {
                    "status": "OK",
                    "tabla": "psi23_datos_masivos_csv",
                    "total_extraidas": len(rows),
                    "rows": rows
                }
            return {"status": f"HTTP_{resp.status_code}", "detail": resp.text, "rows": []}
        except Exception as e:
            return {"status": "ERROR", "detail": str(e), "rows": []}

    @app.post("/earth/save_ray_results")
    def save_ray_results(payload: dict):
        if not (SUPABASE_URL and SUPABASE_KEY):
            return {"status": "NO_CREDENTIALS"}
        url = f"{SUPABASE_URL}/rest/v1/resultados_inferencia_ray"
        resp = requests.post(url, headers=supabase_headers(), json=payload, timeout=10)
        return {"status": "SAVED_IN_SUPABASE" if resp.status_code in (200, 201) else f"HTTP_{resp.status_code}", "detail": resp.json()}

    @app.post("/earth/upload_evidence")
    def upload_evidence(items: list[EvidenceItem]):
        if not (SUPABASE_URL and SUPABASE_KEY):
            return {"status": "ERROR", "detail": "Faltan credenciales."}
        url = f"{SUPABASE_URL}/rest/v1/evidence_records"
        resp = requests.post(url, headers=supabase_headers(), json=[item.dict() for item in items], timeout=5)
        return {"status": "UPSERT_OK" if resp.status_code in (200, 201) else "UPSERT_ERROR", "inserted_records": resp.json()}

# ==========================================
# VM 2: COMMUNICATION NODE (Latencia y Fallos)
# ==========================================
elif VM_ROLE == "COMM":
    @app.get("/comm/relay_sync")
    def relay_sync():
        time.sleep(0.4)
        if random.random() < 0.15:
            return {"status": "CONNECTION_FAILURE", "latency_applied_ms": 400, "payload": None}
        try:
            resp = requests.get("http://earth-node:8001/earth/sync_evidence", timeout=5)
            return {"status": "SYNC_OK", "latency_applied_ms": 400, "payload": resp.json()}
        except Exception as e:
            return {"status": "CONNECTION_FAILURE", "error": str(e)}

    @app.get("/comm/relay_psi23")
    def relay_psi23(limit: int = 1000):
        time.sleep(0.4)
        try:
            resp = requests.get(f"http://earth-node:8001/earth/psi23_batch?limit={limit}", timeout=15)
            return {"status": "SYNC_OK", "payload": resp.json()}
        except Exception as e:
            return {"status": "CONNECTION_FAILURE", "error": str(e)}

# ==========================================
# VM 3: SPACECRAFT NODE (SQLite + Clúster Ray)
# ==========================================
elif VM_ROLE == "SPACECRAFT":
    @ray.remote
    def procesar_particion_real_psi23(particion_id, filas_compartidas, inicio, fin):
        import socket
        sub_lote = filas_compartidas[inicio:fin]
        ignorar = {"id", "c_id_experimento", "c_archivo_origen", "c_nombre_experimento"}

        lecturas_totales = []
        termopar_vals = []
        radiometro_vals = []
        efield_vals = []

        for fila in sub_lote:
            for k, v in fila.items():
                if v is None or k.lower() in ignorar:
                    continue
                try:
                    num = float(v)
                    lecturas_totales.append(num)
                    if "thermocouple" in k:
                        termopar_vals.append(num)
                    elif "radiometer" in k:
                        radiometro_vals.append(num)
                    elif "efield:" in k:
                        efield_vals.append(num)
                except (ValueError, TypeError):
                    pass

        return {
            "particion": particion_id,
            "contenedor_ejecutor": socket.gethostname(),
            "filas_procesadas": len(sub_lote),
            "lecturas_fisicas_evaluadas": len(lecturas_totales),
            "promedio_termopar_V": round(sum(termopar_vals) / len(termopar_vals), 5) if termopar_vals else 0.0,
            "promedio_radiometro_V": round(sum(radiometro_vals) / len(radiometro_vals), 5) if radiometro_vals else 0.0,
            "promedio_efield_V": round(sum(efield_vals) / len(efield_vals), 5) if efield_vals else 0.0,
            "pico_maximo_global": round(max(lecturas_totales), 5) if lecturas_totales else 0.0
        }

    @app.get("/", response_class=HTMLResponse)
    def dashboard_home():
        return """
        <html>
            <body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem;">
                <h1>IGNIS ALFA / PYRO-CAUSAL 0G - Spacecraft Node (VM 3)</h1>
                <p>Clúster distribuido Ray conectado a Supabase (psi23_datos_masivos_csv - 24 sensores físicos activos).</p>
                <ul>
                    <li><a href="/spacecraft/process_real_psi23?limit=1000" style="color: #38bdf8;">Procesar 1,000 Filas Reales de PSI-23 en Ray</a></li>
                    <li><a href="/docs" style="color: #38bdf8;">Documentación API (Swagger)</a></li>
                </ul>
            </body>
        </html>
        """



    @app.get("/spacecraft/audit_nasa_pipeline")
    def audit_nasa_pipeline(limit: int = 500):
        from pipeline_auditoria_nasa import auditar_experimento_nasa
        try:
            resp = requests.get(f"http://earth-node:8001/earth/psi23_batch?limit={limit}", timeout=15).json()
            rows = resp.get("rows", [])
        except Exception as e:
            return {"status": "ERROR_LECTURA_SUPABASE", "detail": str(e)}

        resultado_auditoria = auditar_experimento_nasa(rows, tabla_origen="psi23_datos_masivos_csv")
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": f"AUDITORIA_TEMPORAL_{resultado_auditoria['gate_cientifico']['experiment_id']}",
                "archivo_origen": resultado_auditoria["reporte_calidad"]["archivo_auditado"],
                "total_filas": len(rows),
                "tiempo_ejecucion_s": 0.0,
                "resumen_particiones": [resultado_auditoria]
            }, timeout=10).json()
            resultado_auditoria["supabase_persistence"] = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            resultado_auditoria["supabase_persistence"] = f"ERROR: {str(e)}"
        return resultado_auditoria



    @app.get("/spacecraft/run_benchmark_and_repro")
    def run_benchmark_and_repro(n_bootstrap: int = 3500):
        from benchmark_y_repro import ejecutar_benchmark_abc_y_reproducibilidad
        registrar_inicio_lote(18)
        reporte = ejecutar_benchmark_abc_y_reproducibilidad(n_bootstrap=n_bootstrap)
        registrar_fin_lote(18, reporte["benchmark_abc"]["escenario_C_distribuido_vms_ray"]["tiempo_Tp_s"])
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": "IGNIS-mu BENCHMARK ABC + REPRODUCIBILIDAD",
                "archivo_origen": reporte["reproducibilidad_cientifica"]["input_hash"][:23],
                "total_filas": 282,
                "tiempo_ejecucion_s": reporte["benchmark_abc"]["escenario_C_distribuido_vms_ray"]["tiempo_Tp_s"],
                "resumen_particiones": [reporte]
            }, timeout=10).json()
            reporte["supabase_persistence"] = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            reporte["supabase_persistence"] = f"ERROR: {str(e)}"
        return reporte

    @app.get("/spacecraft/run_chaos_lojo")
    def run_chaos_lojo(n_bootstrap: int = 12000):
        from motor_lojo_ignis import ejecutar_lojo_resiliente_caos
        registrar_inicio_lote(18)
        reporte = ejecutar_lojo_resiliente_caos(n_bootstrap=n_bootstrap)
        caidos = len(reporte["pruebas_caos"]["prueba_C_workers_caidos_detectados"])
        registrar_fin_lote(18, reporte["tiempos"]["ejecucion_con_caida_y_recuperacion_s"], errores=caidos, reintentos=caidos)
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": "IGNIS-mu CHAOS FAILOVER (LOJO 18 Jornadas)",
                "archivo_origen": f"sha256:{reporte['input_sha256'][:16]}",
                "total_filas": 282,
                "tiempo_ejecucion_s": reporte["tiempos"]["ejecucion_con_caida_y_recuperacion_s"],
                "resumen_particiones": [reporte["pruebas_caos"]]
            }, timeout=10).json()
            reporte["supabase_persistence"] = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            reporte["supabase_persistence"] = f"ERROR: {str(e)}"
        return reporte

    @app.get("/spacecraft/run_lojo_validation")
    def run_lojo_validation(n_bootstrap: int = 500):
        from motor_lojo_ignis import ejecutar_validacion_lojo_completa
        registrar_inicio_lote(18)
        reporte = ejecutar_validacion_lojo_completa(n_bootstrap=n_bootstrap, incluir_estudio_crossover=True)
        registrar_fin_lote(18, reporte["tiempos"]["distribuido_Tp_s"])
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": "IGNIS-mu LOJO (18 Jornadas / 282 Ensayos)",
                "archivo_origen": f"sha256:{reporte['input_sha256'][:16]}",
                "total_filas": reporte["ensayos_totales"],
                "tiempo_ejecucion_s": reporte["tiempos"]["distribuido_Tp_s"],
                "resumen_particiones": [
                    {
                        "validacion_equivalencia": reporte["validacion_equivalencia"],
                        "tiempos": reporte["tiempos"],
                        "punto_equilibrio_282_ensayos": reporte["punto_equilibrio_282_ensayos"],
                        "modelos_lojo": reporte["modelos_lojo"]
                    }
                ]
            }, timeout=10).json()
            reporte["supabase_persistence"] = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            reporte["supabase_persistence"] = f"ERROR: {str(e)}"
        return reporte

    @app.get("/spacecraft/process_real_psi23")
    def process_real_psi23(limit: int = 1000):
        if not ray.is_initialized():
            ray.init(address="auto", ignore_reinit_error=True)

        relay = requests.get(f"http://comm-node:8002/comm/relay_psi23?limit={limit}", timeout=20).json()
        payload = relay.get("payload", {})
        filas = payload.get("rows", [])

        if not filas:
            return {"node": "SPACECRAFT_NODE_VM3", "status": "SIN_DATOS", "detalle_earth": payload}

        # Cargar las filas reales en memoria compartida Apache Arrow Plasma (Zero-Copy)
        plasma_ref = ray.put(filas)

        total_filas = len(filas)
        num_particiones = 16
        tamano = max(1, total_filas // num_particiones)

        inicio_t = time.time()
        tareas = []
        for i in range(num_particiones):
            ini = i * tamano
            fin = total_filas if i == (num_particiones - 1) else min(total_filas, (i + 1) * tamano)
            if ini < total_filas:
                tareas.append(procesar_particion_real_psi23.remote(i, plasma_ref, ini, fin))

        resumen = ray.get(tareas)
        tiempo_total = round(time.time() - inicio_t, 4)

        resultado_final = {
            "node": "SPACECRAFT_NODE_VM3",
            "experimento": filas[0].get("c_nombre_experimento", "PSI-23"),
            "archivo_origen": filas[0].get("c_archivo_origen", "desconocido"),
            "total_filas_reales_procesadas": total_filas,
            "particiones_ray": len(tareas),
            "tiempo_ejecucion_s": tiempo_total,
            "resumen_por_particion": resumen
        }
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": resultado_final["experimento"],
                "archivo_origen": resultado_final["archivo_origen"],
                "total_filas": total_filas,
                "tiempo_ejecucion_s": tiempo_total,
                "resumen_particiones": resumen
            }, timeout=10).json()
            resultado_final["supabase_persistence"] = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            resultado_final["supabase_persistence"] = f"ERROR: {str(e)}"
        return resultado_final
        if False:
            return {
                "node": "SPACECRAFT_NODE_VM3",
            "experimento": filas[0].get("c_nombre_experimento", "PSI-23"),
            "archivo_origen": filas[0].get("c_archivo_origen", "desconocido"),
            "total_filas_reales_procesadas": total_filas,
            "particiones_ray": len(tareas),
            "tiempo_ejecucion_s": tiempo_total,
            "resumen_por_particion": resumen
        }

    @ray.remote
    def procesar_archivo_csv_psi159(ruta_csv):
        import csv, os, socket
        nombre_archivo = os.path.basename(ruta_csv)
        filas_contadas = 0
        ion_vals, pta1_vals, efield_vals, pmt1_vals = [], [], [], []
        meta_exp = "PSI-159"

        with open(ruta_csv, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            fila1_meta = next(reader, [])
            fila2_headers = next(reader, [])

            if len(fila1_meta) > 1:
                meta_exp = f"{fila1_meta[1]} | {fila1_meta[2] if len(fila1_meta) > 2 else ''}".strip()

            idx_map = {col.strip(): i for i, col in enumerate(fila2_headers)}
            i_ion = idx_map.get("IonCurrent")
            i_pta1 = idx_map.get("PTA1")
            i_ef = idx_map.get("EfieldVoltage")
            i_pmt1 = idx_map.get("PMT1")

            for row in reader:
                if not row:
                    continue
                filas_contadas += 1
                try:
                    if i_ion is not None and i_ion < len(row):
                        ion_vals.append(float(row[i_ion]))
                    if i_pta1 is not None and i_pta1 < len(row):
                        pta1_vals.append(float(row[i_pta1]))
                    if i_ef is not None and i_ef < len(row):
                        efield_vals.append(float(row[i_ef]))
                    if i_pmt1 is not None and i_pmt1 < len(row):
                        pmt1_vals.append(float(row[i_pmt1]))
                except (ValueError, TypeError):
                    pass

        return {
            "archivo": nombre_archivo,
            "contenedor_ejecutor": socket.gethostname(),
            "metadatos_cabecera": meta_exp,
            "filas_temporales": filas_contadas,
            "promedio_IonCurrent": round(sum(ion_vals) / len(ion_vals), 5) if ion_vals else 0.0,
            "promedio_PTA1_presion": round(sum(pta1_vals) / len(pta1_vals), 5) if pta1_vals else 0.0,
            "promedio_EfieldVoltage": round(sum(efield_vals) / len(efield_vals), 5) if efield_vals else 0.0,
            "pico_PMT1": round(max(pmt1_vals), 5) if pmt1_vals else 0.0
        }

    @app.get("/spacecraft/process_local_psi159")
    def process_local_psi159():
        import glob
        if not ray.is_initialized():
            ray.init(address="auto", ignore_reinit_error=True)

        archivos = sorted(glob.glob("/workspace/psi159_raw/*.csv"))
        if not archivos:
            return {"node": "SPACECRAFT_NODE_VM3", "status": "SIN_ARCHIVOS_EN_PSI159_RAW"}

        t0 = time.time()
        tareas = [procesar_archivo_csv_psi159.remote(ruta) for ruta in archivos]
        resumen_archivos = ray.get(tareas)
        tiempo_total = round(time.time() - t0, 4)

        total_filas = sum(r["filas_temporales"] for r in resumen_archivos)

        estado_db = "NO_SYNC"
        try:
            sync_resp = requests.post("http://earth-node:8001/earth/save_ray_results", json={
                "experimento": "PSI-159 (ACME CFI-G)",
                "archivo_origen": f"{len(archivos)} archivos CSV locales",
                "total_filas": total_filas,
                "tiempo_ejecucion_s": tiempo_total,
                "resumen_particiones": resumen_archivos
            }, timeout=10).json()
            estado_db = sync_resp.get("status", "UNKNOWN")
        except Exception as e:
            estado_db = f"ERROR: {str(e)}"

        return {
            "node": "SPACECRAFT_NODE_VM3",
            "campana": "PSI-159 (ACME CFI-G)",
            "archivos_csv_procesados_en_paralelo": len(archivos),
            "total_filas_temporales_procesadas": total_filas,
            "tiempo_ejecucion_ray_s": tiempo_total,
            "supabase_persistence": estado_db,
            "detalle_por_archivo": resumen_archivos
        }

if __name__ == "__main__":
    port = 8001 if VM_ROLE == "EARTH" else (8002 if VM_ROLE == "COMM" else 8000)
    uvicorn.run(app, host="0.0.0.0", port=port)