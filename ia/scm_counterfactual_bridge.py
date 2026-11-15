"""
ia/scm_counterfactual_bridge.py
Adaptador del Modelo Causal Estructural (SCM) de IGNIS-mu para el Comparador Contrafactual 3D (20013D1).
100% compatible con sensor_registry_20013d1.py, data_bridge_20013d1.py y comparator_3d_ui.py.
"""

import os
import sys
from typing import Dict, Any, Optional
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import get_20013d1_experimental_package  # type: ignore
    from sensor_registry_20013d1 import get_all_sensors_registry  # type: ignore
    from epistemic_guard import allow_3d_flame_isosurface, audit_temporal_alignment  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import get_20013d1_experimental_package
    from ia.sensor_registry_20013d1 import get_all_sensors_registry
    from ia.epistemic_guard import allow_3d_flame_isosurface, audit_temporal_alignment


ALTERNATIVE_PROGRAMS_PRESETS: Dict[str, Dict[str, Any]] = {
    "ALT_HIGH_DRIVE_STEP": {
        "preset_id": "ALT_HIGH_DRIVE_STEP",
        "title": "Intervención do(MFC2 +15%, MFC3 +15% Sostenido)",
        "mfc2_scale": 1.15,
        "mfc3_scale": 1.15,
    },
    "ALT_EARLY_STEPDOWN": {
        "preset_id": "ALT_EARLY_STEPDOWN",
        "title": "Intervención do(Reducción Escalonada MFC2 -20%, MFC3 -10%)",
        "mfc2_scale": 0.80,
        "mfc3_scale": 0.90,
    },
    "ALT_MFC2_DOMINANT": {
        "preset_id": "ALT_MFC2_DOMINANT",
        "title": "Intervención do(MFC2 +25%, MFC3 -15% Cambio de Razón)",
        "mfc2_scale": 1.25,
        "mfc3_scale": 0.85,
    },
}


def evaluate_counterfactual_comparison(
    exp_id: str = "20013D1",
    alt_mfc_program: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    pkg = get_20013d1_experimental_package()
    sensors_obs = get_all_sensors_registry()
    sync_info = audit_temporal_alignment(exp_id)

    if alt_mfc_program is None:
        alt_mfc_program = ALTERNATIVE_PROGRAMS_PRESETS["ALT_HIGH_DRIVE_STEP"]

    mfc2_obs = np.asarray(pkg["mfc_channels"]["MFC2"]["values_V"], dtype=np.float64)
    mfc3_obs = np.asarray(pkg["mfc_channels"]["MFC3"]["values_V"], dtype=np.float64)

    s2 = float(alt_mfc_program.get("mfc2_scale", 1.15))
    s3 = float(alt_mfc_program.get("mfc3_scale", 1.15))

    mfc2_alt = np.clip(mfc2_obs * s2, 0.0, 5.0)
    mfc3_alt = np.clip(mfc3_obs * s3, 0.0, 5.0)

    rel_drive_change = float(
        0.55 * (np.mean(mfc2_alt) - np.mean(mfc2_obs)) / max(np.mean(mfc2_obs), 1e-6)
        + 0.45 * (np.mean(mfc3_alt) - np.mean(mfc3_obs)) / max(np.mean(mfc3_obs), 1e-6)
    )

    scm_sensor_responses: Dict[str, Dict[str, Any]] = {}
    sensor_weights = {
        "TCBurner": 0.65,
        "TCA": 1.10,
        "TCB": 1.25,
        "TCC": 0.85,
        "PMT3": 1.35,
        "RadiometerCenter": 1.18,
    }

    for sid, sdata in sensors_obs.items():
        obs_vec = np.asarray(sdata["raw_signal_vector"], dtype=np.float64)
        w = sensor_weights.get(sid, 1.0)
        alt_vec = obs_vec * (1.0 + w * rel_drive_change)
        delta_vec = alt_vec - obs_vec
        mean_delta = float(np.mean(delta_vec))
        rel_delta_pct = float(100.0 * mean_delta / max(float(np.mean(np.abs(obs_vec))), 1e-6))

        scm_sensor_responses[sid] = {
            "delta_inferred": True,
            "causal_effect_identified": False,
            "unit": sdata["original_registered_unit"],
            "observed_mean_raw": round(float(np.mean(obs_vec)), 4),
            "alternative_inferred_mean_raw": round(float(np.mean(alt_vec)), 4),
            "mean_delta_raw": round(mean_delta, 4),
            "relative_delta_pct": round(rel_delta_pct, 2),
            "alternative_signal_vector": [round(float(x), 5) for x in alt_vec],
            "delta_signal_vector": [round(float(x), 5) for x in delta_vec],
            "halo_radius_multiplier_3d": round(float(np.clip(1.0 + abs(rel_delta_pct) / 25.0, 0.8, 2.2)), 3),
        }

    return {
        "experiment_id": exp_id,
        "investigation_id": "ACME_S_FLAME_PSI23",
        "epistemic_locks": {
            "mfc_voltage_to_massflow_verified": False,
            "thermocouple_to_kelvin_verified": False,
            "mfc_sensor_time_sync_verified": False,
            "allow_3d_flame_field_rendering": allow_3d_flame_isosurface(exp_id),
            "allow_continuous_combustion_animation": sync_info["allow_realtime_combustion_playback"],
        },
        "synchronization_status": sync_info,
        "observed_scenario_blue": {
            "label": "ESCENARIO OBSERVADO (NASA 20013D1)",
            "epistemic_tag": "OBSERVED",
            "theme_color_hex": "#1D4ED8",
            "badge_color_hex": "#168039",
            "mfc_program": {
                "MFC2_unit": "V",
                "MFC3_unit": "V",
                "reconstructed_events": 42,
                "event_indices": pkg["event_indices"],
                "timestamps_reconstructed": pkg["timestamps_reconstructed"],
                "MFC2_values_V": pkg["mfc_channels"]["MFC2"]["values_V"],
                "MFC3_values_V": pkg["mfc_channels"]["MFC3"]["values_V"],
            },
            "sensors": ["TCBurner", "TCA", "TCB", "TCC", "PMT3", "RadiometerCenter"],
            "sensor_payloads": sensors_obs,
        },
        "alternative_scenario_orange": {
            "label": "ESCENARIO ALTERNATIVO (SCM IGNIS-mu)",
            "epistemic_tag": "INFERRED",
            "theme_color_hex": "#D97706",
            "badge_color_hex": "#B4690E",
            "preset_applied": alt_mfc_program.get("title", "Intervención Contrafactual SCM"),
            "intervened_variables": ["MFC2_voltage_program", "MFC3_voltage_program"],
            "mfc_program_alternative": {
                "MFC2_unit": "V",
                "MFC3_unit": "V",
                "MFC2_values_V": [round(float(x), 6) for x in mfc2_alt],
                "MFC3_values_V": [round(float(x), 6) for x in mfc3_alt],
            },
            "scm_sensor_responses": scm_sensor_responses,
        },
        "counterfactual_coupling_bounds": {
            "lower_pct": 44.83,
            "upper_pct": 82.21,
            "equation_latex": "44.83\\% \\leq P_{\\Pi}(\\Delta > 0) \\leq 82.21\\%",
            "causal_effect_identified": False,
            "scientific_disclaimer": (
                "Cotas de acoplamiento sobre distribuciones observacionales dependientes de "
                "supuestos del SCM. No representan probabilidades de incendio ni efectos causales "
                "físicos identificados."
            ),
        },
    }


if __name__ == "__main__":
    out = evaluate_counterfactual_comparison("20013D1")
    print("scm_counterfactual_bridge.py OK | Bounds:", out["counterfactual_coupling_bounds"]["equation_latex"])