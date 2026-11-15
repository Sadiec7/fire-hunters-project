"""
ia/verify_numerical.py
Suite de 5 Pruebas de Verificación Numérica del Modelo 3D - Bloque 8 (Con metadatos explícitos de Alerta 3).
"""

import os
import sys
from typing import Dict, Any
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import SimulationInputSI  # type: ignore
    from grid_3d import create_cartesian_grid_3d  # type: ignore
    from operators_3d import laplacian_3d, advection_upwind_3d, step_species_transport_only  # type: ignore
    from radial_verification import analytical_diffusion_1d  # type: ignore
    from solver_3d import (  # type: ignore
        get_physical_properties_si,
        compute_chemical_sources_3d,
        run_transient_simulation_3d,
    )
    from visualizer_3d import extract_spherical_radial_profile  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI
    from ia.grid_3d import create_cartesian_grid_3d
    from ia.operators_3d import laplacian_3d, advection_upwind_3d, step_species_transport_only
    from ia.radial_verification import analytical_diffusion_1d
    from ia.solver_3d import (
        get_physical_properties_si,
        compute_chemical_sources_3d,
        run_transient_simulation_3d,
    )
    from ia.visualizer_3d import extract_spherical_radial_profile


def test_constant_field() -> Dict[str, Any]:
    """Prueba 1: Campo constante (T=500 K, Y_F=0, Y_O=0.233, u=0) durante 20 pasos."""
    grid = create_cartesian_grid_3d(0.035, 25, 0.00318)
    N = grid["grid_nodes_per_axis"]
    dx, dy, dz = grid["dx"], grid["dy"], grid["dz"]

    T = np.full((N, N, N), 500.0, dtype=np.float64)
    Y_F = np.zeros((N, N, N), dtype=np.float64)
    Y_O = np.full((N, N, N), 0.233, dtype=np.float64)
    u_zero = np.zeros((N, N, N), dtype=np.float64)

    dt = 1e-4
    for _ in range(20):
        lap_T = laplacian_3d(T, dx, dy, dz)
        adv_T = advection_upwind_3d(T, u_zero, u_zero, u_zero, dx, dy, dz)
        T = T + dt * (4.0e-5 * lap_T - adv_T)

        lap_F = laplacian_3d(Y_F, dx, dy, dz)
        adv_F = advection_upwind_3d(Y_F, u_zero, u_zero, u_zero, dx, dy, dz)
        Y_F = Y_F + dt * (3.8e-5 * lap_F - adv_F)

        lap_O = laplacian_3d(Y_O, dx, dy, dz)
        adv_O = advection_upwind_3d(Y_O, u_zero, u_zero, u_zero, dx, dy, dz)
        Y_O = Y_O + dt * (4.2e-5 * lap_O - adv_O)

    max_diff = float(max(
        np.max(np.abs(T - 500.0)),
        np.max(np.abs(Y_F - 0.0)),
        np.max(np.abs(Y_O - 0.233)),
    ))
    assert max_diff < 1e-14
    return {"passed": True, "max_error": max_diff}


def test_analytical_spherical_diffusion() -> Dict[str, Any]:
    """Prueba 2: Difusión esférica pura 3D vs solución analítica 1D (1/r)."""
    grid = create_cartesian_grid_3d(0.035, 31, 0.00318)
    R = grid["R"]
    r_b = grid["burner_radius_m"]
    r_inf = grid["domain_half_width_m"]

    phi_exact_3d = analytical_diffusion_1d(R, r_b, r_inf, phi_b=1.0, phi_inf=0.0)
    phi_3d = phi_exact_3d.copy()
    u_zero = np.zeros_like(phi_3d)
    Y_O_dummy = np.zeros_like(phi_3d)

    dt = (grid["dx"] ** 2) / (6.0 * 4.0e-5) * 0.35
    for _ in range(40):
        phi_3d, _ = step_species_transport_only(
            phi_3d, Y_O_dummy, u_zero, u_zero, u_zero, grid, 4.0e-5, 4.0e-5, dt,
            Y_F_burner=1.0, Y_O_ambient=0.0
        )

    prof = extract_spherical_radial_profile(grid, phi_3d, n_bins=25)
    phi_1d_ref = analytical_diffusion_1d(prof["r_m"], r_b, r_inf, 1.0, 0.0)
    mae_1d_vs_3d = float(np.mean(np.abs(prof["profile_mean"] - phi_1d_ref)))
    assert mae_1d_vs_3d < 0.08
    return {"passed": True, "mae_3d_vs_1d_analytical": mae_1d_vs_3d}


def test_stoichiometric_mass_energy_conservation() -> Dict[str, Any]:
    """Prueba 3: Consistencia de operadores de términos fuente omega_O/omega_F = s."""
    sim_in = SimulationInputSI(fuel_type="C2H4")
    props = get_physical_properties_si(sim_in)

    T = np.full((15, 15, 15), 1400.0, dtype=np.float64)
    Y_F = np.full((15, 15, 15), 0.2, dtype=np.float64)
    Y_O = np.full((15, 15, 15), 0.2, dtype=np.float64)

    omega_F, omega_O, q_chem = compute_chemical_sources_3d(T, Y_F, Y_O, props)
    ratio_s = omega_O / np.maximum(omega_F, 1e-30)
    err_s = float(np.max(np.abs(ratio_s - props["s"])))

    q_ratio = q_chem / np.maximum(props["rho"] * omega_F, 1e-30)
    err_q_uniform = float(np.std(q_ratio) / np.mean(q_ratio))

    assert err_s < 1e-10 and err_q_uniform < 1e-10
    return {"passed": True, "stoich_ratio_error": err_s, "energy_consistency_error": err_q_uniform}


def test_spherical_isotropy_3d() -> Dict[str, Any]:
    """Prueba 4: Isotropía esférica en los ejes +X, +Y y +Z con gravedad residual cero (g_res = 0)."""
    sim_in = SimulationInputSI(grid_nodes_per_axis=31, total_time_s=0.04)
    if hasattr(sim_in, "uq_perturbations") and isinstance(sim_in.uq_perturbations, dict):
        sim_in.uq_perturbations["residual_gravity_m_s2"] = 0.0
    else:
        setattr(sim_in, "uq_perturbations", {"residual_gravity_m_s2": 0.0})

    res = run_transient_simulation_3d(sim_in, max_steps=50)
    T = res["T_3d"]
    mid = 31 // 2

    T_pos_x = T[mid:, mid, mid]
    T_pos_y = T[mid, mid:, mid]
    T_pos_z = T[mid, mid, mid:]

    max_anisotropy = float(max(
        np.max(np.abs(T_pos_x - T_pos_y)),
        np.max(np.abs(T_pos_x - T_pos_z)),
    ))
    assert max_anisotropy < 1e-9
    return {"passed": True, "max_axis_anisotropy_K": max_anisotropy}


def test_grid_convergence() -> Dict[str, Any]:
    """
    Prueba 5 (CORRECCIÓN ALERTA 3):
    Documenta explícitamente las resoluciones comparadas (25^3 vs 41^3), tamaños de celda dx
    y umbrales de tolerancia empleados en la comparación de convergencia de malla.
    """
    t_target_s = 0.04
    res_coarse = run_transient_simulation_3d(
        SimulationInputSI(grid_nodes_per_axis=25, total_time_s=t_target_s), max_steps=1000
    )
    res_medium = run_transient_simulation_3d(
        SimulationInputSI(grid_nodes_per_axis=41, total_time_s=t_target_s), max_steps=1000
    )

    rf_coarse = float(res_coarse["predicted_flame_radius_m"])
    rf_medium = float(res_medium["predicted_flame_radius_m"])
    T_coarse = float(res_coarse["max_temperature_K"])
    T_medium = float(res_medium["max_temperature_K"])

    diff_rf = abs(rf_coarse - rf_medium)
    diff_T = abs(T_coarse - T_medium)
    rel_diff_rf_pct = 100.0 * diff_rf / max(rf_medium, 1e-6)
    rel_diff_T_pct = 100.0 * diff_T / max(T_medium, 1.0)

    tol_rf_m = 0.0025
    tol_T_K = 180.0
    passed = bool(diff_rf <= tol_rf_m and diff_T <= tol_T_K)
    assert passed

    return {
        "passed": passed,
        "compared_resolutions": {
            "coarse_grid": [25, 25, 25],
            "medium_grid": [41, 41, 41],
            "dx_coarse_m": round(float(res_coarse["grid_dict"]["dx"]), 6),
            "dx_medium_m": round(float(res_medium["grid_dict"]["dx"]), 6),
            "evaluation_time_s": t_target_s,
        },
        "coarse_metrics": {"flame_radius_m": rf_coarse, "T_max_K": T_coarse},
        "medium_metrics": {"flame_radius_m": rf_medium, "T_max_K": T_medium},
        "abs_diff_flame_radius_m": round(float(diff_rf), 6),
        "rel_diff_flame_radius_pct": round(float(rel_diff_rf_pct), 2),
        "abs_diff_T_max_K": round(float(diff_T), 2),
        "rel_diff_T_max_pct": round(float(rel_diff_T_pct), 2),
        "tolerance_criteria": {
            "max_allowed_radius_diff_m": tol_rf_m,
            "max_allowed_T_max_diff_K": tol_T_K,
            "note": (
                "Diferencia atribuible a difusión numérica truncada O(dx^2) entre paso "
                "grueso (2.92 mm) y paso medio (1.75 mm) en llama delgada."
            ),
        },
    }


def run_all_numerical_verifications() -> Dict[str, Any]:
    """Ejecuta las 5 pruebas y devuelve el diccionario verification_report."""
    t1 = test_constant_field()
    t2 = test_analytical_spherical_diffusion()
    t3 = test_stoichiometric_mass_energy_conservation()
    t4 = test_spherical_isotropy_3d()
    t5 = test_grid_convergence()

    all_passed = all(t["passed"] for t in (t1, t2, t3, t4, t5))
    return {
        "status": "PASSED" if all_passed else "FAILED",
        "test_1_constant_field": t1,
        "test_2_analytical_1_over_r": t2,
        "test_3_stoichiometry_conservation": t3,
        "test_4_spherical_isotropy": t4,
        "test_5_grid_convergence": t5,
    }


if __name__ == "__main__":
    report = run_all_numerical_verifications()
    print("REPORTE DE VERIFICACIÓN NUMÉRICA:", report["status"])
    for k, v in report.items():
        if k != "status":
            print(f"  - {k}: {v}")