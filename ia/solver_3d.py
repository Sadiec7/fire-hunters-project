"""
ia/solver_3d.py
Motor de Simulación Transitoria 3D de Especies y Energía - Bloques 5 y 6.
"""

import os
import sys
from typing import Dict, Any, Tuple, Union
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contract_si import SimulationInputSI, validate_input_si, assert_valid_3d_fields, R_U_J_MOL_K
from grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d
from operators_3d import laplacian_3d, advection_upwind_3d

# Importación compatible con los módulos de Ángel (con fallback autónomo integrado)
try:
    from thermo_kinetics import get_physical_properties_si, compute_chemical_sources_3d
except ImportError:
    FUEL_DB_FALLBACK = {
        "C2H4": {"W_F": 0.02805, "s": 3.422, "delta_Hc": 4.716e7, "Ea": 1.255e5, "A": 1.2e9, "D_F0": 3.8e-5},
        "CH4":  {"W_F": 0.01604, "s": 3.989, "delta_Hc": 5.002e7, "Ea": 1.255e5, "A": 8.5e8, "D_F0": 4.5e-5},
        "H2":   {"W_F": 0.002016, "s": 7.937, "delta_Hc": 1.199e8, "Ea": 8.314e4, "A": 2.5e9, "D_F0": 1.4e-4},
    }

    def get_physical_properties_si(sim_input: SimulationInputSI) -> Dict[str, Any]:
        f = FUEL_DB_FALLBACK[sim_input.fuel_type]
        p_scale = 101325.0 / sim_input.pressure_Pa
        T_ref = 950.0
        W_mean = 0.0288
        rho = (sim_input.pressure_Pa * W_mean) / (R_U_J_MOL_K * T_ref)
        D_F = f["D_F0"] * p_scale * ((T_ref / 300.0) ** 1.75)
        D_O = 4.2e-5 * p_scale * ((T_ref / 300.0) ** 1.75)
        alpha = 4.5e-5 * p_scale * ((T_ref / 300.0) ** 1.75)
        return {
            "rho": float(rho),
            "cp": 1150.0,
            "D_F": float(D_F),
            "D_O": float(D_O),
            "alpha": float(alpha),
            "s": f["s"],
            "delta_Hc": f["delta_Hc"],
            "A": f["A"],
            "Ea": f["Ea"],
            "W_F": f["W_F"],
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

        Y_F_clean = np.clip(Y_F_3d, 0.0, 1.0)
        Y_O_clean = np.clip(Y_O_3d, 0.0, 1.0)
        T_safe = np.maximum(T_3d, 250.0)

        C_F = rho * Y_F_clean
        C_O = rho * Y_O_clean

        # Activación térmica suave bajo 550 K para evitar ignición ambiental espuria
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
        # Fracción térmica efectiva en llama de difusión con pérdidas radiativas equivalentes
        q_chem = 0.42 * rho * omega_F * delta_Hc
        return omega_F, omega_O, q_chem

try:
    from initial_boundary import initialize_fields_3d, apply_boundary_conditions_3d
except ImportError:
    def initialize_fields_3d(
        grid_dict: Dict[str, Any],
        sim_input: SimulationInputSI
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        R = grid_dict["R"]
        r_b = sim_input.burner_radius_m
        mask_b = grid_dict["mask_burner"]
        mask_o = grid_dict["mask_outer"]

        # Semilla radial suave basada en difusión esférica para converger rápido en 20h
        r_safe = np.maximum(R, r_b)
        Y_F_3d = sim_input.Y_F_burner * (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.012)
        Y_O_3d = sim_input.Y_O_ambient * (1.0 - (r_b / r_safe) * np.exp(-(r_safe - r_b) / 0.018))
        Y_F_3d = np.clip(Y_F_3d, 0.0, 1.0)
        Y_O_3d = np.clip(Y_O_3d, 0.0, 1.0)

        T_3d = np.full_like(R, sim_input.T_initial_K, dtype=np.float64)
        # Chispa térmica esférica inicial de ignición
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


def compute_stable_timestep_s(
    grid_dict: Dict[str, Any],
    props_dict: Dict[str, Any],
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray
) -> float:
    """Calcula el paso de tiempo explícito estable (Fourier + CFL en 3D) [s]."""
    dx = grid_dict["dx"]
    D_max = max(props_dict["D_F"], props_dict["D_O"], props_dict["alpha"])
    dt_diff = (dx * dx) / (6.0 * D_max + 1e-15)

    u_sum_max = float(np.max(np.abs(u_x) + np.abs(u_y) + np.abs(u_z)))
    dt_adv = dx / (u_sum_max + 1e-12)

    return float(0.4 * min(dt_diff, dt_adv))


def compute_stable_dt(grid_dict: Dict[str, Any], props_dict: Dict[str, Any], u_max: float) -> float:
    """Alias compatible con el Bloque 5 del manual operativo."""
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
    """Avanza un paso temporal dt las ecuaciones 3D de Y_F, Y_O y T."""
    dx, dy, dz = grid_dict["dx"], grid_dict["dy"], grid_dict["dz"]

    try:
        omega_F, omega_O, q_chem = compute_chemical_sources_3d(
            T, Y_F, Y_O, props_dict, dt_s=dt
        )
        omega_F = np.where(grid_dict["mask_burner"], 0.0, omega_F)
        omega_O = np.where(grid_dict["mask_burner"], 0.0, omega_O)
        q_chem = np.where(grid_dict["mask_burner"], 0.0, q_chem)
    except TypeError:
        omega_F, omega_O, q_chem = compute_chemical_sources_3d(
            T, Y_F, Y_O, props_dict, grid_dict["mask_burner"]
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


def run_transient_simulation_3d(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    num_snapshots: int = 10,
    max_steps: int = 250
) -> Dict[str, Any]:
    """Ejecuta la simulación 3D transitoria y devuelve campos 3D e historiales."""
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    grid_dict = create_cartesian_grid_3d(
        domain_half_width_m=sim_input.domain_half_width_m,
        grid_nodes_per_axis=sim_input.grid_nodes_per_axis,
        burner_radius_m=sim_input.burner_radius_m,
    )
    props_dict = get_physical_properties_si(sim_input)
    u_x, u_y, u_z = compute_prescribed_velocity_3d(
        grid_dict, sim_input.mass_flow_kg_s, props_dict["rho"]
    )
    Y_F_3d, Y_O_3d, T_3d = initialize_fields_3d(grid_dict, sim_input)

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

    for step in range(1, n_steps + 1):
        Y_F_3d, Y_O_3d, T_3d, q_chem_3d = step_forward_3d(
            Y_F_3d, Y_O_3d, T_3d, u_x, u_y, u_z, grid_dict, props_dict, sim_input, dt
        )
        t_curr += dt

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

    return {
        "sim_input": sim_input,
        "grid_dict": grid_dict,
        "props_dict": props_dict,
        "T_3d": T_3d,
        "Y_F_3d": Y_F_3d,
        "Y_O_3d": Y_O_3d,
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
    cfg = SimulationInputSI(grid_nodes_per_axis=31, total_time_s=0.5)
    res = run_transient_simulation_3d(cfg, max_steps=120)
    print(f"Solver 3D completado | T_max = {res['max_temperature_K']:.1f} K | r_f = {res['predicted_flame_radius_m']:.4f} m")