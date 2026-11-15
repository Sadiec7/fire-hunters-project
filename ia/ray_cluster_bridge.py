"""
ia/ray_cluster_bridge.py
Interfaz de Funciones Puras en Memoria para Ray (@ray.remote / ray.put) y Docker (Requisitos de Emma).
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import validate_input_si  # type: ignore
    from solver_3d import run_transient_simulation_3d  # type: ignore
    from visualizer_3d import extract_spherical_shell_profiles  # type: ignore
    from domain_query import compute_bayesian_bridge_metrics  # type: ignore
except ImportError:
    from ia.contract_si import validate_input_si
    from ia.solver_3d import run_transient_simulation_3d
    from ia.visualizer_3d import extract_spherical_shell_profiles
    from ia.domain_query import compute_bayesian_bridge_metrics

try:
    import ray  # type: ignore
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


def evaluate_sflame_trajectory_in_memory(trajectory_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función 100% pura en memoria (Cero I/O a disco) para ejecución distribuida con @ray.remote.
    """
    mapped = dict(trajectory_params)

    if "O2_pct" in mapped and "Y_O_ambient" not in mapped:
        mapped["Y_O_ambient"] = float(mapped["O2_pct"]) / 100.0
    if "Y_O2_ambient" in mapped and "Y_O_ambient" not in mapped:
        mapped["Y_O_ambient"] = float(mapped["Y_O2_ambient"])

    uq = dict(mapped.get("uq_perturbations", {}))
    if "U_ECLSS_m_s" in mapped or "U_ECLSS" in mapped:
        u_eclss = float(mapped.get("U_ECLSS_m_s", mapped.get("U_ECLSS", 0.0)))
        uq["residual_gravity_m_s2"] = min(5.0e-4, uq.get("residual_gravity_m_s2", 1.0e-4) + 0.002 * abs(u_eclss))
    mapped["uq_perturbations"] = uq

    sim_input = validate_input_si(mapped)
    max_steps = trajectory_params.get("max_steps", None)
    sim_results = run_transient_simulation_3d(sim_input=sim_input, max_steps=max_steps)

    grid_dict = sim_results["grid_dict"]
    props = sim_results["props_dict"]
    T_3d = sim_results["T_3d"]
    Y_F_3d = sim_results["Y_F_3d"]
    Y_O_3d = sim_results["Y_O_3d"]
    Y_P_3d = sim_results["Y_P_3d"]
    q_chem_3d = sim_results["q_chem_3d"]

    shells = extract_spherical_shell_profiles(grid_dict, T_3d, Y_F_3d, Y_O_3d, q_chem_3d, Y_P_3d)
    dV = float(grid_dict["dx"] ** 3)
    q_total_W = float(np.sum(q_chem_3d) * dV)
    bayesian = compute_bayesian_bridge_metrics(sim_input, sim_results["max_temperature_K"], q_total_W)

    T_max = float(sim_results["max_temperature_K"])
    T_th = float(bayesian["T_extinction_threshold_ref_K"])
    p_ext = float(1.0 / (1.0 + np.exp((T_max - (T_th + 330.0)) / 45.0)))

    s = float(props["s"])
    Y_F0 = max(sim_input.Y_F_burner, 1e-6)
    Y_O0 = max(sim_input.Y_O_ambient, 1e-6)
    Z_st = 1.0 / (1.0 + (s * Y_F0) / Y_O0)

    r_arr = np.asarray(shells["r_shells_m"], dtype=np.float64)
    YF_r = np.asarray(shells["Y_F_mean"], dtype=np.float64)
    YO_r = np.asarray(shells["Y_O_mean"], dtype=np.float64)
    Z_r = np.clip(((s * YF_r / Y_F0) - (YO_r / Y_O0) + 1.0) / (s + 1.0), 0.0, 1.0)
    dZ_dr = np.gradient(Z_r, r_arr)
    chi_r = 2.0 * float(props["D_F"]) * (dZ_dr ** 2)

    return {
        "trajectory_id": str(trajectory_params.get("trajectory_id", "RAY_TRAJ_001")),
        "in_memory_only": True,
        "scalars": {
            "T_max_K": round(T_max, 2),
            "flame_radius_m": sim_results["predicted_flame_radius_m"],
            "extinction_probability": round(p_ext, 4),
            "thermal_margin_K": bayesian["thermal_margin_K"],
            "damkohler_number": bayesian["damkohler_number"],
            "heat_release_rate_W": bayesian["heat_release_rate_W"],
            "radiative_power_W": bayesian["radiative_power_W"],
            "steady_state_reached": sim_results["convergence_and_residuals"]["steady_state_reached"],
        },
        "flamelet_1d": {
            "r_shells_m": r_arr,
            "Z_mixture_fraction": Z_r,
            "Z_stoichiometric": float(Z_st),
            "T_flamelet_K": np.asarray(shells["T_mean_K"], dtype=np.float64),
            "Y_F_flamelet": YF_r,
            "Y_O2_flamelet": YO_r,
            "Y_P_flamelet": np.asarray(shells["Y_P_mean"], dtype=np.float64),
            "chi_scalar_dissipation_1_s": chi_r,
        },
        "tensors_3d": {
            "T_3d": T_3d,
            "Y_F_3d": Y_F_3d,
            "Y_O2_3d": Y_O_3d,
            "Y_P_3d": Y_P_3d,
            "u_x_3d": sim_results["u_x"],
            "u_y_3d": sim_results["u_y"],
            "u_z_3d": sim_results["u_z"],
            "q_chem_3d": q_chem_3d,
        },
        "convergence_and_residuals": sim_results["convergence_and_residuals"],
    }


if RAY_AVAILABLE:
    @ray.remote
    def ray_remote_sflame_worker(trajectory_params: Dict[str, Any]) -> Dict[str, Any]:
        return evaluate_sflame_trajectory_in_memory(trajectory_params)


def run_batch_trajectories_ray(trajectories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if RAY_AVAILABLE and ray.is_initialized():
        futures = [ray_remote_sflame_worker.remote(t) for t in trajectories]
        return ray.get(futures)
    return [evaluate_sflame_trajectory_in_memory(t) for t in trajectories]


if __name__ == "__main__":
    sample = {"trajectory_id": "TEST_EMMA_01", "fuel_type": "C2H4", "O2_pct": 21.0, "U_ECLSS_m_s": 0.02, "max_steps": 60}
    out = evaluate_sflame_trajectory_in_memory(sample)
    print("ray_cluster_bridge.py OK | Escalar:", out["scalars"])