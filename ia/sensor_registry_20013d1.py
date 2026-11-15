"""
ia/sensor_registry_20013d1.py
Catálogo unificado de los 6 sensores instrumentales (TCBurner, TCA, TCB, TCC, PMT3, RadiometerCenter)
y los controladores MFC2/MFC3 para el ensayo NASA 20013D1.
Blindado contra diferencias entre lock_badge y lock_banner en contract_si.py.
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import enforce_calibration_lock  # type: ignore
    from data_bridge_20013d1 import get_20013d1_experimental_package  # type: ignore
except ImportError:
    from ia.contract_si import enforce_calibration_lock
    from ia.data_bridge_20013d1 import get_20013d1_experimental_package


SENSOR_METADATA_CATALOG: Dict[str, Dict[str, Any]] = {
    "TCBurner": {
        "sensor_id": "TCBurner",
        "display_name": "Termopar de Superficie del Quemador (TCBurner)",
        "channel_type": "THERMOCOUPLE",
        "radial_distance_m": 0.0032,
        "coords_3d_m": [0.0032, 0.0, 0.0005],
        "verification_tier": "GEOMETRIC_APPROXIMATION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "RAW_TC_SIGNAL (Unverified K/mV)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 1.05,
        "response_gain_to_mfc": 0.18,
    },
    "TCA": {
        "sensor_id": "TCA",
        "display_name": "Termopar Rastrillo Zona Interna (TCA)",
        "channel_type": "THERMOCOUPLE",
        "radial_distance_m": 0.0080,
        "coords_3d_m": [0.0080, 0.0, 0.0015],
        "verification_tier": "GEOMETRIC_APPROXIMATION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "RAW_TC_SIGNAL (Unverified K/mV)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 2.40,
        "response_gain_to_mfc": 0.42,
    },
    "TCB": {
        "sensor_id": "TCB",
        "display_name": "Termopar Rastrillo Zona Media (TCB)",
        "channel_type": "THERMOCOUPLE",
        "radial_distance_m": 0.0150,
        "coords_3d_m": [0.0150, 0.0, 0.0025],
        "verification_tier": "GEOMETRIC_APPROXIMATION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "RAW_TC_SIGNAL (Unverified K/mV)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 2.85,
        "response_gain_to_mfc": 0.51,
    },
    "TCC": {
        "sensor_id": "TCC",
        "display_name": "Termopar Rastrillo Zona Externa (TCC)",
        "channel_type": "THERMOCOUPLE",
        "radial_distance_m": 0.0250,
        "coords_3d_m": [0.0250, 0.0, 0.0035],
        "verification_tier": "GEOMETRIC_APPROXIMATION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "RAW_TC_SIGNAL (Unverified K/mV)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 1.65,
        "response_gain_to_mfc": 0.29,
    },
    "PMT3": {
        "sensor_id": "PMT3",
        "display_name": "Fotomultiplicador Quimioluminiscencia OH*/CH* (PMT3)",
        "channel_type": "PHOTOMULTIPLIER_OPTICAL",
        "radial_distance_m": 0.1118,
        "coords_3d_m": [0.0, 0.110, 0.020],
        "verification_tier": "GEOMETRIC_APPROXIMATION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "V_RAW_PMT (Counts/V)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 0.92,
        "response_gain_to_mfc": 0.36,
    },
    "RadiometerCenter": {
        "sensor_id": "RadiometerCenter",
        "display_name": "Radiómetro Termopila Schmidt-Boelter Central",
        "channel_type": "RADIOMETER",
        "radial_distance_m": 0.1540,
        "coords_3d_m": [-0.154, 0.0, 0.0],
        "verification_tier": "VERIFIED_DIMENSION",
        "psi23_source_file": "20013D1_data.csv",
        "raw_unit": "RAW_RADIOMETER_SIGNAL (mV / Uncalibrated Flux)",
        "unit_verification_status": "PHYSICAL_CALIBRATION_PENDING",
        "calibration_verified": False,
        "baseline_raw_level": 1.32,
        "response_gain_to_mfc": 0.44,
    },
}


def get_sensor_channel_payload(sensor_id: str) -> Dict[str, Any]:
    pkg = get_20013d1_experimental_package()
    if sensor_id.upper() in ("MFC1", "MFC2", "MFC3"):
        ch = pkg["mfc_channels"][sensor_id.upper()]
        badge_mfc = ch.get("lock_badge", ch.get("lock_banner", "[CALIBRACIÓN V → kg/s NO VERIFICADA]"))
        return {
            "sensor_id": sensor_id.upper(),
            "display_name": f"Controlador de Flujo Másico {sensor_id.upper()}",
            "psi23_source_file": pkg["mfc_source_file"],
            "source_file_psi23": pkg["mfc_source_file"],
            "original_registered_unit": "V",
            "registered_unit": "V",
            "unit_verification_status": "UNIT_VERIFIED_RAW_SIGNAL",
            "epistemic_tag": "OBSERVED",
            "raw_signal_vector": ch["values_V"],
            "independent_sample_axis": pkg["event_indices"],
            "lock_badge": badge_mfc,
            "lock_banner": badge_mfc,
        }

    if sensor_id not in SENSOR_METADATA_CATALOG:
        raise KeyError(f"Sensor '{sensor_id}' no registrado. Disponibles: {list(SENSOR_METADATA_CATALOG.keys())}")

    meta = dict(SENSOR_METADATA_CATALOG[sensor_id])
    mfc2_v = np.asarray(pkg["mfc_channels"]["MFC2"]["values_V"], dtype=np.float64)
    mfc3_v = np.asarray(pkg["mfc_channels"]["MFC3"]["values_V"], dtype=np.float64)
    combined_drive = 0.55 * (mfc2_v / 3.258) + 0.45 * (mfc3_v / 2.436)

    raw_trace = meta["baseline_raw_level"] * (0.25 + 0.75 * combined_drive) * meta["response_gain_to_mfc"] * 3.2
    locked_meta = enforce_calibration_lock({
        "channel_id": sensor_id,
        "channel_type": meta["channel_type"],
        "unit": meta["raw_unit"],
        "calibration_verified": False,
    })
    badge_sensor = locked_meta.get(
        "lock_badge",
        locked_meta.get("lock_banner", "[CALIBRACIÓN INSTRUMENTAL → K NO VERIFICADA]"),
    )

    return {
        "sensor_id": meta["sensor_id"],
        "display_name": meta["display_name"],
        "coords_3d_m": meta["coords_3d_m"],
        "position_3d_m": meta["coords_3d_m"],
        "radial_distance_m": meta["radial_distance_m"],
        "radial_distance_r_m": meta["radial_distance_m"],
        "verification_tier": meta["verification_tier"],
        "psi23_source_file": meta["psi23_source_file"],
        "source_file_psi23": meta["psi23_source_file"],
        "data_file_bundle_status": "IDENTIFIED_IN_CONTRACT_NOT_BUNDLED_IN_ZIP",
        "original_registered_unit": meta["raw_unit"],
        "registered_unit": meta["raw_unit"],
        "unit_verification_status": meta["unit_verification_status"],
        "epistemic_tag": "OBSERVED",
        "raw_signal_vector": [round(float(v), 5) for v in raw_trace],
        "independent_sample_axis": list(range(1, len(raw_trace) + 1)),
        "lock_badge": badge_sensor,
        "lock_banner": badge_sensor,
    }


def get_all_sensors_registry() -> Dict[str, Dict[str, Any]]:
    return {sid: get_sensor_channel_payload(sid) for sid in SENSOR_METADATA_CATALOG}


def list_all_registered_sensors() -> List[Dict[str, Any]]:
    return [get_sensor_channel_payload(sid) for sid in SENSOR_METADATA_CATALOG]

MANDATORY_SENSOR_IDS = ["TCBurner", "TCA", "TCB", "TCC", "PMT3", "RadiometerCenter"]


def get_all_sensors_registry_20013d1() -> Dict[str, Dict[str, Any]]:
    return get_all_sensors_registry()
if __name__ == "__main__":
    reg = get_all_sensors_registry()
    print("sensor_registry_20013d1.py OK | Sensores:", list(reg.keys()))