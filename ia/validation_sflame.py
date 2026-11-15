# -*- coding: utf-8 -*-
"""
ia/validation_sflame.py
Validación Experimental Cuantitativa (MAE y RMSE) frente a Mediciones de NASA s-Flame.
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame).
Autor: Ángel ("Lito" / "Perrita")
"""

import os
import sys
import json
from typing import Dict, Any, Tuple, Optional
import numpy as np

# Permitir ejecución directa desde la terminal "python ia/validation_sflame.py"
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from ia.visualizer_3d import extract_spherical_shell_profiles
except ImportError:
    from visualizer_3d import extract_spherical_shell_profiles


# Nota metodológica obligatoria exigida en la Sección 7.2 del documento técnico
SPATIAL_AVERAGING_NOTE_ES: str = (
    "NOTA METODOLÓGICA DE RESOLUCIÓN ESPACIAL (Sección 7.2): El campo tridimensional "
    "cartesiano (x, y, z) resuelto por el modelo 3D fue promediado azimutalmente en "
    "cascarones esféricos concéntricos de espesor Delta_r para proyectarlo a una "
    "coordenada radial 1D equivalente r. Esto empareja rigurosamente la resolución "
    "espacial del solver 3D con los diagnósticos experimentales radiales (termopares "
    "y radio óptico de quimioluminiscencia) del experimento NASA ACME s-Flame."
)


# =============================================================================
# 1. CÁLCULO CUANTITATIVO DE MAE Y RMSE (Tarea A8.1 - Función 1 / Ecuación 18)
# =============================================================================
def compute_mae_and_rmse(y_exp: Any, y_sim: Any) -> Tuple[float, float]:
    """
    Recibe dos arreglos de igual longitud:
      - y_exp (y_i): Mediciones experimentales reales de NASA s-Flame.
      - y_sim (y_hat_i): Predicciones del modelo 3D interpoladas en las mismas posiciones.
    Calcula las dos ecuaciones oficiales de la Sección 7.2:
      MAE  = (1 / N) * sum(|y_i - y_hat_i|)
      RMSE = sqrt((1 / N) * sum((y_i - y_hat_i)^2))
    Devuelve la tupla (MAE, RMSE) en unidades SI.
    """
    arr_exp = np.asarray(y_exp, dtype=np.float64).flatten()
    arr_sim = np.asarray(y_sim, dtype=np.float64).flatten()

    if arr_exp.size == 0 or arr_sim.size == 0:
        raise ValueError("Los arreglos y_exp y y_sim no pueden estar vacíos.")
    if arr_exp.size != arr_sim.size:
        raise ValueError(
            f"Dimensiones incompatibles en validación: len(y_exp)={arr_exp.size} vs len(y_sim)={arr_sim.size}."
        )

    abs_diff = np.abs(arr_exp - arr_sim)
    mae = float(np.mean(abs_diff))
    rmse = float(np.sqrt(np.mean(abs_diff**2)))
    return mae, rmse


def compute_mae_rmse(y_exp: Any, y_pred: Any) -> Tuple[float, float]:
    """Alias de compatibilidad directa con proyecto_acme (1).pdf (Tarea 8.2 - Función 1)."""
    return compute_mae_and_rmse(y_exp, y_pred)


# =============================================================================
# 2. CARGA DEL CASO DE REFERENCIA MAESTRO DESDE JSON
# =============================================================================
def load_reference_case_json(json_path: Optional[str] = None) -> Dict[str, Any]:
    """Carga la ficha ia/sflame_reference_case.json creada por Ángel en el Bloque 1."""
    if json_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "sflame_reference_case.json")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Respaldo en memoria idéntico a sflame_reference_case.json del Bloque 1
    return {
        "metadata": {"reference_case_id": "SFLAME_REF_C2H4"},
        "experimental_targets": {
            "measured_flame_radius_m": {"value": 0.0224, "unit": "m", "uncertainty": 0.0005},
            "measured_max_temp_K": {"value": 1677.0, "unit": "K", "uncertainty": 50.0},
            "radial_profile_r_m": [0.00318, 0.006, 0.010, 0.015, 0.019, 0.0224, 0.026, 0.030, 0.035],
            "radial_profile_T_exp_K": [300.0, 620.0, 1040.0, 1390.0, 1585.0, 1677.0, 1410.0, 980.0, 480.0],
        },
    }


# =============================================================================
# 3. VALIDACIÓN CONTRA REFERENCIA NASA s-Flame (Tarea A8.1 - Función 2)
# =============================================================================
def validate_against_sflame_reference(
    sim_results_dict: Dict[str, Any],
    ref_case_dict: Optional[Dict[str, Any]] = None,
    matched_experiment_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compara cuantitativamente las predicciones del modelo 3D contra las mediciones
    reales de NASA s-Flame:
      1) Extrae (o recupera) el perfil radial en cascarones esféricos T_mean(r).
      2) Calcula el error absoluto y relativo en el radio de la llama |r_f,exp - r_f,sim| [m].
      3) Calcula el error absoluto y relativo en la temperatura máxima |T_max,exp - T_max,sim| [K].
      4) Interpola el perfil radial simulado T_mean(r) en los radios medidos por la NASA
         y calcula el MAE y RMSE del perfil radial de temperatura [K].
      5) Incluye la nota metodológica obligatoria de promediado en cascarones esféricos.
    """
    if ref_case_dict is None:
        ref_case_dict = load_reference_case_json()

    targets = ref_case_dict.get("experimental_targets", {})

    # Si domain_query encontró un experimento específico distinto al caso maestro, usar su r_f y T_max
    if matched_experiment_data is not None:
        exp_id = str(matched_experiment_data.get("experiment_id", "SFLAME_REF_C2H4"))
        r_f_exp_m = float(matched_experiment_data["measured_flame_radius_m"])
        T_max_exp_K = float(matched_experiment_data["measured_max_temp_K"])
        u_rf_m = float(matched_experiment_data.get("uncertainty_radius_m", 0.0005))
        u_T_K = float(matched_experiment_data.get("uncertainty_temp_K", 50.0))
    else:
        exp_id = str(ref_case_dict.get("metadata", {}).get("reference_case_id", "SFLAME_REF_C2H4"))
        r_f_exp_m = float(targets["measured_flame_radius_m"]["value"])
        T_max_exp_K = float(targets["measured_max_temp_K"]["value"])
        u_rf_m = float(targets["measured_flame_radius_m"].get("uncertainty", 0.0005))
        u_T_K = float(targets["measured_max_temp_K"].get("uncertainty", 50.0))

    # Extraer perfil radial promediado en cascarones esféricos si aún no viene en sim_results_dict
    if "radial_shell_profiles" in sim_results_dict:
        shell_prof = sim_results_dict["radial_shell_profiles"]
    elif "T_3d" in sim_results_dict and "grid_dict" in sim_results_dict:
        shell_prof = extract_spherical_shell_profiles(
            sim_results_dict["grid_dict"],
            sim_results_dict["T_3d"],
            sim_results_dict.get("Y_F_3d", np.zeros_like(sim_results_dict["T_3d"])),
            sim_results_dict.get("Y_O_3d", np.zeros_like(sim_results_dict["T_3d"])),
        )
    else:
        raise ValueError(
            "sim_results_dict debe contener 'radial_shell_profiles' o ('T_3d' y 'grid_dict')."
        )

    r_sim_shells = np.asarray(shell_prof.get("r_shells_m", shell_prof.get("r_m")), dtype=np.float64)
    T_sim_shells = np.asarray(shell_prof["T_mean_K"], dtype=np.float64)

    # Radio de llama simulado y temperatura máxima simulada
    idx_peak = int(np.argmax(T_sim_shells))
    r_f_sim_m = float(sim_results_dict.get("predicted_flame_radius_m", r_sim_shells[idx_peak]))
    T_max_sim_K = float(sim_results_dict.get("max_temperature_K", np.max(T_sim_shells)))

    # Errores puntuales en radio de llama y temperatura máxima
    abs_error_radius_m = abs(r_f_exp_m - r_f_sim_m)
    rel_error_radius_pct = 100.0 * abs_error_radius_m / max(r_f_exp_m, 1.0e-12)

    abs_error_T_max_K = abs(T_max_exp_K - T_max_sim_K)
    rel_error_T_max_pct = 100.0 * abs_error_T_max_K / max(T_max_exp_K, 1.0e-12)

    # Interpolación del perfil radial simulado en los puntos radiales medidos por NASA
    r_exp_profile = np.asarray(
        targets.get("radial_profile_r_m", [0.00318, 0.010, 0.015, 0.0224, 0.030, 0.035]),
        dtype=np.float64,
    )
    T_exp_profile = np.asarray(
        targets.get("radial_profile_T_exp_K", [300.0, 1040.0, 1390.0, 1677.0, 980.0, 480.0]),
        dtype=np.float64,
    )

    # Si se valida otro experimento sin curva radial completa, escalar el perfil de referencia a su T_max y r_f
    if exp_id != "SFLAME_REF_C2H4":
        T_exp_profile = 298.15 + (T_exp_profile - 298.15) * (
            (T_max_exp_K - 298.15) / (1677.0 - 298.15)
        )

    T_sim_interp_K = np.interp(r_exp_profile, r_sim_shells, T_sim_shells)

    # Cálculo oficial de MAE y RMSE sobre el perfil radial de temperatura T(r)
    mae_temp_K, rmse_temp_K = compute_mae_and_rmse(T_exp_profile, T_sim_interp_K)

    # MAE y RMSE del radio de llama (puntual o serie)
    mae_radius_m, rmse_radius_m = compute_mae_and_rmse([r_f_exp_m], [r_f_sim_m])

    return {
        "reference_experiment_id": exp_id,
        "measured_flame_radius_m": r_f_exp_m,
        "predicted_flame_radius_m": r_f_sim_m,
        "abs_error_radius_m": abs_error_radius_m,
        "rel_error_radius_pct": rel_error_radius_pct,
        "MAE_radius_m": mae_radius_m,
        "RMSE_radius_m": rmse_radius_m,
        "experimental_radius_uncertainty_m": u_rf_m,
        "measured_max_temp_K": T_max_exp_K,
        "predicted_max_temp_K": T_max_sim_K,
        "abs_error_max_temp_K": abs_error_T_max_K,
        "rel_error_max_temp_pct": rel_error_T_max_pct,
        "experimental_temp_uncertainty_K": u_T_K,
        "MAE_temp_K": mae_temp_K,
        "RMSE_temp_K": rmse_temp_K,
        "radial_validation_points": {
            "r_exp_m": r_exp_profile.tolist(),
            "T_exp_K": T_exp_profile.tolist(),
            "T_sim_interp_K": [float(v) for v in T_sim_interp_K],
        },
        "spatial_resolution_methodology_note": SPATIAL_AVERAGING_NOTE_ES,
    }


# =============================================================================
# 4. BLOQUE DE PRUEBA DIRECTA EN TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=== PRUEBA DE VALIDACIÓN EXPERIMENTAL NASA s-Flame (ia/validation_sflame.py) ===")

    ref_case = load_reference_case_json()
    r_exp = np.array(ref_case["experimental_targets"]["radial_profile_r_m"])
    T_exp = np.array(ref_case["experimental_targets"]["radial_profile_T_exp_K"])

    # Crear perfil simulado de prueba en 30 cascarones esféricos cercano al caso maestro
    r_shells = np.linspace(0.00318, 0.035, 30)
    T_shells = np.interp(r_shells, r_exp, T_exp) + np.sin(np.linspace(0, 3.14, 30)) * 18.0

    mock_sim_results = {
        "max_temperature_K": float(np.max(T_shells)),
        "predicted_flame_radius_m": 0.0221,
        "radial_shell_profiles": {
            "r_shells_m": r_shells.tolist(),
            "T_mean_K": T_shells.tolist(),
        },
    }

    val_report = validate_against_sflame_reference(mock_sim_results, ref_case)
    print(f"[OK] Experimento de referencia: {val_report['reference_experiment_id']}")
    print(f"     Radio de llama: Exp = {val_report['measured_flame_radius_m']:.4f} m | Sim = {val_report['predicted_flame_radius_m']:.4f} m | Error Abs = {val_report['abs_error_radius_m']:.5f} m ({val_report['rel_error_radius_pct']:.2f}%)")
    print(f"     Temp. máxima : Exp = {val_report['measured_max_temp_K']:.1f} K | Sim = {val_report['predicted_max_temp_K']:.1f} K | Error Abs = {val_report['abs_error_max_temp_K']:.2f} K")
    print(f"     Perfil radial T(r): MAE = {val_report['MAE_temp_K']:.2f} K | RMSE = {val_report['RMSE_temp_K']:.2f} K")
    print(f"     Nota metodológica incluida: {len(val_report['spatial_resolution_methodology_note'])} caracteres.")