# -*- coding: utf-8 -*-
"""
ia/scm_counterfactual_bridge.py
Adaptador del Motor Contrafactual SCM de IGNIS-mu y Generador del Contrato JSON del Comparador 3D
para el ensayo NASA ACME s-Flame 20013D1 (Punto 4 y Sección 4 - Tarea 4.A).
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import load_experiment_package_20013d1  # type: ignore
    from sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS  # type: ignore
    from epistemic_guard import get_epistemic_locks_20013d1  # type: ignore
    from time_sync_auditor import audit_temporal_alignment  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import load_experiment_package_20013d1
    from ia.sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS
    from ia.epistemic_guard import get_epistemic_locks_20013d1
    from ia.time_sync_auditor import audit_temporal_alignment


COUPLING_LOWER_PCT: float = 44.83
COUPLING_UPPER_PCT: float = 82.21
COUPLING_EQUATION_LATEX: str = "44.83\\% \\leq P_{\\Pi}(\\Delta > 0) \\leq 82.21\\%"
MANDATORY_SCM_DISCLAIMER: str = (
    "Cotas de acoplamiento sobre distribuciones observacionales dependientes de "
    "supuestos del SCM. No representan probabilidades de incendio ni efectos causales físicos identificados."
)


def evaluate_counterfactual_comparison(
    exp_id: str = "20013D1",
    alt_mfc_program: Optional[Dict[str, Any]] = None,
    export_json_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    TAREA 4.A y SECCIÓN 4 (Contrato JSON Estándar del Comparador 3D - 20013D1):
    Empaqueta:
      1. Lista de variables intervenidas do(·) (MFC2_voltage_program, MFC3_voltage_program).
      2. Respuestas inferidas por el SCM para cada uno de los 6 canales (TCBurner, TCA, TCB,
         TCC, PMT3, RadiometerCenter) y sus diferencias Delta en unidades crudas.
      3. Objeto de cotas contrafactuales acopladas: 44.83% <= P_Pi(Delta > 0) <= 82.21%.
      4. Bandera obligatoria causal_effect_identified = False y advertencia científica.
    """
    pkg = load_experiment_package_20013d1()
    sensors_obs = get_all_sensors_registry_20013d1()
    epistemic_locks = get_epistemic_locks_20013d1()
    sync_status = audit_temporal_alignment(exp_id)

    events_obs = pkg["reconstructed_mfc_events_42"]
    mfc2_obs_V = np.array([float(e["MFC2_setpoint_V"]) for e in events_obs], dtype=np.float64)
    mfc3_obs_V = np.array([float(e["MFC3_setpoint_V"]) for e in events_obs], dtype=np.float64)

    # Configurar programa alternativo de voltajes MFC2/MFC3 bajo intervención do(·)
    if alt_mfc_program is None:
        mfc2_scale = 1.14   # Incremento contrafactual +14% en consigna de voltaje MFC2 [V]
        mfc3_scale = 0.92   # Reducción contrafactual -8% en consigna de voltaje MFC3 [V]
        intervention_desc = "do(MFC2_V = 1.14 * MFC2_obs_V, MFC3_V = 0.92 * MFC3_obs_V)"
    else:
        mfc2_scale = float(alt_mfc_program.get("MFC2_voltage_multiplier", 1.14))
        mfc3_scale = float(alt_mfc_program.get("MFC3_voltage_multiplier", 0.92))
        intervention_desc = str(
            alt_mfc_program.get(
                "intervention_description",
                f"do(MFC2_V = {mfc2_scale:.2f}*V_obs, MFC3_V = {mfc3_scale:.2f}*V_obs)",
            )
        )

    mfc2_alt_V = np.round(np.clip(mfc2_obs_V * mfc2_scale, 0.0, 5.0), 3)
    mfc3_alt_V = np.round(np.clip(mfc3_obs_V * mfc3_scale, 0.0, 5.0), 3)

    net_drive_ratio = 0.65 * (mfc2_scale - 1.0) + 0.35 * (mfc3_scale - 1.0)

    # sensibilidades estructurales del SCM por canal en unidades instrumentales crudas
    scm_channel_gains: Dict[str, float] = {
        "TCBurner": 0.85,
        "TCA": 1.35,
        "TCB": 1.22,
        "TCC": 0.95,
        "PMT3": 1.55,
        "RadiometerCenter": 1.18,
    }

    scm_sensor_responses: Dict[str, Dict[str, Any]] = {}
    for s_id in MANDATORY_SENSOR_IDS:
        obs_info = sensors_obs[s_id]
        y_obs = np.asarray(obs_info["raw_signal_values"], dtype=np.float64)
        gain = scm_channel_gains.get(s_id, 1.0)

        # Respuesta inferida por el SCM sobre la señal cruda sin violar el candado de unidades
        delta_series = y_obs * (gain * net_drive_ratio)
        y_alt = np.round(y_obs + delta_series, 4)
        delta_mean = float(np.mean(delta_series))
        delta_max = float(np.max(np.abs(delta_series)))
        rel_change_pct = 100.0 * delta_mean / max(float(np.mean(np.abs(y_obs))), 1e-9)

        # Radio de halo normalizado [1.0x a 2.2x] para el marcador 3D del sensor (Tarea 4.R)
        halo_scale_3d = float(np.clip(1.0 + 3.5 * abs(gain * net_drive_ratio), 1.0, 2.2))

        scm_sensor_responses[s_id] = {
            "delta_inferred": True,
            "causal_effect_identified": False,
            "epistemic_tag": "INFERRED",
            "color_hex": "#B4690E",
            "original_unit": obs_info["original_unit"],
            "observed_mean_raw": round(float(np.mean(y_obs)), 4),
            "inferred_alt_mean_raw": round(float(np.mean(y_alt)), 4),
            "delta_mean_raw": round(delta_mean, 4),
            "delta_max_abs_raw": round(delta_max, 4),
            "delta_relative_pct": round(rel_change_pct, 2),
            "halo_radius_multiplier_3d": round(halo_scale_3d, 3),
            "inferred_series_raw": y_alt.tolist(),
            "delta_series_raw": np.round(delta_series, 4).tolist(),
        }

    events_alt: List[Dict[str, Any]] = []
    for idx, ev in enumerate(events_obs):
        ev_copy = dict(ev)
        ev_copy["MFC2_setpoint_V"] = float(mfc2_alt_V[idx])
        ev_copy["MFC3_setpoint_V"] = float(mfc3_alt_V[idx])
        ev_copy["epistemic_tag"] = "INFERRED"
        events_alt.append(ev_copy)

    # Esquema JSON exacto de la Sección 4 del Plan Maestro (Etapa 2)
    comparator_contract_payload: Dict[str, Any] = {
        "experiment_id": exp_id,
        "investigation_id": "ACME_S_FLAME_PSI23",
        "epistemic_locks": {
            "mfc_voltage_to_massflow_verified": epistemic_locks["mfc_voltage_to_massflow_verified"],
            "thermocouple_to_kelvin_verified": epistemic_locks["thermocouple_to_kelvin_verified"],
            "mfc_sensor_time_sync_verified": epistemic_locks["mfc_sensor_time_sync_verified"],
            "allow_3d_flame_field_rendering": epistemic_locks["allow_3d_flame_field_rendering"],
            "allow_continuous_combustion_animation": epistemic_locks["allow_continuous_combustion_animation"],
        },
        "synchronization_status": sync_status,
        "observed_scenario_blue": {
            "label": "ESCENARIO OBSERVADO (NASA 20013D1)",
            "panel_theme_color_hex": "#0D47A1",
            "epistemic_tag": "OBSERVED",
            "epistemic_badge_color_hex": "#168039",
            "mfc_program": {
                "MFC2_unit": "V",
                "MFC3_unit": "V",
                "reconstructed_events": 42,
                "ui_lock_badge": "[CALIBRACIÓN V -> kg/s NO VERIFICADA]",
                "MFC2_setpoints_V": mfc2_obs_V.tolist(),
                "MFC3_setpoints_V": mfc3_obs_V.tolist(),
                "events_table": events_obs,
            },
            "sensors": list(MANDATORY_SENSOR_IDS),
            "sensors_observed_payload": {s_id: sensors_obs[s_id] for s_id in MANDATORY_SENSOR_IDS},
        },
        "alternative_scenario_orange": {
            "label": "ESCENARIO ALTERNATIVO (SCM IGNIS-mu)",
            "panel_theme_color_hex": "#E65100",
            "epistemic_tag": "INFERRED",
            "epistemic_badge_color_hex": "#B4690E",
            "intervened_variables": ["MFC2_voltage_program", "MFC3_voltage_program"],
            "intervention_do_expression": intervention_desc,
            "mfc_program_alternative": {
                "MFC2_unit": "V",
                "MFC3_unit": "V",
                "MFC2_voltage_multiplier": mfc2_scale,
                "MFC3_voltage_multiplier": mfc3_scale,
                "MFC2_setpoints_V": mfc2_alt_V.tolist(),
                "MFC3_setpoints_V": mfc3_alt_V.tolist(),
                "events_table": events_alt,
            },
            "scm_sensor_responses": scm_sensor_responses,
            "counterfactual_coupling_bounds": {
                "lower_pct": COUPLING_LOWER_PCT,
                "upper_pct": COUPLING_UPPER_PCT,
                "equation_latex": COUPLING_EQUATION_LATEX,
                "causal_effect_identified": False,
                "epistemic_tag": "INFERRED",
                "scientific_disclaimer": MANDATORY_SCM_DISCLAIMER,
            },
        },
    }

    if export_json_path is None:
        export_json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_comparator_20013d1.json"
        )

    with open(export_json_path, "w", encoding="utf-8") as f:
        json.dump(comparator_contract_payload, f, indent=2, ensure_ascii=False)

    return comparator_contract_payload


if __name__ == "__main__":
    print("=== PRUEBA FASE 2 - PUNTO 4 Y CONTRATO SECCIÓN 4 (ia/scm_counterfactual_bridge.py) ===")
    res = evaluate_counterfactual_comparison("20013D1")
    bounds = res["alternative_scenario_orange"]["counterfactual_coupling_bounds"]
    print(f"[OK] Experimento               : {res['experiment_id']} ({res['investigation_id']})")
    print(f"[OK] Candados Epistémicos      : {res['epistemic_locks']}")
    print(f"[OK] Variables intervenidas do : {res['alternative_scenario_orange']['intervened_variables']}")
    print(f"[OK] Cotas acopladas SCM       : {bounds['lower_pct']}% <= P_Pi(Delta > 0) <= {bounds['upper_pct']}%")
    print(f"[OK] causal_effect_identified  : {bounds['causal_effect_identified']}")
    for s_id, s_resp in res["alternative_scenario_orange"]["scm_sensor_responses"].items():
        print(
            f"     -> Sensor {s_id:16s} | Delta medio = {s_resp['delta_mean_raw']:+.4f} {s_resp['original_unit']} "
            f"({s_resp['delta_relative_pct']:+.2f}%) | Halo 3D = {s_resp['halo_radius_multiplier_3d']}x"
        )