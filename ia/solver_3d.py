"""
ia/solver_3d.py
Solver Transitorio 3D con Residuos L2, Estado Estacionario, CFL/Fo y Exportación .npz (IGNIS-mu).
"""

import os
import sys
from typing import Dict, Any, Tuple, Union
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ia.contract_si import SimulationInputSI, validate_input_si, assert_valid_3d_fields, R_U_J_MOL_K
    from ia.grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d
    from ia.operators_3d import laplacian_3d, advection_upwind_3d
except ImportError:
    from contract_si import SimulationInputSI, validate_input_si, assert_valid_3d_fields, R_U_J_MOL_K  # type: ignore
    from grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d  # type: ignore
    from operators_3d import laplacian_3d, advection_upwind_3d  # type: ignore

FUEL_DB_FALLBACK = {
    "C2H4": {"W_F": 0.02805, "s": 3.422, "delta_Hc": 4.716e7, "Ea": 1.255e5, "A": 1.2e9, "D_F0": 3.8e-5},
    "CH4":  {"W_F": 0.01604, "s": 3.989, "delta_Hc": 5.002e7, "Ea": 1.255e5, "A": 8.5e8, "D_F0": 4.5e-5},
    "H2":   {"W_F": 0.002016, "s": 7.937, "delta_Hc": 1.199e8, "Ea": 8.314e4, "A": 2.5e9, "D_F0": 1.4e-4},
}


def get_physical_properties_si(sim_input: SimulationInputSI) -> Dict[str, Any]:
    f = FUEL_DB_FALLBACK[sim_input.fuel_type]
    uq = getattr(sim_input, "uq_perturbations", {}) or {}

    p_scale = 101325.0 / sim_input.pressure_Pa
    T_ref = 950.0
    W_mean = 0.0288
    rho = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * T_ref)

    D_F = f["D_F0"] * p_scale * ((T_ref / 300.0) ** 1.75) * float(uq.get("D_F_factor", 1.0))
    D_O = 4.2e-5 * p_scale * ((T_ref / 300.0) ** 1.75) * float(uq.get("D_O_factor", 1.0))
    alpha = 4.5e-5 * p_scale * ((T_ref / 300.0) ** 1.75) * float(uq.get("alpha_factor", 1.0))
    cp = 1150.0 * float(uq.get("c_p_factor", 1.0))
    A = f["A"] * float(uq.get("A_preexp_factor", 1.0))
    Ea = f["Ea"] + float(uq.get("E_a_offset_J_mol", 0.0))
    Xr = float(uq.get("radiative_loss_fraction_Xr", 0.15))

    return {
        "rho": float(rho),
        "cp": float(cp),
        "D_F": float(D_F),
        "D_O": float(D_O),
        "alpha": float(alpha),
        "s": f["s"],
        "delta_Hc": f["delta_Hc"],
        "A": float(A),
        "Ea": float(Ea),
        "W_F": f["W_F"],
        "Xr": float(Xr),
    }


def compute_chemical_sources_3d(
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    props_dict: Dict[str, Any],
    dt_s: float = None,
    mask_burner: np.ndarray = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rho = props_dict["rho"]
    s = props_dict["s"]
    delta_Hc = props_dict["delta_Hc"]
    A = props_dict["A"]
    Ea = props_dict["Ea"]
    Xr = props_dict.get("Xr", 0.15)

    Y_F_clean = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_clean = np.clip(Y_O_3d, 0.0, 1.0)
    T_safe = np.maximum(T_3d, 250.0)

    C_F = rho * Y_F_clean
    C_O = rho * Y_O_clean

    arrhenius = A * np.exp(-Ea / (R_U_J_MOL_K * T_safe))
    arrhenius = np.where(T_safe > 500.0, arrhenius, 0.0)
    r_rxn = arrhenius * C_F * C_O

    omega_F = r_rxn / rho
    if dt_s is not None and dt_s > 0.0:
        omega_max = 0.45 * np.minimum(Y_F_clean / dt_s, Y_O_clean / (s * dt_s))
        omega_F = np.minimum(omega_F, omega_max)

    if mask_burner is not None:
        omega_F = np.where(mask_burner, 0.0, omega_F)

    omega_O = s * omega_F
    q_chem = 0.48 * (1.0 - Xr) * rho * omega_F * delta_Hc
    return omega_F, omega_O, q_chem


try:
    from ia.initial_boundary import initialize_fields_3d, apply_boundary_conditions_3d  # type: ignore
except ImportError:
    try:
        from initial_boundary import initialize_fields_3d, apply_boundary_conditions_3d  # type: ignore
    except ImportError:
        def initialize_fields_3d(
            grid_dict: Dict[str, Any],
            sim_input: SimulationInputSI
        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            R = grid_dict["R"]
            r_b = sim_input.burner_radius_m
            mask_b = grid_dict["mask_burner"]
            mask_o = grid_dict["mask_outer"]

            r_safe = np.maximum(R, r_b)
            Y_F_3d = sim_input.Y_F_burner * (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.012)
            Y_O_3d = sim_input.Y_O_ambient * (1.0 - (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.018))
            Y_F_3d = np.clip(Y_F_3d, 0.0, 1.0)
            Y_O_3d = np.clip(Y_O_3d, 0.0, 1.0)

            T_3d = np.full_like(R, sim_input.T_initial_K, dtype=np.float64)
            r_spark_center = 0.016
            spark_profile = np.exp(-((R - r_spark_center) / 0.0065) ** 2)
            T_3d = T_3d + (1650.0 - sim_input.T_initial_K) * spark_profile

            Y_F_3d[mask_b] = sim_input.Y_F_burner
            Y_O_3d[mask_b] = 0.0
            T_3d[mask_b] = sim_input.T_burner_K

            Y_F_3d[mask_o] = 0.0
            Y_O_3d[mask_o] = sim_input.Y_O_ambient
            T_3d[mask_o] = sim_input.T_initial_K
            return Y_F_3d, Y_O_3d, T_3d

        def apply_boundary_conditions_3d(
            Y_F_3d: np.ndarray,
            Y_O_3d: np.ndarray,
            T_3d: np.ndarray,
            grid_dict: Dict[str, Any],
            sim_input: SimulationInputSI
        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            mask_b = grid_dict["mask_burner"]
            mask_o = grid_dict["mask_outer"]

            Y_F_3d[mask_b] = sim_input.Y_F_burner
            Y_O_3d[mask_b] = 0.0
            T_3d[mask_b] = sim_input.T_burner_K

            Y_F_3d[mask_o] = 0.0
            Y_O_3d[mask_o] = sim_input.Y_O_ambient
            T_3d[mask_o] = sim_input.T_initial_K
            return Y_F_3d, Y_O_3d, T_3d


def compute_l2_normalized_residual(phi_new: np.ndarray, phi_old: np.ndarray, dt: float) -> float:
    """Fórmula Entregable 4: Norma L2 de la tasa de cambio relativa."""
    denom = dt * max(float(np.max(np.abs(phi_old))), 1e-12)
    diff_rel = (phi_new - phi_old) / denom
    return float(np.sqrt(np.mean(diff_rel ** 2)))


def compute_stable_timestep_s(
    grid_dict: Dict[str, Any],
    props_dict: Dict[str, Any],
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray
) -> float:
    dx = grid_dict["dx"]
    D_max = max(props_dict["D_F"], props_dict["D_O"], props_dict["alpha"])
    dt_diff = (dx * dx) / (6.0 * D_max + 1e-15)
    u_sum_max = float(np.max(np.abs(u_x) + np.abs(u_y) + np.abs(u_z)))
    dt_adv = dx / (u_sum_max + 1e-12)
    return float(0.4 * min(dt_diff, dt_adv))


def compute_stable_dt(grid_dict: Dict[str, Any], props_dict: Dict[str, Any], u_max: float) -> float:
    dx = grid_dict["dx"]
    D_max = max(props_dict["D_F"], props_dict["D_O"], props_dict["alpha"])
    dt_diff = (dx * dx) / (6.0 * D_max + 1e-15)
    dt_adv = dx / (3.0 * u_max + 1e-12)
    return float(0.4 * min(dt_diff, dt_adv))


def step_forward_3d(
    Y_F: np.ndarray,
    Y_O: np.ndarray,
    T: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray,
    grid_dict: Dict[str, Any],
    props_dict: Dict[str, Any],
    sim_input: SimulationInputSI,
    dt: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dx, dy, dz = grid_dict["dx"], grid_dict["dy"], grid_dict["dz"]

    omega_F, omega_O, q_chem = compute_chemical_sources_3d(
        T, Y_F, Y_O, props_dict, dt_s=dt, mask_burner=grid_dict["mask_burner"]
    )

    lap_YF = laplacian_3d(Y_F, dx, dy, dz)
    adv_YF = advection_upwind_3d(Y_F, u_x, u_y, u_z, dx, dy, dz)

    lap_YO = laplacian_3d(Y_O, dx, dy, dz)
    adv_YO = advection_upwind_3d(Y_O, u_x, u_y, u_z, dx, dy, dz)

    lap_T = laplacian_3d(T, dx, dy, dz)
    adv_T = advection_upwind_3d(T, u_x, u_y, u_z, dx, dy, dz)

    Y_F_new = Y_F + dt * (props_dict["D_F"] * lap_YF - adv_YF - omega_F)
    Y_O_new = Y_O + dt * (props_dict["D_O"] * lap_YO - adv_YO - omega_O)
    T_new = T + dt * (
        props_dict["alpha"] * lap_T - adv_T + q_chem / (props_dict["rho"] * props_dict["cp"])
    )

    Y_F_new = np.clip(Y_F_new, 0.0, 1.0)
    Y_O_new = np.clip(Y_O_new, 0.0, 1.0)
    T_new = np.clip(T_new, min(sim_input.T_initial_K, sim_input.T_burner_K), 2600.0)

    apply_boundary_conditions_3d(Y_F_new, Y_O_new, T_new, grid_dict, sim_input)
    return Y_F_new, Y_O_new, T_new, q_chem


def export_3d_state_for_ignis(
    sim_results: Dict[str, Any],
    npz_path: str = "ia/output_fields_3d.npz"
) -> str:
    """Entregable 3: Guarda tensores 3D completos y referencias espaciales/temporales en .npz."""
    g = sim_results["grid_dict"]
    os.makedirs(os.path.dirname(os.path.abspath(npz_path)), exist_ok=True)
    np.savez_compressed(
        npz_path,
        T_3d=sim_results["T_3d"],
        Y_F_3d=sim_results["Y_F_3d"],
        Y_O_3d=sim_results["Y_O_3d"],
        Y_P_3d=sim_results["Y_P_3d"],
        rho_3d=sim_results["rho_3d"],
        u_x_3d=sim_results["u_x"],
        u_y_3d=sim_results["u_y"],
        u_z_3d=sim_results["u_z"],
        q_chem_3d=sim_results["q_chem_3d"],
        x_m=g["x_m"],
        y_m=g["y_m"],
        z_m=g["z_m"],
        time_history_s=np.asarray(sim_results["time_history_s"], dtype=np.float64),
    )
    return npz_path


def run_transient_simulation_3d(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    num_snapshots: int = 10,
    max_steps: int = 250
) -> Dict[str, Any]:
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    uq = getattr(sim_input, "uq_perturbations", {}) or {}
    g_res = float(uq.get("residual_gravity_m_s2", 1.0e-4))
    g_dir = uq.get("gravity_direction_unit", [0.0, 0.0, 1.0])

    grid_dict = create_cartesian_grid_3d(
        domain_half_width_m=sim_input.domain_half_width_m,
        grid_nodes_per_axis=sim_input.grid_nodes_per_axis,
        burner_radius_m=sim_input.burner_radius_m,
    )
    props_dict = get_physical_properties_si(sim_input)
    Y_F_3d, Y_O_3d, T_3d = initialize_fields_3d(grid_dict, sim_input)

    u_x, u_y, u_z = compute_prescribed_velocity_3d(
        grid_dict,
        sim_input.mass_flow_kg_s,
        props_dict["rho"],
        T_3d=T_3d,
        T_ambient_K=sim_input.T_initial_K,
        residual_gravity_m_s2=g_res,
        gravity_direction_unit=g_dir,
    )

    dt = compute_stable_timestep_s(grid_dict, props_dict, u_x, u_y, u_z)
    n_steps = min(max(int(sim_input.total_time_s / dt), 40), max_steps)
    snapshot_interval = max(1, n_steps // max(1, num_snapshots))

    time_history_s = []
    T_max_history_K = []
    r_f_history_m = []
    snapshots = []

    R = grid_dict["R"]
    q_chem_3d = np.zeros_like(T_3d)
    t_curr = 0.0

    res_T_l2 = 0.0
    res_YF_l2 = 0.0
    res_YO_l2 = 0.0
    res_rho_l2 = 0.0
    W_mean = 0.0288

    for step in range(1, n_steps + 1):
        T_old = T_3d.copy()
        YF_old = Y_F_3d.copy()
        YO_old = Y_O_3d.copy()
        rho_old = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_old, 250.0))

        if step % 10 == 0:
            u_x, u_y, u_z = compute_prescribed_velocity_3d(
                grid_dict,
                sim_input.mass_flow_kg_s,
                props_dict["rho"],
                T_3d=T_3d,
                T_ambient_K=sim_input.T_initial_K,
                residual_gravity_m_s2=g_res,
                gravity_direction_unit=g_dir,
            )

        Y_F_3d, Y_O_3d, T_3d, q_chem_3d = step_forward_3d(
            Y_F_3d, Y_O_3d, T_3d, u_x, u_y, u_z, grid_dict, props_dict, sim_input, dt
        )
        t_curr += dt

        if step == n_steps:
            rho_new = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_3d, 250.0))
            res_T_l2 = compute_l2_normalized_residual(T_3d, T_old, dt)
            res_YF_l2 = compute_l2_normalized_residual(Y_F_3d, YF_old, dt)
            res_YO_l2 = compute_l2_normalized_residual(Y_O_3d, YO_old, dt)
            res_rho_l2 = compute_l2_normalized_residual(rho_new, rho_old, dt)

        T_max_val = float(np.max(T_3d))
        hot_mask = T_3d >= (0.98 * T_max_val)
        r_f_val = float(np.mean(R[hot_mask])) if np.any(hot_mask) else sim_input.burner_radius_m

        time_history_s.append(round(t_curr, 6))
        T_max_history_K.append(round(T_max_val, 2))
        r_f_history_m.append(round(r_f_val, 5))

        if step % snapshot_interval == 0 or step == n_steps:
            snapshots.append({
                "step": step,
                "time_s": round(t_curr, 5),
                "T_max_K": round(T_max_val, 2),
                "flame_radius_m": round(r_f_val, 5),
            })

    assert_valid_3d_fields(T_3d, Y_F_3d, Y_O_3d)

    rho_3d = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_3d, 250.0))
    Y_N2_amb = max(0.0, 1.0 - sim_input.Y_O_ambient)
    Y_P_3d = np.clip(1.0 - Y_F_3d - Y_O_3d - Y_N2_amb * (Y_O_3d / max(sim_input.Y_O_ambient, 1e-6)), 0.0, 1.0)

    dx = grid_dict["dx"]
    cfl_max = float(np.max(np.abs(u_x) + np.abs(u_y) + np.abs(u_z)) * dt / dx)
    fo_max = float(max(props_dict["D_F"], props_dict["D_O"], props_dict["alpha"]) * dt / (dx * dx))

    window = min(100, len(time_history_s) - 1)
    dt_win = max(time_history_s[-1] - time_history_s[-1 - window], 1e-9)
    drf_dt_rel = abs(r_f_history_m[-1] - r_f_history_m[-1 - window]) / (dt_win * max(r_f_history_m[-1], 1e-6))
    dT_dt_rel = abs(T_max_history_K[-1] - T_max_history_K[-1 - window]) / (dt_win * max(T_max_history_K[-1], 1.0))
    steady_reached = bool(drf_dt_rel < 1e-2 and dT_dt_rel < 1e-2)

    N = grid_dict["grid_nodes_per_axis"]
    solver_metadata = {
        "solver_backend": getattr(sim_input, "solver_backend", "INTERNAL_3D_FDM"),
        "grid_resolution": [N, N, N],
        "dx_m": round(dx, 6),
        "spatial_scheme": "CENTRAL_DIFF_2ND_ORDER_DIFFUSION_UPWIND_1ST_ORDER_ADVECTION",
        "temporal_scheme": "EXPLICIT_EULER_CFL_FOURIER_LIMITED",
    }

    convergence_and_residuals = {
        "steady_state_reached": steady_reached,
        "L2_residuals": {
            "T_L2_s_inv": round(res_T_l2, 6),
            "Y_F_L2_s_inv": round(res_YF_l2, 6),
            "Y_O_L2_s_inv": round(res_YO_l2, 6),
            "rho_L2_s_inv": round(res_rho_l2, 6),
        },
        "relative_rates_last_window": {
            "dr_f_dt_rel_s_inv": round(float(drf_dt_rel), 6),
            "dT_max_dt_rel_s_inv": round(float(dT_dt_rel), 6),
        },
        "stability_numbers": {
            "CFL_max": round(cfl_max, 5),
            "Fourier_max": round(fo_max, 5),
            "dt_s": dt,
            "steps_executed": n_steps,
        },
    }

    return {
        "sim_input": sim_input,
        "grid_dict": grid_dict,
        "props_dict": props_dict,
        "solver_metadata": solver_metadata,
        "convergence_and_residuals": convergence_and_residuals,
        "T_3d": T_3d,
        "Y_F_3d": Y_F_3d,
        "Y_O_3d": Y_O_3d,
        "Y_P_3d": Y_P_3d,
        "rho_3d": rho_3d,
        "q_chem_3d": q_chem_3d,
        "u_x": u_x,
        "u_y": u_y,
        "u_z": u_z,
        "dt_s": dt,
        "steps_executed": n_steps,
        "max_temperature_K": T_max_history_K[-1],
        "predicted_flame_radius_m": r_f_history_m[-1],
        "time_history_s": time_history_s,
        "T_max_history_K": T_max_history_K,
        "r_f_history_m": r_f_history_m,
        "snapshots": snapshots,
    }


if __name__ == "__main__":
    cfg = SimulationInputSI(grid_nodes_per_axis=31, total_time_s=0.4)
    res = run_transient_simulation_3d(cfg, max_steps=100)
    npz_file = export_3d_state_for_ignis(res)
    print("solver_3d.py OK | Residuos:", res["convergence_and_residuals"]["L2_residuals"], "| NPZ:", npz_file)
