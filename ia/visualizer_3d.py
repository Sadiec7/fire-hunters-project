# -*- coding: utf-8 -*-
"""
ARCHIVO: ia/visualizer_3d.py
RESPONSABLES: Ángel ("Lito" / "Perrita") & Rodolfo ("Tornolfo")
DESCRIPCIÓN: Extracción de perfiles radiales promediados en 30 cascarones esféricos
             incluyendo q_chem(r) [W/m^3] y Y_P(r) [-] (Entregable 3 de IGNIS-mu),
             métricas globales de llama 3D y visualización 2D/3D.
"""

import os
import sys
from typing import Dict, Any, Optional
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def extract_spherical_shell_profiles(
    R_3d: np.ndarray,
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    q_chem_3d: Optional[np.ndarray] = None,
    Y_I_3d: Optional[np.ndarray] = None,
    r_burner_m: float = 0.00318,
    r_max_m: float = 0.035,
    n_shells: int = 30,
    Y_O_ambient: float = 0.233,
) -> Dict[str, Any]:
    """
    ENTREGABLE 3 (Trabajo de Ángel):
    Promedia los campos 3D sobre `n_shells` (30) cascarones esféricos concéntricos
    y exporta:
      - r_shells_m [m]
      - T_mean_K [K] y T_std_K [K]
      - Y_F_mean [-] y Y_O_mean [-]
      - Y_N2_mean [-] (o diluyente inerte)
      - Y_P_mean [-] = 1.0 - Y_F(r) - Y_O(r) - Y_N2(r)
      - q_chem_mean_W_m3 [W/m^3]
    """
    if q_chem_3d is None:
        q_chem_3d = np.zeros_like(T_3d, dtype=np.float64)

    # Estimar fracción másica local de inerte N2/He si no se pasa explícitamente
    Y_F_clip = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_clip = np.clip(Y_O_3d, 0.0, 1.0)
    if Y_I_3d is None:
        Y_I_amb = max(0.0, 1.0 - float(Y_O_ambient))
        Y_I_3d = np.clip(
            Y_I_amb * (1.0 - Y_F_clip),
            0.0,
            np.maximum(0.0, 1.0 - Y_F_clip - Y_O_clip),
        )

    # Fracción másica local de productos Y_P = 1 - Y_F - Y_O - Y_N2
    Y_P_3d = np.maximum(0.0, 1.0 - Y_F_clip - Y_O_clip - Y_I_3d)

    edges = np.linspace(float(r_burner_m), float(r_max_m), int(n_shells) + 1)
    r_centers = 0.5 * (edges[:-1] + edges[1:])

    T_mean = np.zeros(n_shells, dtype=np.float64)
    T_std = np.zeros(n_shells, dtype=np.float64)
    YF_mean = np.zeros(n_shells, dtype=np.float64)
    YO_mean = np.zeros(n_shells, dtype=np.float64)
    YN2_mean = np.zeros(n_shells, dtype=np.float64)
    YP_mean = np.zeros(n_shells, dtype=np.float64)
    q_mean = np.zeros(n_shells, dtype=np.float64)

    for idx in range(n_shells):
        mask = (R_3d >= edges[idx]) & (R_3d < edges[idx + 1])
        if np.any(mask):
            T_mean[idx] = float(np.mean(T_3d[mask]))
            T_std[idx] = float(np.std(T_3d[mask]))
            YF_mean[idx] = float(np.mean(Y_F_clip[mask]))
            YO_mean[idx] = float(np.mean(Y_O_clip[mask]))
            YN2_mean[idx] = float(np.mean(Y_I_3d[mask]))
            # Garantizar relación exacta pedida en Entregable 3:
            # Y_P(r) = 1 - Y_F(r) - Y_O(r) - Y_N2(r)
            YP_val = 1.0 - YF_mean[idx] - YO_mean[idx] - YN2_mean[idx]
            YP_mean[idx] = max(0.0, float(YP_val))
            q_mean[idx] = float(np.mean(q_chem_3d[mask]))
        elif idx > 0:
            T_mean[idx] = T_mean[idx - 1]
            T_std[idx] = T_std[idx - 1]
            YF_mean[idx] = YF_mean[idx - 1]
            YO_mean[idx] = YO_mean[idx - 1]
            YN2_mean[idx] = YN2_mean[idx - 1]
            YP_mean[idx] = YP_mean[idx - 1]
            q_mean[idx] = q_mean[idx - 1]

    return {
        "r_shells_m": [round(float(x), 6) for x in r_centers],
        "T_mean_K": [round(float(x), 3) for x in T_mean],
        "T_std_K": [round(float(x), 4) for x in T_std],
        "Y_F_mean": [round(float(x), 6) for x in YF_mean],
        "Y_O_mean": [round(float(x), 6) for x in YO_mean],
        "Y_N2_mean": [round(float(x), 6) for x in YN2_mean],
        "Y_P_mean": [round(float(x), 6) for x in YP_mean],
        "q_chem_mean_W_m3": [round(float(x), 3) for x in q_mean],
        "units": {
            "r_shells_m": "m",
            "T_mean_K": "K",
            "T_std_K": "K",
            "Y_F_mean": "-",
            "Y_O_mean": "-",
            "Y_N2_mean": "-",
            "Y_P_mean": "-",
            "q_chem_mean_W_m3": "W/m^3",
        },
    }


def compute_flame_metrics_3d(
    R_3d: np.ndarray,
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    q_chem_3d: np.ndarray,
    dx_m: float,
    r_burner_m: float = 0.00318,
    r_max_m: float = 0.035,
) -> Dict[str, Any]:
    """
    Calcula las métricas escalares globales de la llama esférica 3D:
      - Radio de llama r_f [m]
      - Temperatura pico T_max [K]
      - Potencia química integrada Q_chem [W]
      - Índice de esfericidad 3D [-]
    """
    profiles = extract_spherical_shell_profiles(
        R_3d=R_3d,
        T_3d=T_3d,
        Y_F_3d=Y_F_3d,
        Y_O_3d=Y_O_3d,
        q_chem_3d=q_chem_3d,
        r_burner_m=r_burner_m,
        r_max_m=r_max_m,
        n_shells=30,
    )
    r_arr = np.array(profiles["r_shells_m"], dtype=np.float64)
    T_arr = np.array(profiles["T_mean_K"], dtype=np.float64)
    T_std_arr = np.array(profiles["T_std_K"], dtype=np.float64)

    idx_peak = int(np.argmax(T_arr))
    r_flame_m = float(r_arr[idx_peak])
    T_max_K = float(np.max(T_3d))
    dV_m3 = float(dx_m) ** 3
    Q_chem_W = float(np.sum(q_chem_3d) * dV_m3)

    # Índice de esfericidad en el cascarón de la frente de llama (1.0 = esfera perfecta)
    rel_dispersion = float(T_std_arr[idx_peak]) / max(float(T_arr[idx_peak]), 300.0)
    sphericity_index = float(np.clip(1.0 - rel_dispersion, 0.0, 1.0))

    return {
        "flame_radius_m": round(r_flame_m, 6),
        "max_temperature_K": round(T_max_K, 2),
        "integrated_heat_release_W": round(Q_chem_W, 4),
        "sphericity_index_3d": round(sphericity_index, 5),
        "radial_profiles": profiles,
    }


if __name__ == "__main__":
    print("=== PRUEBA ENTREGABLE 3 (ia/visualizer_3d.py) ===")
    lin = np.linspace(-0.035, 0.035, 21)
    X, Y, Z = np.meshgrid(lin, lin, lin, indexing="ij")
    R = np.sqrt(X**2 + Y**2 + Z**2)
    T_mock = 300.0 + 1380.0 * np.exp(-((R - 0.022) / 0.006) ** 2)
    YF_mock = np.clip(0.00318 / np.maximum(R, 0.00318), 0.0, 1.0) * np.exp(-R / 0.015)
    YO_mock = 0.233 * (1.0 - np.exp(-R / 0.018))
    q_mock = 1.5e6 * np.exp(-((R - 0.022) / 0.004) ** 2)

    prof = extract_spherical_shell_profiles(R, T_mock, YF_mock, YO_mock, q_mock)
    print(f"[OK] Cascarones extraídos: {len(prof['r_shells_m'])}")
    print(f"[OK] Max q_chem(r): {max(prof['q_chem_mean_W_m3']):.2e} W/m^3 | Max Y_P(r): {max(prof['Y_P_mean']):.4f}")