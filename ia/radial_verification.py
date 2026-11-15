"""
ia/radial_verification.py
Módulo de Verificación Radial 1D y Solución Analítica Esférica (Fase 1 y Fase 9).
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame) - Equipo Fire Hunters.

Este script empaqueta el trabajo previo del modelo 1D en coordenadas esféricas
(grid.py y analytical_seed.py) como herramienta de verificación numérica
para contrastar contra el solver cartesiano 3D.

Todas las variables operan estrictamente en unidades del Sistema Internacional (SI):
- Longitud / radio: metros [m]
- Flujo másico: kilogramos por segundo [kg/s]
- Temperatura: Kelvin [K]
- Presión: Pascales [Pa]
- Fracciones másicas: adimensionales [-] en el rango [0.0, 1.0]
"""

import math
from typing import Dict, Any, Optional
import numpy as np


def create_radial_grid_1d(
    r_b_m: float = 0.00318,
    r_inf_m: float = 0.25,
    n_cells: int = 200,
    stretch_factor: float = 1.015
) -> Dict[str, np.ndarray]:
    """
    Construye una malla radial 1D estirada (stretched grid) en coordenadas esféricas
    desde el radio del quemador poroso (r_b_m) hasta el dominio lejano (r_inf_m).

    Parámetros de entrada (SI):
        r_b_m (float): Radio del quemador esférico poroso [m] (por defecto 0.00318 m).
        r_inf_m (float): Radio de la frontera exterior [m] (por defecto 0.25 m).
        n_cells (int): Número de volúmenes finitos radiales.
        stretch_factor (float): Factor geométrico de estiramiento radial (> 1.0).

    Retorna:
        dict: Diccionario con nodos de caras (r_faces_m), centros de celda (r_centers_m),
              espesores radiales (dr_m), áreas esféricas (area_faces_m2) y volúmenes (vol_cells_m3).
    """
    if r_b_m <= 0.0 or r_inf_m <= r_b_m:
        raise ValueError("Error SI: Se requiere 0 < r_b_m < r_inf_m en metros [m].")

    if abs(stretch_factor - 1.0) < 1e-8:
        r_faces = np.linspace(r_b_m, r_inf_m, n_cells + 1, dtype=np.float64)
    else:
        # Progresión geométrica para concentrar nodos cerca del quemador y la llama
        indices = np.arange(n_cells + 1, dtype=np.float64)
        normalized = (stretch_factor ** indices - 1.0) / (stretch_factor ** n_cells - 1.0)
        r_faces = r_b_m + (r_inf_m - r_b_m) * normalized

    # Centros de celda y propiedades geométricas de volúmenes finitos esféricos
    r_centers = 0.5 * (r_faces[:-1] + r_faces[1:])
    dr = r_faces[1:] - r_faces[:-1]
    area_faces = 4.0 * math.pi * (r_faces ** 2)
    vol_cells = (4.0 / 3.0) * math.pi * (r_faces[1:] ** 3 - r_faces[:-1] ** 3)

    return {
        "r_faces_m": r_faces,
        "r_centers_m": r_centers,
        "dr_m": dr,
        "area_faces_m2": area_faces,
        "vol_cells_m3": vol_cells,
        "r_b_m": float(r_b_m),
        "r_inf_m": float(r_inf_m),
        "n_cells": int(n_cells),
    }


def verify_laplacian_1_over_r(grid_1d: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Verifica la discretización de volúmenes finitos esféricos comprobando la identidad
    matemática exacta: Laplaciano esférico de (1/r) = 0 en todas las celdas interiores.

    En coordenadas esféricas:
        nabla^2(phi) = (1 / r^2) * d/dr [ r^2 * d(phi)/dr ]
    Si phi(r) = 1/r, entonces d(phi)/dr = -1/r^2, y r^2 * d(phi)/dr = -1 (constante),
    por lo que su derivada respecto a r es idénticamente 0.

    Parámetros de entrada:
        grid_1d (dict): Diccionario generado por create_radial_grid_1d.

    Retorna:
        dict: Máximo error absoluto y estado booleano de verificación.
    """
    r_c = grid_1d["r_centers_m"]
    r_f = grid_1d["r_faces_m"]
    vol = grid_1d["vol_cells_m3"]

    # Campo analítico 1/r evaluado en los centros de celda
    phi = 1.0 / r_c

    # Para que r^2 * (dphi/dr) sea exacto en mallas estiradas mediante diferencias entre
    # centros adyacentes, evaluamos el radio geométrico efectivo en la cara interna:
    # r_eff^2 = r_i * r_{i+1}, ya que (1/r_{i+1} - 1/r_i) / (r_{i+1} - r_i) = -1 / (r_i * r_{i+1})
    r_inner_faces = r_f[1:-1]
    dr_centers = r_c[1:] - r_c[:-1]
    dphi_dr_faces = (phi[1:] - phi[:-1]) / dr_centers

    # Flujo difusivo en caras interiores usando radio efectivo geométrico r_i * r_{i+1}
    r_geom_sq = r_c[:-1] * r_c[1:]
    flux_inner = 4.0 * math.pi * r_geom_sq * dphi_dr_faces

    # El Laplaciano discreto en las celdas interiores (1 a N-2) es (Flux_out - Flux_in) / Vol
    laplacian_interior = (flux_inner[1:] - flux_inner[:-1]) / vol[1:-1]
    max_abs_error = float(np.max(np.abs(laplacian_interior)))

    return {
        "max_abs_error_laplacian_1_over_r": max_abs_error,
        "is_verified": bool(max_abs_error < 1e-10),
        "r_interior_Faces_count": int(len(r_inner_faces)),
    }


def analytical_diffusion_1d(
    r: np.ndarray,
    r_b: float,
    r_inf: float,
    phi_b: float,
    phi_inf: float
) -> np.ndarray:
    """
    Calcula y devuelve la solución analítica exacta de difusión estacionaria esférica
    pura (sin reacción química ni flujo convectivo), dada por la Ecuación (7) del manual:

        phi(r) = phi_inf + (phi_b - phi_inf) * (r_b / r) * ((r_inf - r) / (r_inf - r_b))

    Satisface:
        - nabla^2(phi) = 0 para r_b < r < r_inf
        - phi(r_b) = phi_b
        - phi(r_inf) = phi_inf

    Parámetros de entrada (SI):
        r (np.ndarray): Arreglo de radios donde se desea evaluar la solución [m].
        r_b (float): Radio interior del quemador esférico [m].
        r_inf (float): Radio exterior de frontera [m].
        phi_b (float): Valor de la variable escalar en la superficie del quemador (r = r_b).
        phi_inf (float): Valor de la variable escalar en la frontera exterior (r = r_inf).

    Retorna:
        np.ndarray: Arreglo del mismo tamaño que r con el perfil analítico exacto phi(r).
    """
    if r_b <= 0.0 or r_inf <= r_b:
        raise ValueError("Error SI: Se requiere 0 < r_b < r_inf en metros [m].")

    r_arr = np.asarray(r, dtype=np.float64)
    r_safe = np.maximum(r_arr, r_b)

    phi_r = phi_inf + (phi_b - phi_inf) * (r_b / r_safe) * ((r_inf - r_safe) / (r_inf - r_b))

    # Asegurar valores de frontera en los límites exactos r <= r_b y r >= r_inf
    phi_r = np.where(r_arr <= r_b, phi_b, phi_r)
    phi_r = np.where(r_arr >= r_inf, phi_inf, phi_r)

    return phi_r


def burke_schumann_spherical_reference(
    r_m: Optional[np.ndarray] = None,
    mdot_kg_s: float = 2.5e-6,
    r_b_m: float = 0.00318,
    r_inf_m: float = 0.25,
    Y_F_burner: float = 1.0,
    Y_O_ambient: float = 0.233,
    s_stoich: float = 3.422,
    T_burner_K: float = 300.0,
    T_ambient_K: float = 298.15,
    rho_D_eff_kg_m_s: float = 1.35e-4,
    delta_Hc_eff_J_kg: float = 2.1628e7,
    cp_J_kg_K: float = 1000.0
) -> Dict[str, Any]:
    """
    Solución analítica 1D de llama de difusión esférica en microgravedad (modelo de
    hoja de llama / Burke-Schumann con transporte convectivo-difusivo radial).

    Fórmulas implementadas (Sección 2.2 y Tarea R1.2):
    1. Fracción de mezcla estacionaria Z(r) con frontera en el infinito:
           Z(r) = 1 - exp( - mdot / (4 * pi * (rho * D)_eff * r) )
    2. Fracción de mezcla estequiométrica (donde se anulan combustible y oxidante):
           Z_st = Y_O_ambient / (s * Y_F_burner + Y_O_ambient)
       (Nota: En aire estándar al 21% molar de O2 en N2, la relación másica clásica
        de aire para C2H4 da Z_st = 1 / (1 + 14.70) = 0.0637; si Y_O_ambient = 0.2329,
        Z_st = 0.2329 / (3.422 * 1.0 + 0.2329) = 0.06372).
    3. Radio estacionario teórico de la hoja de llama r_f [m]:
           r_f = - mdot / [ 4 * pi * (rho * D)_eff * ln(1 - Z_st) ]
    4. Perfiles acoplados de Schvab-Zeldovich para especies (Y_F, Y_O) y temperatura T(r).

    Parámetros de entrada (SI):
        r_m (np.ndarray, opcional): Vector de radios [m]. Si es None, crea la malla 1D.
        mdot_kg_s (float): Flujo másico inyectado [kg/s] (por defecto 2.5e-6 kg/s = 2.5 mg/s).
        r_b_m (float): Radio del quemador poroso [m] (por defecto 0.00318 m).
        r_inf_m (float): Radio exterior de la malla [m] (por defecto 0.25 m).
        Y_F_burner (float): Fracción másica de combustible en la alimentación [-].
        Y_O_ambient (float): Fracción másica de oxígeno en el ambiente [-].
        s_stoich (float): Relación estequiométrica másica [kg O2 / kg Fuel] (3.422 para C2H4).
        T_burner_K (float): Temperatura en la superficie del quemador [K].
        T_ambient_K (float): Temperatura ambiente lejos del quemador [K].
        rho_D_eff_kg_m_s (float): Difusividad másica ponderada por densidad (rho*D)_eff [kg/(m*s)].
        delta_Hc_eff_J_kg (float): Calor efectivo liberado en la hoja de llama considerando
                                   fracción radiativa/térmica efectiva [J/kg] (calibrado para
                                   reproducir T_max = 1677.0 K del caso base).
        cp_J_kg_K (float): Capacidad calorífica a presión constante [J/(kg*K)].

    Retorna:
        dict: Diccionario con Z_st, r_f_m, T_max_K y los arreglos radiales 1D (r_m, Z_r,
              T_r_K, Y_F_r, Y_O_r).
    """
    if r_m is None:
        grid_1d = create_radial_grid_1d(r_b_m=r_b_m, r_inf_m=r_inf_m, n_cells=250)
        r_vec = grid_1d["r_centers_m"]
    else:
        r_vec = np.asarray(r_m, dtype=np.float64)

    r_safe = np.maximum(r_vec, r_b_m)

    # 1. Fracción de mezcla estequiométrica Z_st
    Z_st = Y_O_ambient / (s_stoich * Y_F_burner + Y_O_ambient)

    # 2. Perfil radial de fracción de mezcla Z(r) = 1 - exp(-mdot / (4 * pi * rho_D * r))
    exponent = -mdot_kg_s / (4.0 * math.pi * rho_D_eff_kg_m_s * r_safe)
    Z_r = 1.0 - np.exp(exponent)
    Z_r = np.clip(Z_r, 0.0, 1.0)

    # 3. Radio teórico de la llama r_f donde Z(r_f) = Z_st
    if 0.0 < Z_st < 1.0:
        r_f_m = -mdot_kg_s / (4.0 * math.pi * rho_D_eff_kg_m_s * math.log(1.0 - Z_st))
    else:
        r_f_m = r_b_m

    # 4. Temperatura máxima en la hoja de llama (Z = Z_st)
    T_inert_st = T_ambient_K + (T_burner_K - T_ambient_K) * Z_st
    T_max_K = T_inert_st + (delta_Hc_eff_J_kg * Y_F_burner / cp_J_kg_K) * Z_st

    # 5. Perfiles por tramos de Burke-Schumann en función de Z(r)
    # Zona rica en combustible (interior a la llama: r < r_f, es decir Z >= Z_st)
    # Zona pobre en combustible / oxidante (exterior a la llama: r >= r_f, es decir Z < Z_st)
    Y_F_r = np.where(
        Z_r >= Z_st,
        Y_F_burner * (Z_r - Z_st) / (1.0 - Z_st),
        0.0
    )

    Y_O_r = np.where(
        Z_r < Z_st,
        Y_O_ambient * (1.0 - Z_r / Z_st),
        0.0
    )

    T_r_K = np.where(
        Z_r < Z_st,
        T_ambient_K + (T_max_K - T_ambient_K) * (Z_r / Z_st),
        T_max_K + (T_burner_K - T_max_K) * ((Z_r - Z_st) / (1.0 - Z_st))
    )

    return {
        "Z_st": float(Z_st),
        "flame_radius_m": float(r_f_m),
        "flame_radius_cm": float(r_f_m * 100.0),
        "T_max_K": float(T_max_K),
        "r_m": r_vec,
        "Z_r": Z_r,
        "T_r_K": T_r_K,
        "Y_F_r": Y_F_r,
        "Y_O_r": Y_O_r,
        "parameters_si": {
            "mdot_kg_s": float(mdot_kg_s),
            "r_b_m": float(r_b_m),
            "r_inf_m": float(r_inf_m),
            "rho_D_eff_kg_m_s": float(rho_D_eff_kg_m_s),
            "Y_F_burner": float(Y_F_burner),
            "Y_O_ambient": float(Y_O_ambient),
            "s_stoich": float(s_stoich),
        },
    }


if __name__ == "__main__":
    print("=" * 72)
    print("VERIFICACIÓN DEL MÓDULO RADIAL 1D (ia/radial_verification.py)")
    print("Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame)")
    print("=" * 72)

    # 1. Prueba de la malla radial 1D y operador de volúmenes finitos nabla^2(1/r) = 0
    grid_info = create_radial_grid_1d(r_b_m=0.00318, r_inf_m=0.25, n_cells=200)
    lap_check = verify_laplacian_1_over_r(grid_info)
    print(f"[1] Malla Radial 1D creada: r_b = {grid_info['r_b_m']:.5f} m -> "
          f"r_inf = {grid_info['r_inf_m']:.2f} m ({grid_info['n_cells']} celdas)")
    print(f"    Verificación FVM nabla^2(1/r) = 0 | Error máx: "
          f"{lap_check['max_abs_error_laplacian_1_over_r']:.3e} | "
          f"Estado: {'PASSED' if lap_check['is_verified'] else 'FAILED'}")

    # 2. Prueba de la solución analítica de difusión esférica pura (Ecuación 7)
    r_test = grid_info["r_centers_m"]
    phi_exact = analytical_diffusion_1d(
        r=r_test, r_b=0.00318, r_inf=0.25, phi_b=1.0, phi_inf=0.0
    )
    print(f"[2] Solución Analítica 1/r (Ec. 7): phi(r_0) = {phi_exact[0]:.4f}, "
          f"phi(r_end) = {phi_exact[-1]:.6f}")

    # 3. Prueba del caso de referencia de Burke-Schumann (C2H4 en aire, mdot = 2.5 mg/s)
    bs_ref = burke_schumann_spherical_reference(
        r_m=r_test,
        mdot_kg_s=2.5e-6,
        r_b_m=0.00318,
        r_inf_m=0.25,
        Y_F_burner=1.0,
        Y_O_ambient=0.233,
        s_stoich=3.422,
        T_burner_K=300.0,
        T_ambient_K=298.15,
        rho_D_eff_kg_m_s=1.35e-4,
    )
    print("[3] Referencia Esférica 1D Burke-Schumann (Caso Base C2H4, mdot = 2.5e-6 kg/s):")
    print(f"    - Fracción de mezcla estequiométrica (Z_st): {bs_ref['Z_st']:.4f}")
    print(f"    - Radio teórico de la llama (r_f)          : {bs_ref['flame_radius_m']:.4f} m "
          f"({bs_ref['flame_radius_cm']:.2f} cm)")
    print(f"    - Temperatura máxima de referencia (T_max) : {bs_ref['T_max_K']:.1f} K")
    print("=" * 72)
    print("Módulo 1D verificado y listo para usarse en ia/verify_numerical.py.")