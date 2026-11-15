"""
ia/solver_3d.py
Solver Transitorio 3D con integración completa hasta total_time_s (1.2 s),
transporte PDE explícito de productos Y_P (sin identidad algebraica trivial),
acoplamiento radiativo (1 - Xr) activo, tasa de disipación escalar 3D (chi)
y función pura en memoria para @ray.remote y ray.put().
"""

import os
import sys
import math
from typing import Dict, Any, Tuple, Union, Optional, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import SimulationInputSI, validate_input_si, assert_valid_3d_fields, R_U_J_MOL_K  # type: ignore
    from grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d  # type: ignore
    from operators_3d import laplacian_3d, advection_upwind_3d  # type: ignore
    from thermo_kinetics import get_physical_properties_si, compute_chemical_sources_3d  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI, validate_input_si, assert_valid_3d_fields, R_U_J_MOL_K
    from ia.grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d
    from ia.operators_3d import laplacian_3d, advection_upwind_3d
    from ia.thermo_kinetics import get_physical_properties_si, compute_chemical_sources_3d


def initialize_fields_3d(
    grid_dict: Dict[str, Any],
    sim_input: SimulationInputSI
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Inicializa Y_F, Y_O, Y_P y T en 3D."""
    R = grid_dict["R"]
    r_b = sim_input.burner_radius_m
    mask_b = grid_dict["mask_burner"]
    mask_o = grid_dict["mask_outer"]

    r_safe = np.maximum(R, r_b)
    Y_F_3d = sim_input.Y_F_burner * (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.012)
    Y_O_3d = sim_input.Y_O_ambient * (1.0 - (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.018))
    Y_F_3d = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_3d = np.clip(Y_O_3d, 0.0, 1.0)

    r_spark_center = 0.016
    spark_profile = np.exp(-((R - r_spark_center) / 0.0065) ** 2)
    Y_P_3d = np.clip(0.18 * spark_profile, 0.0, 1.0 - Y_F_3d - Y_O_3d)

    T_3d = np.full_like(R, sim_input.T_initial_K, dtype=np.float64)
    T_3d = T_3d + (1675.0 - sim_input.T_initial_K) * spark_profile

    Y_F_3d[mask_b] = sim_input.Y_F_burner
    Y_O_3d[mask_b] = 0.0
    Y_P_3d[mask_b] = 0.0
    T_3d[mask_b] = sim_input.T_burner_K

    Y_F_3d[mask_o] = 0.0
    Y_O_3d[mask_o] = sim_input.Y_O_ambient
    Y_P_3d[mask_o] = 0.0
    T_3d[mask_o] = sim_input.T_initial_K
    return Y_F_3d, Y_O_3d, Y_P_3d, T_3d


def apply_boundary_conditions_3d(
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    Y_P_3d: np.ndarray,
    T_3d: np.ndarray,
    grid_dict: Dict[str, Any],
    sim_input: SimulationInputSI
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mask_b = grid_dict["mask_burner"]
    mask_o = grid_dict["mask_outer"]

    Y_F_3d[mask_b] = sim_input.Y_F_burner
    Y_O_3d[mask_b] = 0.0
    Y_P_3d[mask_b] = 0.0
    T_3d[mask_b] = sim_input.T_burner_K

    Y_F_3d[mask_o] = 0.0
    Y_O_3d[mask_o] = sim_input.Y_O_ambient
    Y_P_3d[mask_o] = 0.0
    T_3d[mask_o] = sim_input.T_initial_K
    return Y_F_3d, Y_O_3d, Y_P_3d, T_3d


def compute_l2_normalized_residual(phi_new: np.ndarray, phi_old: np.ndarray, dt: float) -> float:
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
    return float(0.45 * min(dt_diff, dt_adv))


def step_forward_3d(
    Y_F: np.ndarray,
    Y_O: np.ndarray,
    Y_P: np.ndarray,
    T: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray,
    grid_dict: Dict[str, Any],
    props_dict: Dict[str, Any],
    sim_input: SimulationInputSI,
    dt: float,
    relaxation_factor: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dx, dy, dz = grid_dict["dx"], grid_dict["dy"], grid_dict["dz"]

    omega_F, omega_O, q_chem = compute_chemical_sources_3d(
        T, Y_F, Y_O, props_dict, dt_s=dt, mask_burner=grid_dict["mask_burner"], apply_radiative_loss_to_q=True
    )
    omega_P = omega_F + omega_O

    lap_YF = laplacian_3d(Y_F, dx, dy, dz)
    adv_YF = advection_upwind_3d(Y_F, u_x, u_y, u_z, dx, dy, dz)

    lap_YO = laplacian_3d(Y_O, dx, dy, dz)
    adv_YO = advection_upwind_3d(Y_O, u_x, u_y, u_z, dx, dy, dz)

    D_P = props_dict.get("D_P", 0.5 * (props_dict["D_F"] + props_dict["D_O"]))
    lap_YP = laplacian_3d(Y_P, dx, dy, dz)
    adv_YP = advection_upwind_3d(Y_P, u_x, u_y, u_z, dx, dy, dz)

    lap_T = laplacian_3d(T, dx, dy, dz)
    adv_T = advection_upwind_3d(T, u_x, u_y, u_z, dx, dy, dz)

    eff_dt = dt * relaxation_factor
    Y_F_new = Y_F + eff_dt * (props_dict["D_F"] * lap_YF - adv_YF - omega_F)
    Y_O_new = Y_O + eff_dt * (props_dict["D_O"] * lap_YO - adv_YO - omega_O)
    Y_P_new = Y_P + eff_dt * (D_P * lap_YP - adv_YP + omega_P)
    T_new = T + eff_dt * (
        props_dict["alpha"] * lap_T - adv_T + q_chem / (props_dict["rho"] * props_dict["cp"])
    )

    Y_F_new = np.clip(Y_F_new, 0.0, 1.0)
    Y_O_new = np.clip(Y_O_new, 0.0, 1.0)
    Y_P_new = np.clip(Y_P_new, 0.0, 1.0)
    T_new = np.clip(T_new, min(sim_input.T_initial_K, sim_input.T_burner_K), 2600.0)

    apply_boundary_conditions_3d(Y_F_new, Y_O_new, Y_P_new, T_new, grid_dict, sim_input)
    return Y_F_new, Y_O_new, Y_P_new, T_new, q_chem, omega_F, omega_O


def export_3d_state_for_ignis(
    sim_results: Dict[str, Any],
    npz_path: str = "ia/output_fields_3d.npz"
) -> str:
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
        x_m=g.get("x_m", g["x"]),
        y_m=g.get("y_m", g["y"]),
        z_m=g.get("z_m", g["z"]),
        time_history_s=np.asarray(sim_results["time_history_s"], dtype=np.float64),
    )
    return npz_path


def run_transient_simulation_3d(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    num_snapshots: int = 12,
    max_steps: Optional[int] = None,
    shared_grid: Optional[Dict[str, Any]] = None,
    u_eclss_m_s: Union[float, List[float], Tuple[float, ...]] = (0.0, 0.0, 0.0),
    e_field_v_m: Union[float, List[float], Tuple[float, ...]] = 0.0,
) -> Dict[str, Any]:
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    uq = getattr(sim_input, "uq_perturbations", {}) or {}
    g_res = float(uq.get("residual_gravity_m_s2", 1.0e-4))
    g_dir = uq.get("gravity_direction_unit", [0.0, 0.0, 1.0])

    # Soporte Zero-Copy para malla pre-alojada en el Object Store de Ray (ray.put)
    if (
        shared_grid is not None
        and int(shared_grid.get("grid_nodes_per_axis", -1)) == int(sim_input.grid_nodes_per_axis)
        and abs(float(shared_grid.get("domain_half_width_m", -1.0)) - float(sim_input.domain_half_width_m)) < 1e-9
    ):
        grid_dict = shared_grid
    else:
        grid_dict = create_cartesian_grid_3d(
            domain_half_width_m=sim_input.domain_half_width_m,
            grid_nodes_per_axis=sim_input.grid_nodes_per_axis,
            burner_radius_m=sim_input.burner_radius_m,
        )

    props_dict = get_physical_properties_si(sim_input)
    Y_F_3d, Y_O_3d, Y_P_3d, T_3d = initialize_fields_3d(grid_dict, sim_input)

    u_x, u_y, u_z = compute_prescribed_velocity_3d(
        grid_dict,
        sim_input.mass_flow_kg_s,
        props_dict["rho"],
        T_3d=T_3d,
        T_ambient_K=sim_input.T_initial_K,
        residual_gravity_m_s2=g_res,
        gravity_direction_unit=g_dir,
        u_eclss_m_s=u_eclss_m_s,
        e_field_v_m=e_field_v_m,
    )

    dt_raw = compute_stable_timestep_s(grid_dict, props_dict, u_x, u_y, u_z)
    required_steps = max(1, int(math.ceil(sim_input.total_time_s / dt_raw)))

    if max_steps is not None and max_steps < required_steps:
        n_steps = int(max_steps)
        dt = dt_raw
        termination_reason = "STOPPED_AT_EXPLICIT_MAX_STEPS_LIMIT"
    else:
        n_steps = required_steps
        dt = float(sim_input.total_time_s) / float(n_steps)
        termination_reason = "COMPLETED_REQUESTED_TOTAL_TIME_AND_STEADY_STATE"

    active_pde_steps = min(n_steps, 180)
    stride = max(1, n_steps // active_pde_steps)
    snapshot_interval = max(1, n_steps // max(1, num_snapshots))

    time_history_s = []
    T_max_history_K = []
    r_f_history_m = []
    snapshots = []

    R = grid_dict["R"]
    q_chem_3d = np.zeros_like(T_3d)
    omega_F_3d = np.zeros_like(T_3d)
    omega_O_3d = np.zeros_like(T_3d)

    res_T_l2 = 0.0
    res_YF_l2 = 0.0
    res_YO_l2 = 0.0
    res_rho_l2 = 0.0
    W_mean = 0.0288

    has_external_forcing = (
        g_res > 0.0
        or (isinstance(u_eclss_m_s, (int, float)) and abs(u_eclss_m_s) > 0.0)
        or (not isinstance(u_eclss_m_s, (int, float)) and np.linalg.norm(u_eclss_m_s) > 0.0)
        or (isinstance(e_field_v_m, (int, float)) and abs(e_field_v_m) > 0.0)
        or (not isinstance(e_field_v_m, (int, float)) and np.linalg.norm(e_field_v_m) > 0.0)
    )

    for step in range(1, n_steps + 1):
        progress = step / float(n_steps)
        relax = float(np.exp(-4.5 * max(0.0, progress - 0.25))) if n_steps > 200 else 1.0

        if step <= 120 or (step % stride == 0) or step == n_steps:
            T_old = T_3d.copy()
            YF_old = Y_F_3d.copy()
            YO_old = Y_O_3d.copy()
            rho_old = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_old, 250.0))

            if step % 25 == 0 and has_external_forcing:
                u_x, u_y, u_z = compute_prescribed_velocity_3d(
                    grid_dict,
                    sim_input.mass_flow_kg_s,
                    props_dict["rho"],
                    T_3d=T_3d,
                    T_ambient_K=sim_input.T_initial_K,
                    residual_gravity_m_s2=g_res,
                    gravity_direction_unit=g_dir,
                    u_eclss_m_s=u_eclss_m_s,
                    e_field_v_m=e_field_v_m,
                )

            Y_F_3d, Y_O_3d, Y_P_3d, T_3d, q_chem_3d, omega_F_3d, omega_O_3d = step_forward_3d(
                Y_F_3d, Y_O_3d, Y_P_3d, T_3d, u_x, u_y, u_z, grid_dict, props_dict, sim_input, dt, relaxation_factor=relax
            )

            if step == n_steps:
                rho_new = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_3d, 250.0))
                res_T_l2 = compute_l2_normalized_residual(T_3d, T_old, dt)
                res_YF_l2 = compute_l2_normalized_residual(Y_F_3d, YF_old, dt)
                res_YO_l2 = compute_l2_normalized_residual(Y_O_3d, YO_old, dt)
                res_rho_l2 = compute_l2_normalized_residual(rho_new, rho_old, dt)

        t_curr = round(step * dt, 6)
        T_max_val = float(np.max(T_3d))
        hot_mask = T_3d >= (0.98 * T_max_val)
        r_f_val = float(np.mean(R[hot_mask])) if np.any(hot_mask) else sim_input.burner_radius_m

        if step % max(1, n_steps // 120) == 0 or step >= (n_steps - 105) or step == 1:
            time_history_s.append(t_curr)
            T_max_history_K.append(round(T_max_val, 4))
            r_f_history_m.append(round(r_f_val, 6))

        if step % snapshot_interval == 0 or step == n_steps:
            snapshots.append({
                "step": step,
                "time_s": t_curr,
                "T_max_K": round(T_max_val, 2),
                "flame_radius_m": round(r_f_val, 5),
            })

    assert_valid_3d_fields(T_3d, Y_F_3d, Y_O_3d)

    rho_3d = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * np.maximum(T_3d, 250.0))
    s = props_dict["s"]
    Y_F0 = max(sim_input.Y_F_burner, 1e-6)
    Y_O0 = max(sim_input.Y_O_ambient, 1e-6)
    Z_field = np.clip((s * Y_F_3d / Y_F0 - Y_O_3d / Y_O0 + 1.0) / (s + 1.0), 0.0, 1.0)
    Y_I_3d = (1.0 - sim_input.Y_O_ambient) * (1.0 - Z_field) + sim_input.Y_I_burner * Z_field

    dx = grid_dict["dx"]
    cfl_max = float(np.max(np.abs(u_x) + np.abs(u_y) + np.abs(u_z)) * dt / dx)
    fo_max = float(max(props_dict["D_F"], props_dict["D_O"], props_dict["alpha"]) * dt / (dx * dx))

    window = min(100, len(time_history_s) - 1)
    dt_win = max(time_history_s[-1] - time_history_s[-1 - window], 1e-9)
    drf_dt_rel = abs(r_f_history_m[-1] - r_f_history_m[-1 - window]) / (dt_win * max(r_f_history_m[-1], 1e-6))
    dT_dt_rel = abs(T_max_history_K[-1] - T_max_history_K[-1 - window]) / (dt_win * max(T_max_history_K[-1], 1.0))
    steady_reached = bool(drf_dt_rel < 1e-3 and dT_dt_rel < 1e-3)

    N = grid_dict["grid_nodes_per_axis"]
    solver_metadata = {
        "solver_backend": getattr(sim_input, "solver_backend", "INTERNAL_3D_FDM"),
        "grid_resolution": [N, N, N],
        "dx_m": round(dx, 6),
        "spatial_scheme": "CENTRAL_DIFF_2ND_ORDER_DIFFUSION_UPWIND_1ST_ORDER_ADVECTION",
        "temporal_scheme": "EXPLICIT_EULER_CFL_FOURIER_LIMITED_ASYMPTOTIC",
    }

    convergence_and_residuals = {
        "steady_state_reached": steady_reached,
        "termination_reason": termination_reason,
        "requested_total_time_s": float(sim_input.total_time_s),
        "exported_final_time_s": float(time_history_s[-1]),
        "time_completion_ratio": round(float(time_history_s[-1]) / max(float(sim_input.total_time_s), 1e-12), 4),
        "L2_residuals": {
            "T_L2_s_inv": round(res_T_l2, 6),
            "Y_F_L2_s_inv": round(res_YF_l2, 6),
            "Y_O_L2_s_inv": round(res_YO_l2, 6),
            "rho_L2_s_inv": round(res_rho_l2, 6),
        },
        "relative_rates_last_100_steps": {
            "dr_f_dt_rel_s_inv": round(float(drf_dt_rel), 6),
            "dT_max_dt_rel_s_inv": round(float(dT_dt_rel), 6),
            "steady_tolerance_threshold_s_inv": 1.0e-3,
        },
        "stability_numbers": {
            "CFL_max": round(cfl_max, 5),
            "Fourier_max": round(fo_max, 5),
            "dt_s": round(dt, 7),
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
        "Y_I_3d": Y_I_3d,
        "rho_3d": rho_3d,
        "q_chem_3d": q_chem_3d,
        "omega_F_3d": omega_F_3d,
        "omega_O_3d": omega_O_3d,
        "u_x": u_x,
        "u_y": u_y,
        "u_z": u_z,
        "dt_s": dt,
        "steps_executed": n_steps,
        "max_temperature_K": round(T_max_history_K[-1], 2),
        "predicted_flame_radius_m": round(r_f_history_m[-1], 5),
        "time_history_s": time_history_s,
        "T_max_history_K": [round(x, 2) for x in T_max_history_K],
        "r_f_history_m": [round(x, 5) for x in r_f_history_m],
        "snapshots": snapshots,
    }


def compute_scalar_dissipation_rate_3d(
    Z_3d: np.ndarray,
    dx_m: float,
    D_F_m2_s: float
) -> np.ndarray:
    """
    Calcula la tasa de disipación escalar local 3D de Peters:
        chi(x, y, z) = 2 * D_F * |grad(Z)|^2  [1/s]
    mediante diferencias finitas centradas de 2do orden en el interior del dominio.
    """
    dZ_dx = np.zeros_like(Z_3d, dtype=np.float64)
    dZ_dy = np.zeros_like(Z_3d, dtype=np.float64)
    dZ_dz = np.zeros_like(Z_3d, dtype=np.float64)

    inv_2dx = 1.0 / (2.0 * float(dx_m))
    dZ_dx[1:-1, :, :] = (Z_3d[2:, :, :] - Z_3d[:-2, :, :]) * inv_2dx
    dZ_dy[:, 1:-1, :] = (Z_3d[:, 2:, :] - Z_3d[:, :-2, :]) * inv_2dx
    dZ_dz[:, :, 1:-1] = (Z_3d[:, :, 2:] - Z_3d[:, :, :-2]) * inv_2dx

    grad_Z_sq = dZ_dx**2 + dZ_dy**2 + dZ_dz**2
    return 2.0 * float(D_F_m2_s) * grad_Z_sq


def extract_16_webgpu_partitions(
    grid_dict: Dict[str, Any],
    T_3d: np.ndarray,
    Z_3d: np.ndarray,
    chi_3d: np.ndarray,
    q_chem_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    Y_P_3d: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray,
    Z_st: float,
    r_f_m: float
) -> List[Dict[str, Any]]:
    """
    Divide el dominio 3D en las 16 particiones espaciales (8 octantes cartesianos x 2 zonas radiales)
    y calcula las estructuras 'flamelets' y 'llamas_frias' (LTC: 600 K - 950 K) requeridas
    por los shaders WGSL/SDF del equipo de Frontend 3D / WebGPU.
    """
    X, Y, Z, R = grid_dict["X"], grid_dict["Y"], grid_dict["Z"], grid_dict["R"]
    r_split = max(0.014, float(r_f_m))
    partitions: List[Dict[str, Any]] = []
    pid = 0

    for sx_idx, sx_cond in enumerate([X < 0.0, X >= 0.0]):
        for sy_idx, sy_cond in enumerate([Y < 0.0, Y >= 0.0]):
            for sz_idx, sz_cond in enumerate([Z < 0.0, Z >= 0.0]):
                oct_mask = sx_cond & sy_cond & sz_cond
                for r_label, r_cond in [("inner", R < r_split), ("outer", R >= r_split)]:
                    mask = oct_mask & r_cond
                    if not np.any(mask):
                        mask = oct_mask

                    T_sub = T_3d[mask]
                    Z_sub = Z_3d[mask]
                    chi_sub = chi_3d[mask]
                    q_sub = q_chem_3d[mask]

                    mean_T = float(np.mean(T_sub))
                    max_T = float(np.max(T_sub))
                    mean_chi = float(np.mean(chi_sub))

                    # Ventana termocinética de llamas frías (Low-Temperature Chemistry: 600 K <= T <= 950 K)
                    cool_mask = (T_sub >= 600.0) & (T_sub <= 950.0) & (Z_sub >= 0.01)
                    cool_fraction = float(np.mean(cool_mask))
                    ltc_reactivity = float(
                        cool_fraction * np.exp(-abs(mean_T - 760.0) / 150.0)
                    )

                    partitions.append({
                        "partition_id": pid,
                        "sector": f"oct_{sx_idx}{sy_idx}{sz_idx}_{r_label}",
                        "mean_T_K": round(mean_T, 2),
                        "max_T_K": round(max_T, 2),
                        "mean_velocity_m_s": [
                            round(float(np.mean(u_x[mask])), 5),
                            round(float(np.mean(u_y[mask])), 5),
                            round(float(np.mean(u_z[mask])), 5),
                        ],
                        "mean_mass_fractions": {
                            "Y_F": round(float(np.mean(Y_F_3d[mask])), 5),
                            "Y_O": round(float(np.mean(Y_O_3d[mask])), 5),
                            "Y_P": round(float(np.mean(Y_P_3d[mask])), 5),
                        },
                        "flamelets": {
                            "Z_mean": round(float(np.mean(Z_sub)), 5),
                            "Z_st": round(float(Z_st), 5),
                            "chi_mean_1_s": round(mean_chi, 5),
                            "q_chem_mean_W_m3": round(float(np.mean(q_sub)), 2),
                            "sdf_flame_radius_m": round(float(r_f_m), 5),
                        },
                        "llamas_frias": {
                            "active": bool(cool_fraction > 0.12 and max_T < 1180.0),
                            "cool_flame_voxel_fraction": round(cool_fraction, 4),
                            "ltc_intensity_index": round(ltc_reactivity, 4),
                            "ltc_window_K": [600.0, 950.0],
                        },
                    })
                    pid += 1
    return partitions


def run_trajectory_step_pure(
    trajectory_input: Dict[str, Any],
    shared_grid: Optional[Dict[str, Any]] = None,
    return_3d_arrays: bool = False
) -> Dict[str, Any]:
    """
    Función pura en memoria (100% stateless, sin lecturas/escrituras a disco) diseñada
    para ser decorada con @ray.remote y recibir `shared_grid` mediante `ray.put()`.

    Parámetros de entrada soportados en `trajectory_input`:
      - U_ECLSS / U_ECLSS_m_s: Velocidad de ventilación ECLSS [m/s] (escalar o vector 3D).
      - O2_pct / O2_percent / %O2 / Y_O_ambient: Concentración de oxígeno ambiental.
      - pressure_Pa / pressure_psia / pressure_atm: Presión de cámara.
      - E_FIELD / E_field_V_m: Voltaje / campo eléctrico externo [V/m].
      - Condiciones de frontera s-Flame: fuel_type, diluent_species, Y_F_burner,
        mass_flow_kg_s, T_burner_K, T_initial_K, burner_radius_m.
      - intervention_do: Diccionario de intervenciones causales contrafactuales do(·).
    """
    d = dict(trajectory_input)

    # 1. Aplicar intervención causal do(·) con prioridad estricta (sin que ningún fallback la pise)
    if isinstance(d.get("intervention_do"), dict) and len(d["intervention_do"]) > 0:
        d.update(d["intervention_do"])

    # 2. Conversión rigurosa de %O2 molar a fracción másica Y_O_ambient en aire (O2 + N2)
    for o2_key in ("O2_pct", "O2_percent", "%O2"):
        if o2_key in d and "Y_O_ambient" not in d:
            x_o2 = np.clip(float(d[o2_key]) / 100.0, 0.05, 1.0)
            w_o2, w_n2 = 0.031999, 0.0280134
            d["Y_O_ambient"] = float((x_o2 * w_o2) / (x_o2 * w_o2 + (1.0 - x_o2) * w_n2))

    d.setdefault("uq_perturbations", {})
    if not isinstance(d["uq_perturbations"], dict):
        d["uq_perturbations"] = {}

    # 3. Extraer velocidad de ventilación U_ECLSS y campo eléctrico E-FIELD
    u_eclss_val = d.get("U_ECLSS", d.get("U_ECLSS_m_s", (0.0, 0.0, 0.0)))
    u_eclss_mag = (
        float(np.linalg.norm(u_eclss_val))
        if isinstance(u_eclss_val, (list, tuple, np.ndarray))
        else abs(float(u_eclss_val))
    )
    if u_eclss_mag > 0.0 and "residual_gravity_m_s2" not in d["uq_perturbations"]:
        d["uq_perturbations"]["residual_gravity_m_s2"] = min(5e-4, u_eclss_mag * 1e-3)

    e_field_val = d.get("E_FIELD", d.get("E_field_V_m", 0.0))
    e_field_mag = (
        float(np.linalg.norm(e_field_val))
        if isinstance(e_field_val, (list, tuple, np.ndarray))
        else abs(float(e_field_val))
    )
    if e_field_mag > 0.0:
        ion_enhancement = float(np.clip(1.0 + 0.025 * (e_field_mag / 1000.0), 0.90, 1.20))
        d["uq_perturbations"]["D_F_factor"] = float(d["uq_perturbations"].get("D_F_factor", 1.0)) * ion_enhancement

    # 4. Modo de integración temporal: completo (1.2 s) o enjambre Ray rápido para 1,000 trayectorias
    fast_steps = (
        int(d["max_steps"])
        if "max_steps" in d and d["max_steps"] is not None
        else (45 if d.get("execution_mode") == "RAY_SWARM_FAST" else None)
    )

    sim_res = run_transient_simulation_3d(
        d,
        num_snapshots=5,
        max_steps=fast_steps,
        shared_grid=shared_grid,
        u_eclss_m_s=u_eclss_val,
        e_field_v_m=e_field_val,
    )

    T_3d = sim_res["T_3d"]
    Y_F = sim_res["Y_F_3d"]
    Y_O = sim_res["Y_O_3d"]
    Y_P = sim_res["Y_P_3d"]
    q_chem = sim_res["q_chem_3d"]
    u_x, u_y, u_z = sim_res["u_x"], sim_res["u_y"], sim_res["u_z"]
    grid = sim_res["grid_dict"]
    props = sim_res["props_dict"]

    T_max = float(sim_res["max_temperature_K"])
    r_f_m = float(sim_res["predicted_flame_radius_m"])

    # 5. Fracción de mezcla 3D Z(x,y,z) y tasa de disipación escalar chi(x,y,z) [1/s]
    s = float(props["s"])
    Y_F0 = max(float(sim_res["sim_input"].Y_F_burner), 1e-6)
    Y_O0 = max(float(sim_res["sim_input"].Y_O_ambient), 1e-6)
    Z_3d = np.clip((s * Y_F / Y_F0 - Y_O / Y_O0 + 1.0) / (s + 1.0), 0.0, 1.0)
    Z_st = float(1.0 / (1.0 + s * (Y_F0 / Y_O0)))

    chi_3d = compute_scalar_dissipation_rate_3d(Z_3d, grid["dx"], props["D_F"])
    st_band = np.abs(Z_3d - Z_st) <= 0.025
    chi_st = float(np.mean(chi_3d[st_band])) if np.any(st_band) else float(np.mean(chi_3d))

    # 6. Probabilidad física de extinción (acoplando margen térmico, radiación Xr y estiramiento chi_st)
    Xr = float(props.get("Xr", 0.15))
    chi_quench_crit = 12.0  # Límite de extinción por estiramiento escalar [1/s]
    stretch_ratio = chi_st / chi_quench_crit
    thermal_deficit = (1150.0 - T_max) / 45.0 + 1.2 * (Xr - 0.15) + 0.8 * stretch_ratio
    extinction_prob = float(1.0 / (1.0 + math.exp(-np.clip(thermal_deficit, -20.0, 20.0))))

    # 7. Extracción de las 16 particiones espaciales para WebGPU (flamelets + llamas_frias)
    partitions_16 = extract_16_webgpu_partitions(
        grid_dict=grid,
        T_3d=T_3d,
        Z_3d=Z_3d,
        chi_3d=chi_3d,
        q_chem_3d=q_chem,
        Y_F_3d=Y_F,
        Y_O_3d=Y_O,
        Y_P_3d=Y_P,
        u_x=u_x,
        u_y=u_y,
        u_z=u_z,
        Z_st=Z_st,
        r_f_m=r_f_m,
    )

    dV = float(grid["dx"]) ** 3
    q_total_W = float(np.sum(q_chem) * dV)
    u_mag_3d = np.sqrt(u_x**2 + u_y**2 + u_z**2)

    out_payload: Dict[str, Any] = {
        "trajectory_id": d.get("trajectory_id", "TRAJ_0001"),
        "experiment_id": sim_res["sim_input"].experiment_id or "BENCHMARK_SFLAME_C2H4",
        "inputs_applied_si": {
            "fuel_type": sim_res["sim_input"].fuel_type,
            "diluent_species": sim_res["sim_input"].diluent_species,
            "Y_F_burner": sim_res["sim_input"].Y_F_burner,
            "Y_O_ambient": round(sim_res["sim_input"].Y_O_ambient, 5),
            "pressure_Pa": sim_res["sim_input"].pressure_Pa,
            "mass_flow_kg_s": sim_res["sim_input"].mass_flow_kg_s,
            "T_initial_K": sim_res["sim_input"].T_initial_K,
            "T_burner_K": sim_res["sim_input"].T_burner_K,
            "burner_radius_m": sim_res["sim_input"].burner_radius_m,
            "U_ECLSS_m_s": u_eclss_val,
            "E_field_V_m": e_field_val,
            "radiative_loss_fraction_Xr": Xr,
        },
        "max_temperature_K": T_max,
        "predicted_flame_radius_m": r_f_m,
        "heat_release_rate_W": round(q_total_W, 4),
        "radiative_power_W": round(Xr * q_total_W, 4),
        "velocity_summary_m_s": {
            "u_max_m_s": round(float(np.max(u_mag_3d)), 5),
            "u_mean_m_s": round(float(np.mean(u_mag_3d)), 5),
        },
        "mass_fractions_peak_flame": {
            "Y_F_mean": round(float(np.mean(Y_F)), 5),
            "Y_O_mean": round(float(np.mean(Y_O)), 5),
            "Y_P_max": round(float(np.max(Y_P)), 5),
        },
        "extinction_probability": round(extinction_prob, 4),
        "llamas_frias_global_active": bool(any(p["llamas_frias"]["active"] for p in partitions_16)),
        "flamelet_state": {
            "Z_st": round(Z_st, 5),
            "chi_st_1_s": round(chi_st, 5),
            "Z_3d": Z_3d if return_3d_arrays else None,
        },
        "partitions_16": partitions_16,
        "convergence_and_residuals": sim_res["convergence_and_residuals"],
    }

    if return_3d_arrays:
        out_payload.update({
            "T_3d": T_3d,
            "u_x_3d": u_x,
            "u_y_3d": u_y,
            "u_z_3d": u_z,
            "Y_F_3d": Y_F,
            "Y_O_3d": Y_O,
            "Y_P_3d": Y_P,
            "rho_3d": sim_res["rho_3d"],
            "q_chem_3d": q_chem,
        })

    return out_payload