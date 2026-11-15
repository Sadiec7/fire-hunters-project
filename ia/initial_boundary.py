# -*- coding: utf-8 -*-
"""
ia/initial_boundary.py
Condiciones Iniciales 3D, Chispa Térmica de Ignición y Máscaras de Frontera.
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame).
Autor: Ángel ("Lito" / "Perrita")
"""

import os
import sys
from typing import Dict, Any, Tuple
import numpy as np

# Permitir importación tanto al correr "python ia/initial_boundary.py" como desde la raíz
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from ia.contract_si import SimulationInputSI, assert_valid_3d_fields
except ImportError:
    from contract_si import SimulationInputSI, assert_valid_3d_fields


# =============================================================================
# 1. EXTRACCIÓN SEGURA DE PARÁMETROS DESDE OBJETO SI O DICCIONARIO
# =============================================================================
def _extract_bc_params(sim_input: Any) -> Dict[str, float]:
    """
    Extrae de forma uniforme los parámetros de frontera e inicialización,
    ya sea que sim_input venga como instancia de SimulationInputSI o como dict.
    """
    if isinstance(sim_input, dict):
        return {
            "Y_F_burner": float(sim_input.get("Y_F_burner", sim_input.get("Y_F_inlet", 1.0))),
            "Y_O_ambient": float(sim_input.get("Y_O_ambient", 0.233)),
            "T_initial_K": float(sim_input.get("T_initial_K", sim_input.get("T_0_K", 298.15))),
            "T_burner_K": float(sim_input.get("T_burner_K", 300.0)),
            "burner_radius_m": float(sim_input.get("burner_radius_m", sim_input.get("r_b_m", 0.00318))),
        }
    return {
        "Y_F_burner": float(sim_input.Y_F_burner),
        "Y_O_ambient": float(sim_input.Y_O_ambient),
        "T_initial_K": float(sim_input.T_initial_K),
        "T_burner_K": float(sim_input.T_burner_K),
        "burner_radius_m": float(sim_input.burner_radius_m),
    }


# =============================================================================
# 2. INICIALIZACIÓN DE CAMPOS 3D Y CHISPA DE IGNICIÓN (Tarea A4.1 - Función 1)
# =============================================================================
def initialize_fields_3d(
    grid_dict: Dict[str, Any],
    sim_input: Any,
    warm_start: bool = True,
    T_spark_peak_K: float = 1380.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Construye los tres cubos tridimensionales iniciales (Y_F_3d, Y_O_3d, T_3d)
    de tamaño (Nx, Ny, Nz) sobre la malla 3D de Rodolfo:
      a) En el ambiente exterior al quemador (~mask_burner):
         Y_O_3d = Y_O_ambient, Y_F_3d = 0.0, T_3d = T_initial_K.
      b) Dentro de la esfera porosa del quemador (mask_burner, R <= r_b):
         Y_F_3d = Y_F_burner, Y_O_3d = 0.0, T_3d = T_burner_K.
      c) Chispa inicial de ignición (si warm_start=True):
         Añade una cáscara esférica suave de precalentamiento entre r_b < R < 2.2 * r_b
         (centrada alrededor de 1.5 * r_b a ~1380 K) junto con una capa difusiva inicial
         de mezcla para encender suavemente la cinética de Arrhenius en t = 0 s.
    Devuelve la tupla (Y_F_3d, Y_O_3d, T_3d).
    """
    params = _extract_bc_params(sim_input)
    Y_F_in = params["Y_F_burner"]
    Y_O_inf = params["Y_O_ambient"]
    T_0 = params["T_initial_K"]
    T_b = params["T_burner_K"]
    r_b = params["burner_radius_m"]

    R = grid_dict["R"]
    mask_burner = grid_dict["mask_burner"]
    mask_outer = grid_dict["mask_outer"]
    shape_3d = R.shape

    # a) Inicialización base en todo el dominio exterior
    Y_F_3d = np.zeros(shape_3d, dtype=np.float64)
    Y_O_3d = np.full(shape_3d, Y_O_inf, dtype=np.float64)
    T_3d = np.full(shape_3d, T_0, dtype=np.float64)

    # b) Chispa térmica inicial suave y semilla difusiva cerca del quemador (r_b < R < 2.2 * r_b)
    if warm_start:
        r_spark_inner = r_b
        r_spark_outer = 2.2 * r_b
        r_spark_center = 1.5 * r_b
        sigma_spark = 0.35 * r_b

        # Cáscara esférica gaussiana suave para evitar gradientes abruptos
        spark_shell_mask = (R > r_spark_inner) & (R <= r_spark_outer)
        gaussian_profile = np.exp(-0.5 * ((R - r_spark_center) / sigma_spark) ** 2)

        # Precalentamiento suave hasta T_spark_peak_K (~1350 - 1400 K)
        T_spark_field = T_0 + (T_spark_peak_K - T_0) * gaussian_profile
        T_3d = np.where(spark_shell_mask, np.maximum(T_3d, T_spark_field), T_3d)

        # Semilla suave de difusión de combustible en la vecindad inmediata del quemador
        # para que la primera evaluación de Arrhenius encuentre ambos reactivos (C_F * C_O > 0)
        R_safe = np.maximum(R, r_b)
        seed_decay = np.exp(-(R_safe - r_b) / (0.6 * r_b))
        Y_F_seed = Y_F_in * (r_b / R_safe) * seed_decay
        Y_F_3d = np.where(~mask_burner & ~mask_outer, Y_F_seed, Y_F_3d)
        Y_O_3d = np.where(
            ~mask_burner & ~mask_outer,
            Y_O_inf * (1.0 - 0.5 * seed_decay),
            Y_O_3d,
        )

    # c) Imposición estricta en la esfera del quemador y en las fronteras exteriores
    Y_F_3d, Y_O_3d, T_3d = apply_boundary_conditions_3d(
        Y_F_3d, Y_O_3d, T_3d, grid_dict, sim_input
    )

    return Y_F_3d, Y_O_3d, T_3d


# =============================================================================
# 3. IMPOSICIÓN DE CONDICIONES DE FRONTERA EN CADA PASO dt (Tarea A4.1 - Función 2)
# =============================================================================
def apply_boundary_conditions_3d(
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    T_3d: np.ndarray,
    grid_dict: Dict[str, Any],
    sim_input: Any,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Se llama al final de cada paso de tiempo dt.
    1. Acota físicamente las fracciones másicas en [0.0, 1.0] y la temperatura >= min(T_0, T_b).
    2. Fija los valores de inyección dentro de la máscara esférica del quemador (mask_burner):
       Y_F = Y_F_burner, Y_O = 0.0, T = T_burner_K.
    3. Fija las condiciones ambientales de cámara lejos de la llama (mask_outer):
       Y_F = 0.0, Y_O = Y_O_ambient, T = T_initial_K.
    Devuelve la tupla actualizada (Y_F_3d, Y_O_3d, T_3d).
    """
    params = _extract_bc_params(sim_input)
    Y_F_in = params["Y_F_burner"]
    Y_O_inf = params["Y_O_ambient"]
    T_0 = params["T_initial_K"]
    T_b = params["T_burner_K"]

    mask_burner = grid_dict["mask_burner"]
    mask_outer = grid_dict["mask_outer"]

    # Recorte de seguridad física en todo el dominio
    np.clip(Y_F_3d, 0.0, 1.0, out=Y_F_3d)
    np.clip(Y_O_3d, 0.0, 1.0, out=Y_O_3d)
    T_min_allowed = min(T_0, T_b)
    np.clip(T_3d, T_min_allowed, 4500.0, out=T_3d)

    # Condición de frontera interna: Esfera porosa del quemador (R <= r_b)
    Y_F_3d[mask_burner] = Y_F_in
    Y_O_3d[mask_burner] = 0.0
    T_3d[mask_burner] = T_b

    # Condición de frontera externa: Paredes de la cámara / campo lejano (mask_outer)
    Y_F_3d[mask_outer] = 0.0
    Y_O_3d[mask_outer] = Y_O_inf
    T_3d[mask_outer] = T_0

    return Y_F_3d, Y_O_3d, T_3d


def apply_boundary_masks_3d(
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    T_3d: np.ndarray,
    grid_dict: Dict[str, Any],
    cond_dict: Any,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Alias de compatibilidad exacta con la firma de proyecto_acme (1).pdf.
    """
    return apply_boundary_conditions_3d(Y_F_3d, Y_O_3d, T_3d, grid_dict, cond_dict)


# =============================================================================
# 4. BLOQUE DE PRUEBA DIRECTA EN TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=== PRUEBA DE CONDICIONES INICIALES Y FRONTERA 3D (ia/initial_boundary.py) ===")

    # Crear malla 3D de prueba (41x41x41) por si Rodolfo aún no sube grid_3d.py
    L = 0.035
    N = 41
    r_b = 0.00318
    x = np.linspace(-L, L, N)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    R = np.sqrt(X**2 + Y**2 + Z**2)
    mask_burner = R <= r_b
    mask_outer = (R >= 0.95 * L)
    mask_outer[0, :, :] = True
    mask_outer[-1, :, :] = True
    mask_outer[:, 0, :] = True
    mask_outer[:, -1, :] = True
    mask_outer[:, :, 0] = True
    mask_outer[:, :, -1] = True

    dummy_grid = {
        "x": x, "y": x, "z": x,
        "X": X, "Y": Y, "Z": Z, "R": R,
        "mask_burner": mask_burner,
        "mask_outer": mask_outer,
    }

    sim_in = SimulationInputSI()
    Y_F, Y_O, T = initialize_fields_3d(dummy_grid, sim_in, warm_start=True)

    # Validar con el guardián de tensores 3D del Bloque 2
    assert_valid_3d_fields(T, Y_F, Y_O)

    print(f"[OK] Cubos 3D inicializados con forma: {T.shape}")
    print(f"     Celdas dentro del quemador (R <= {r_b} m): {int(np.sum(mask_burner))}")
    print(f"     En quemador -> Y_F={np.mean(Y_F[mask_burner]):.3f}, Y_O={np.mean(Y_O[mask_burner]):.3f}, T={np.mean(T[mask_burner]):.1f} K")
    print(f"     En frontera -> Y_F={np.mean(Y_F[mask_outer]):.3f}, Y_O={np.mean(Y_O[mask_outer]):.3f}, T={np.mean(T[mask_outer]):.2f} K")
    print(f"     Chispa de ignición máxima en t=0 s -> T_max = {np.max(T):.1f} K")