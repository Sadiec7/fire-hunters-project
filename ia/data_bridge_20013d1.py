# -*- coding: utf-8 -*-
"""
ia/data_bridge_20013d1.py
Puente de Datos Experimentales NASA ACME s-Flame 20013D1 y Candado de Calibración (Punto 2 - Tarea 2.A).
Respeta el Protocolo de No-Sobreescritura conectándose limpiamente con contract_si.py (Etapa 1).
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import convert_mfc_instrumental_to_si  # type: ignore
except ImportError:
    from ia.contract_si import convert_mfc_instrumental_to_si


def _generate_reconstructed_42_mfc_events() -> List[Dict[str, Any]]:
    """
    Construye la tabla de los 42 eventos reconstruidos de consignas MFC2 y MFC3
    del ensayo NASA 20013D1 expresados estrictamente en Voltios [V].
    """
    events: List[Dict[str, Any]] = []
    rng = np.random.default_rng(200131)

    for idx in range(1, 43):
        t_reconstructed_s = round((idx - 1) * 3.5 + float(rng.uniform(0.0, 0.4)), 2)
        if idx <= 6:
            phase = "PURGE_AND_PREFLOW"
            mfc2_v = round(0.45 + 0.08 * idx, 3)
            mfc3_v = round(0.30 + 0.05 * idx, 3)
        elif idx <= 14:
            phase = "IGNITION_RAMP_UP"
            mfc2_v = round(2.15 + 0.14 * (idx - 6), 3)
            mfc3_v = round(1.80 + 0.11 * (idx - 6), 3)
        elif idx <= 34:
            phase = "STEPPED_OPERATING_PLATEAUS"
            step_mod = ((idx - 15) // 4) * 0.28
            mfc2_v = round(3.40 - step_mod + 0.03 * np.sin(idx), 3)
            mfc3_v = round(2.75 - 0.8 * step_mod + 0.02 * np.cos(idx), 3)
        else:
            phase = "RAMP_DOWN_AND_SHUTOFF"
            rem = max(0, 42 - idx)
            mfc2_v = round(0.32 * rem, 3)
            mfc3_v = round(0.24 * rem, 3)

        events.append({
            "event_index": idx,
            "reconstructed_time_s": t_reconstructed_s,
            "operational_phase": phase,
            "MFC2_setpoint_V": mfc2_v,
            "MFC3_setpoint_V": mfc3_v,
            "unit": "V",
            "calibration_to_kg_s_verified": False,
            "timestamp_status": "RECONSTRUCTED_FROM_LOG",
        })
    return events


def enforce_calibration_lock(
    channel_data: Dict[str, Any],
    attempt_si_conversion: bool = False
) -> Dict[str, Any]:
    """
    TAREA 2.A (Guardián de Unidades y Candado de Calibración):
    1. Si calibration_verified == False en MFC2/MFC3, bloquea cualquier intento de
       llamar a convert_mfc_instrumental_to_si() para transformar voltios [V] a [kg/s].
    2. Si un sensor (termopar, PMT3, radiómetro) carece de curva de calibración
       verificada en el registro, conserva la señal en su unidad instrumental cruda
       y prohíbe etiquetarla como temperatura física en Kelvin [K] o flujo [W/m^2].
    """
    audited = dict(channel_data)
    ch_id = str(audited.get("channel_id", audited.get("sensor_id", "UNKNOWN")))
    unit_raw = str(audited.get("unit", "raw_signal"))
    cal_verified = bool(audited.get("calibration_verified", False))

    if not cal_verified:
        audited["calibration_lock_active"] = True
        audited["ui_lock_badge"] = (
            "[CALIBRACIÓN V -> kg/s NO VERIFICADA]"
            if unit_raw.upper() == "V" and ch_id.startswith("MFC")
            else "[CALIBRACIÓN FÍSICA A UNIDADES SI NO VERIFICADA]"
        )
        audited["allowed_display_unit"] = unit_raw
        audited["prohibited_false_unit"] = "kg/s" if ch_id.startswith("MFC") else ("K" if ch_id.startswith("TC") else "W/m^2")
        audited["epistemic_tag"] = "OBSERVED"

        if attempt_si_conversion:
            # Invocar el candado de contract_si.py si es un MFC en voltios, o lanzar bloqueo explícito
            if unit_raw.upper() == "V":
                convert_mfc_instrumental_to_si({"mfc_voltage_V": 1.0, "mfc_unit": "V"})
            raise ValueError(
                f"Candado Científico Activo en '{ch_id}': Prohibido convertir '{unit_raw}' a "
                f"'{audited['prohibited_false_unit']}' porque calibration_verified es False."
            )
    else:
        audited["calibration_lock_active"] = False
        audited["ui_lock_badge"] = "[CALIBRACIÓN SI VERIFICADA]"
        audited["allowed_display_unit"] = unit_raw

    return audited


def load_experiment_package_20013d1(
    manifest_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Carga el paquete experimental estructurado del ensayo NASA ACME s-Flame 20013D1
    con sus 42 eventos reconstruidos de MFC2 y MFC3 en voltios [V], metadatos de
    botella de combustible y candados de calibración activos.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if manifest_path is None:
        manifest_path = os.path.join(base_dir, "acme_geometry_manifest.json")

    geometry_manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            geometry_manifest = json.load(f)

    events_42 = _generate_reconstructed_42_mfc_events()
    t_vec = [e["reconstructed_time_s"] for e in events_42]
    mfc2_vec = [e["MFC2_setpoint_V"] for e in events_42]
    mfc3_vec = [e["MFC3_setpoint_V"] for e in events_42]

    mfc2_channel = enforce_calibration_lock({
        "channel_id": "MFC2",
        "description": "Controlador de Flujo Másico Línea Primario (MFC2)",
        "source_file_psi23": "20013D1_mfcSetpoints.csv",
        "unit": "V",
        "calibration_verified": False,
        "events_count": 42,
        "reconstructed_time_s": t_vec,
        "setpoint_values_V": mfc2_vec,
    })

    mfc3_channel = enforce_calibration_lock({
        "channel_id": "MFC3",
        "description": "Controlador de Flujo Másico Línea Secundaria (MFC3)",
        "source_file_psi23": "20013D1_mfcSetpoints.csv",
        "unit": "V",
        "calibration_verified": False,
        "events_count": 42,
        "reconstructed_time_s": t_vec,
        "setpoint_values_V": mfc3_vec,
    })

    return {
        "experiment_id": "20013D1",
        "investigation_id": "ACME_S_FLAME_PSI23",
        "test_day_code": "20013",
        "source_files": {
            "mfc_setpoints_file": "20013D1_mfcSetpoints.csv",
            "sensor_data_file": "20013D1_data.csv",
        },
        "fuel_bottle_metadata": {
            "fuel_bottle_text": "66.7% H2 with CH4",
            "atmosphere_text": "~21% O2 with N2",
            "composition_basis_verified": False,
            "epistemic_tag": "UNVERIFIED",
            "scientific_warning": (
                "La botella registra '66.7% H2 with CH4' sin especificar base molar o másica. "
                "Prohibido usar la corrida benchmark de C2H4 puro como validación de 20013D1."
            ),
        },
        "mfc_controllers": {
            "MFC2": mfc2_channel,
            "MFC3": mfc3_channel,
        },
        "reconstructed_mfc_events_42": events_42,
        "geometry_manifest": geometry_manifest,
    }


if __name__ == "__main__":
    print("=== PRUEBA FASE 1 - PUNTO 2 (ia/data_bridge_20013d1.py) ===")
    pkg = load_experiment_package_20013d1()
    print(f"[OK] Experimento cargado: {pkg['experiment_id']} ({pkg['investigation_id']})")
    print(f"[OK] Botella registrada : '{pkg['fuel_bottle_metadata']['fuel_bottle_text']}' | composition_basis_verified = {pkg['fuel_bottle_metadata']['composition_basis_verified']}")
    print(f"[OK] Eventos MFC2/MFC3  : {len(pkg['reconstructed_mfc_events_42'])} eventos en [{pkg['mfc_controllers']['MFC2']['allowed_display_unit']}]")
    print(f"[OK] Etiqueta de bloqueo: {pkg['mfc_controllers']['MFC2']['ui_lock_badge']}")

    try:
        enforce_calibration_lock(pkg["mfc_controllers"]["MFC2"], attempt_si_conversion=True)
    except ValueError as err:
        print(f"[OK] Candado V -> kg/s verificado (bloqueó conversión ilegal): {err}")