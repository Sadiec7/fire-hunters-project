# -*- coding: utf-8 -*-
"""
ia/time_sync_auditor.py
Auditor de Sincronización Temporal entre Eventos MFC Reconstruidos y Sensores (Punto 6 - Tarea 6.A).
Bloquea cualquier animación continua falsa cuando la alineación de relojes no está verificada.
"""

import os
import sys
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import load_experiment_package_20013d1  # type: ignore
    from sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import load_experiment_package_20013d1
    from ia.sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS


def audit_temporal_alignment(exp_id: str = "20013D1") -> Dict[str, Any]:
    """
    TAREA 6.A:
    Audita los vectores temporales de los 42 eventos reconstruidos de MFC2/MFC3 frente a
    los vectores temporales de las señales instrumentales (TCBurner ... RadiometerCenter)
    y exporta el bloque obligatorio `synchronization_status`.
    """
    pkg = load_experiment_package_20013d1()
    sensors = get_all_sensors_registry_20013d1()

    events_42 = pkg["reconstructed_mfc_events_42"]
    mfc_times = [float(e["reconstructed_time_s"]) for e in events_42]

    sensor_windows = {}
    for s_id in MANDATORY_SENSOR_IDS:
        t_arr = sensors[s_id]["time_s"]
        sensor_windows[s_id] = {
            "t_start_s": float(t_arr[0]),
            "t_end_s": float(t_arr[-1]),
            "samples_count": len(t_arr),
            "clock_domain": "INSTRUMENTAL_DAQ_CLOCK_UNALIGNED",
        }

    synchronization_status = {
        "experiment_id": exp_id,
        "mfc_timestamps_status": "RECONSTRUCTED_FROM_LOG",
        "mfc_reconstructed_events_count": len(events_42),
        "mfc_time_span_s": [round(min(mfc_times), 2), round(max(mfc_times), 2)],
        "sensor_mfc_alignment_verified": False,
        "allow_realtime_combustion_playback": False,
        "allowed_ui_interaction_mode": "DISCRETE_MFC_EVENT_STEPPER_AND_INDEPENDENT_TIME_AXES",
        "sync_warning_message": (
            "Las marcas temporales de los MFC son reconstruidas y su correspondencia exacta "
            "con las señales instrumentales no está verificada. Se prohíbe animar la evolución "
            "como reproducción física continua de la combustión."
        ),
        "sensor_daq_windows": sensor_windows,
    }
    return synchronization_status


if __name__ == "__main__":
    print("=== PRUEBA FASE 2 - PUNTO 6 (ia/time_sync_auditor.py) ===")
    sync_rep = audit_temporal_alignment("20013D1")
    print(f"[OK] mfc_timestamps_status            : {sync_rep['mfc_timestamps_status']} ({sync_rep['mfc_reconstructed_events_count']} eventos)")
    print(f"[OK] sensor_mfc_alignment_verified    : {sync_rep['sensor_mfc_alignment_verified']}")
    print(f"[OK] allow_realtime_combustion_playback: {sync_rep['allow_realtime_combustion_playback']}")
    print(f"[OK] Advertencia obligatoria          : {sync_rep['sync_warning_message']}")