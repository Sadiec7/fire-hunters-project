"""
ia/validation_sflame.py
Validación contra perfiles de referencia s-Flame sin valores predefinidos (Corrige Hallazgo Alto 4).
"""

import os
import sys
from typing import Dict, Any
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from radial_verification import burke_schumann_spherical_reference  # type: ignore
except ImportError:
    from ia.radial_verification import burke_schumann_spherical_reference


def validate_against_sflame_reference(
    shells_dict: Dict[str, np.ndarray],
    r_f_sim: float,
    T_max_sim: float,
    mdot_kg_s: float = 2.5e-6
) -> Dict[str, Any]:
    """
    CORRECCIÓN HALLAZGO ALTO 4:
    Exige los arreglos reales r_shells_m y T_mean_K provenientes del solver 3D.
    Eliminados por completo los valores hardcodeados (mae_K = 6.82, rmse_K = 8.33).
    """
    if not isinstance(shells_dict, dict) or "r_shells_m" not in shells_dict or "T_mean_K" not in shells_dict:
        raise ValueError(
            "Error en validate_against_sflame_reference: Se requieren los perfiles radiales reales "
            "'r_shells_m' y 'T_mean_K' extraídos de la simulación 3D."
        )

    r_shells = np.asarray(shells_dict["r_shells_m"], dtype=np.float64)
    T_sim = np.asarray(shells_dict["T_mean_K"], dtype=np.float64)
    if r_shells.size == 0 or T_sim.size != r_shells.size:
        raise ValueError("Error en validate_against_sflame_reference: Perfiles radiales vacíos o de distinto tamaño.")

    bs_ref = burke_schumann_spherical_reference(r_m=r_shells, mdot_kg_s=mdot_kg_s)
    T_ref = np.asarray(bs_ref["T_r_K"], dtype=np.float64)

    mae_T = float(np.mean(np.abs(T_ref - T_sim)))
    rmse_T = float(np.sqrt(np.mean((T_ref - T_sim) ** 2)))
    r_f_ref = float(bs_ref.get("flame_radius_m", bs_ref.get("r_f_m", 0.0224)))
    T_max_ref = float(np.max(T_ref))

    return {
        "reference_type": "BURKE_SCHUMANN_1D_ANALYTICAL_BENCHMARK",
        "is_nasa_experimental_validation": False,
        "MAE_temp_K": round(mae_T, 3),
        "RMSE_temp_K": round(rmse_T, 3),
        "abs_error_radius_m": round(abs(r_f_ref - float(r_f_sim)), 5),
        "abs_error_T_max_K": round(abs(T_max_ref - float(T_max_sim)), 2),
        "spatial_comparison_note": (
            "Comparación calculada dinámicamente entre el promedio azimutal 3D en cascarones "
            "esféricos y la solución analítica radial 1D para el flujo másico evaluado."
        ),
    }