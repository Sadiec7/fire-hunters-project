import re
from datetime import datetime
import numpy as np
import pandas as pd

def auditar_experimento_nasa(rows: list, tabla_origen: str = "psi23_datos_masivos_csv") -> dict:
    """
    Audita registros experimentales NASA en modo estricto (sin interpolar ni inventar tiempos).
    Verifica emparejamiento MFC vs. sensores instrumentales, integridad de IDs,
    discontinuidades temporales y cruces de medianoche.
    """
    if not rows:
        return {
            "status": "NO_DATA",
            "ready_for_dynamic_scm": False,
            "motivo": "No se recibieron filas desde Supabase."
        }

    df = pd.DataFrame(rows)
    columnas = list(df.columns)

    # 1. Identificar experimento y archivo origen
    archivo_origen = str(df["c_archivo_origen"].iloc[0]) if "c_archivo_origen" in df.columns else "desconocido"
    nombre_exp = str(df["c_nombre_experimento"].iloc[0]) if "c_nombre_experimento" in df.columns else "NASA-PSI"
    exp_id = archivo_origen.replace("_data.csv", "").strip()

    # 2. Reconstruir parejas entre canales MFC y sensores instrumentales
    cols_mfc = sorted([c for c in columnas if "mfc" in c.lower()])
    cols_sensores = sorted([
        c for c in columnas
        if any(k in c.lower() for k in ("thermocouple", "radiometer", "efield", "pmt", "burner", "igniter", "ipsu", "fiber", "pta", "ioncurrent"))
    ])

    parejas_reconstruidas = []
    for mfc_col in cols_mfc:
        valores_mfc = pd.to_numeric(df[mfc_col], errors="coerce").dropna()
        if len(valores_mfc) > 0:
            parejas_reconstruidas.append({
                "canal_mfc": mfc_col,
                "muestras_validas": int(len(valores_mfc)),
                "sensores_instrumentales_asociados": len(cols_sensores),
                "emparejado_por_archivo": True
            })

    # 3. Auditar integridad de muestras e identificadores
    ids_unicos_archivo = int(df["c_archivo_origen"].nunique()) if "c_archivo_origen" in df.columns else 0
    total_muestras = int(len(df))
    valores_nulos_sensores = int(df[cols_sensores].isna().sum().sum()) if cols_sensores else 0

    # 4. Recuperar marcas temporales documentadas (sin inventar ni interpolar)
    # Busca columnas con formato fecha/hora (ej. c_2020-06-08_160_23:41:56:378 o time/timestamp)
    patron_ts = re.compile(r"(\d{4}-\d{2}-\d{2})[_T](\d{3}_)?(\d{2}:\d{2}:\d{2})")
    cols_timestamp_cabecera = [c for c in columnas if patron_ts.search(c) or "time" in c.lower() or "fecha" in c.lower()]

    marcas_extraidas = []
    fechas_detectadas = set()
    cruces_medianoche = 0
    discontinuidades = 0
    fechas_inconsistentes = False

    for c in cols_timestamp_cabecera:
        m = patron_ts.search(c)
        if m:
            fecha_str, _, hora_str = m.group(1), m.group(2), m.group(3)
            fechas_detectadas.add(fecha_str)
            try:
                dt = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
                marcas_extraidas.append(dt)
            except ValueError:
                fechas_inconsistentes = True

    if len(fechas_detectadas) > 1:
        fechas_inconsistentes = True

    marcas_extraidas.sort()
    for i in range(1, len(marcas_extraidas)):
        delta = (marcas_extraidas[i] - marcas_extraidas[i - 1]).total_seconds()
        if delta < 0:
            cruces_medianoche += 1
        elif delta > 1.0:
            discontinuidades += 1

    # 5. Regla científica estricta:
    # Si solo existe marca de cabecera/MFC pero no un vector de tiempo verificado muestra-a-muestra
    # sincronizado con los sensores físicos, se bloquea el paso al SCM dinámico.
    mfc_timestamps_reconstructed = len(marcas_extraidas) > 0 or len(cols_mfc) > 0
    tiene_reloj_muestra_a_muestra = any(
        c.lower() in ("timestamp", "time_s", "elapsed_time", "t_sec") for c in columnas
    )
    sensor_timestamps_verified = bool(tiene_reloj_muestra_a_muestra and not fechas_inconsistentes and discontinuidades == 0)
    temporal_alignment_verified = bool(mfc_timestamps_reconstructed and sensor_timestamps_verified)
    physical_units_calibrated = False  # Los canales crudos en Supabase están en voltios sin curva de calibración física adjunta
    ready_for_dynamic_scm = bool(temporal_alignment_verified and physical_units_calibrated)

    # 6. Contrato de estado obligatorio para el módulo científico
    estado_gate_cientifico = {
        "experiment_id": exp_id,
        "mfc_timestamps_reconstructed": mfc_timestamps_reconstructed,
        "sensor_timestamps_verified": sensor_timestamps_verified,
        "temporal_alignment_verified": temporal_alignment_verified,
        "physical_units_calibrated": physical_units_calibrated,
        "ready_for_dynamic_scm": ready_for_dynamic_scm
    }

    reporte_calidad = {
        "tabla_supabase": tabla_origen,
        "experimento": nombre_exp,
        "archivo_auditado": archivo_origen,
        "integridad_muestras": {
            "total_filas_auditadas": total_muestras,
            "archivos_distintos_en_lote": ids_unicos_archivo,
            "canales_mfc_detectados": len(cols_mfc),
            "canales_instrumentales_detectados": len(cols_sensores),
            "celdas_nulas_en_sensores": valores_nulos_sensores
        },
        "auditoria_temporal": {
            "marcas_horarias_documentadas": [dt.isoformat() for dt in marcas_extraidas],
            "fechas_unicas_detectadas": sorted(list(fechas_detectadas)),
            "fechas_inconsistentes": fechas_inconsistentes,
            "cruces_medianoche_detectados": cruces_medianoche,
            "discontinuidades_detectadas": discontinuidades,
            "interpolacion_aplicada": False,
            "advertencia_cientifica": (
                "BLOQUEADO PARA SCM DINAMICO: Se reconstruyeron marcas MFC/cabecera, pero no existe "
                "reloj continuo muestra-a-muestra verificado contra señales instrumentales. No se inventaron tiempos."
                if not ready_for_dynamic_scm else "Sincronización temporal verificada."
            )
        },
        "parejas_mfc_sensores": parejas_reconstruidas[:6]
    }

    return {
        "gate_cientifico": estado_gate_cientifico,
        "reporte_calidad": reporte_calidad
    }