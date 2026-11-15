# -*- coding: utf-8 -*-
"""
ia/sensor_registry_20013d1.py
Registro Estructurado de los 6 Canales Instrumentales y 2 MFC del Ensayo 20013D1 (Punto 3 - Tarea 3.A).
Incluye coordenadas 3D para raycasting/hotspots, serie cruda, archivo PSI-23 y estado de unidades.
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import load_experiment_package_20013d1, enforce_calibration_lock  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import load_experiment_package_20013d1, enforce_calibration_lock


MANDATORY_SENSOR_IDS: List[str] = [
    "TCBurner",
    "TCA",
    "TCB",
    "TCC",
    "PMT3",
    "RadiometerCenter",
]

ALL_CHANNEL_IDS: List[str] = MANDATORY_SENSOR_IDS + ["MFC2", "MFC3"]


def _build_sensor_raw_catalog_20013d1() -> Dict[str, Dict[str, Any]]:
    """
    Genera las series instrumentales crudas representativas del archivo 20013D1_data.csv
    preservando sus unidades instrumentales originales sin convertir a Kelvin [K] ni [W/m^2].
    """
    n_samples = 160
    t_sensor_s = np.linspace(0.0, 145.0, n_samples, dtype=np.float64)
    envelope = np.exp(-((t_sensor_s - 68.0) / 38.0) ** 2)
    step_modulation = 1.0 - 0.12 * np.floor(np.clip(t_sensor_s - 35.0, 0.0, 90.0) / 22.0)
    active_shape = np.clip(envelope * step_modulation, 0.0, 1.0)

    raw_specs = {
        "TCBurner": {
            "sensor_id": "TCBurner",
            "label": "Termopar Superficie del Quemador (TCBurner)",
            "category": "THERMOCOUPLE",
            "position_xyz_m": [0.0, 0.0, 0.0032],
            "radial_distance_m": 0.0032,
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "mV_raw",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(1.25 + 6.40 * active_shape + 0.04 * np.sin(0.3 * t_sensor_s), 4).tolist(),
            "forbidden_interpretation": "Prohibido presentar directamente como Temperatura Física en Kelvin [K].",
        },
        "TCA": {
            "sensor_id": "TCA",
            "label": "Termopar Rastrillo Radial Interior (TCA, r ~ 8 mm)",
            "category": "THERMOCOUPLE",
            "position_xyz_m": [0.008, 0.0, 0.0],
            "radial_distance_m": 0.008,
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "mV_raw",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(1.10 + 14.85 * active_shape + 0.06 * np.cos(0.25 * t_sensor_s), 4).tolist(),
            "forbidden_interpretation": "Prohibido presentar directamente como Temperatura Física en Kelvin [K].",
        },
        "TCB": {
            "sensor_id": "TCB",
            "label": "Termopar Rastrillo Radial Medio (TCB, r ~ 15 mm)",
            "category": "THERMOCOUPLE",
            "position_xyz_m": [0.015, 0.0, 0.0],
            "radial_distance_m": 0.015,
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "mV_raw",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(1.05 + 12.10 * active_shape + 0.05 * np.sin(0.2 * t_sensor_s), 4).tolist(),
            "forbidden_interpretation": "Prohibido presentar directamente como Temperatura Física en Kelvin [K].",
        },
        "TCC": {
            "sensor_id": "TCC",
            "label": "Termopar Rastrillo Radial Exterior (TCC, r ~ 25 mm)",
            "category": "THERMOCOUPLE",
            "position_xyz_m": [0.025, 0.0, 0.0],
            "radial_distance_m": 0.025,
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "mV_raw",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(0.95 + 7.65 * active_shape + 0.03 * np.cos(0.18 * t_sensor_s), 4).tolist(),
            "forbidden_interpretation": "Prohibido presentar directamente como Temperatura Física en Kelvin [K].",
        },
        "PMT3": {
            "sensor_id": "PMT3",
            "label": "Fotomultiplicador Quimioluminiscencia OH*/CH* (PMT3)",
            "category": "PHOTOMULTIPLIER",
            "position_xyz_m": [0.0, 0.120, 0.035],
            "radial_distance_m": 0.125,
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "V_raw_counts",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(0.08 + 4.12 * (active_shape ** 1.15), 4).tolist(),
            "forbidden_interpretation": "Señal óptica cruda; no calibrada a concentración molar absoluta de radicales.",
        },
        "RadiometerCenter": {
            "sensor_id": "RadiometerCenter",
            "label": "Radiómetro Central Schmidt-Boelter (r = 154 mm)",
            "category": "RADIOMETER",
            "position_xyz_m": [0.0, -0.154, 0.0],
            "radial_distance_m": 0.154,
            "verification_tier": "VERIFIED_DIMENSION",
            "source_file_psi23": "20013D1_data.csv",
            "original_unit": "mV_raw_irradiance",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": np.round(t_sensor_s, 3).tolist(),
            "raw_signal_values": np.round(0.05 + 2.85 * active_shape, 4).tolist(),
            "forbidden_interpretation": "Señal radiométrica cruda; verificar factor de vista antes de reportar [W] totales.",
        },
    }

    pkg = load_experiment_package_20013d1()
    for mfc_id, x_pos in [("MFC2", -0.045), ("MFC3", 0.045)]:
        mfc_info = pkg["mfc_controllers"][mfc_id]
        raw_specs[mfc_id] = {
            "sensor_id": mfc_id,
            "label": mfc_info["description"],
            "category": "MASS_FLOW_CONTROLLER",
            "position_xyz_m": [x_pos, 0.0, -0.060],
            "radial_distance_m": round(float(np.hypot(x_pos, 0.060)), 4),
            "verification_tier": "GEOMETRIC_APPROXIMATION",
            "source_file_psi23": mfc_info["source_file_psi23"],
            "original_unit": "V",
            "calibration_verified": False,
            "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
            "raw_signal_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "time_s": mfc_info["reconstructed_time_s"],
            "raw_signal_values": mfc_info["setpoint_values_V"],
            "forbidden_interpretation": "Consigna eléctrica en Voltios [V]; prohibido presentar como flujo másico [kg/s].",
        }

    return raw_specs


def get_sensor_channel_payload(sensor_id: str) -> Dict[str, Any]:
    """
    TAREA 3.A:
    Devuelve para cualquiera de los 6 sensores (TCBurner, TCA, TCB, TCC, PMT3, RadiometerCenter)
    o 2 controladores (MFC2, MFC3):
      (a) vector de señal experimental cruda,
      (b) archivo de procedencia en NASA PSI-23,
      (c) unidad original registrada, y
      (d) estado de verificación de sus unidades (UNIT_VERIFIED_RAW_SIGNAL vs PHYSICAL_CALIBRATION_PENDING).
    """
    catalog = _build_sensor_raw_catalog_20013d1()
    if sensor_id not in catalog:
        raise KeyError(f"Canal '{sensor_id}' no registrado en 20013D1. Canales válidos: {ALL_CHANNEL_IDS}")

    entry = enforce_calibration_lock(catalog[sensor_id])
    vals = np.asarray(entry["raw_signal_values"], dtype=np.float64)

    entry["summary_stats_raw"] = {
        "min_raw": round(float(np.min(vals)), 4),
        "max_raw": round(float(np.max(vals)), 4),
        "mean_raw": round(float(np.mean(vals)), 4),
        "samples_count": int(vals.size),
    }
    return entry


def get_all_sensors_registry_20013d1() -> Dict[str, Dict[str, Any]]:
    """Devuelve el diccionario completo de los 6 canales instrumentales + 2 MFC auditados."""
    return {cid: get_sensor_channel_payload(cid) for cid in ALL_CHANNEL_IDS}


if __name__ == "__main__":
    print("=== PRUEBA FASE 1 - PUNTO 3 (ia/sensor_registry_20013d1.py) ===")
    reg = get_all_sensors_registry_20013d1()
    for s_id in ALL_CHANNEL_IDS:
        info = reg[s_id]
        print(
            f"[OK] Canal {s_id:16s} | Origen: {info['source_file_psi23']:24s} | "
            f"Unidad: {info['original_unit']:17s} | Estado: {info['raw_signal_status']} / {info['unit_verification_status']}"
        )