"""
ia/ray_cluster_bridge.py
Módulo de Integración Distribuida para los 3 Nodos Docker y el Clúster Ray (4 Workers).
Cumple con el Punto 1 solicitado por Emmanuel:
  1. Funciones puras en memoria envueltas con @ray.remote y pre-alojamiento Zero-Copy con ray.put().
  2. Ejecución masiva de trayectorias (ej. las 1,000 trayectorias de la demo de 2 minutos).
  3. Contrato exacto de entrada/salida compatible con Supabase (resultados_inferencia_ray),
     caché autónoma SQLite (spacecraft-node) y shaders WGSL/SDF de Frontend 3D / WebGPU.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from grid_3d import create_cartesian_grid_3d  # type: ignore
    from solver_3d import run_trajectory_step_pure  # type: ignore
except ImportError:
    from ia.grid_3d import create_cartesian_grid_3d
    from ia.solver_3d import run_trajectory_step_pure

try:
    import ray  # type: ignore
    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False


if RAY_AVAILABLE and ray is not None:
    @ray.remote(num_cpus=1)
    def ray_simulate_trajectory_worker(
        trajectory_input: Dict[str, Any],
        shared_grid: Dict[str, Any],
        return_3d_arrays: bool = False
    ) -> Dict[str, Any]:
        return run_trajectory_step_pure(
            trajectory_input=trajectory_input,
            shared_grid=shared_grid,
            return_3d_arrays=return_3d_arrays,
        )


def put_shared_grid_in_ray_store(
    domain_half_width_m: float = 0.035,
    grid_nodes_per_axis: int = 31,
    burner_radius_m: float = 0.00318
) -> Any:
    grid_dict = create_cartesian_grid_3d(
        domain_half_width_m=domain_half_width_m,
        grid_nodes_per_axis=grid_nodes_per_axis,
        burner_radius_m=burner_radius_m,
    )
    if RAY_AVAILABLE and ray is not None and ray.is_initialized():
        return ray.put(grid_dict)
    return grid_dict


def generate_trajectory_swarm_inputs(
    n_trajectories: int = 1000,
    base_fuel: str = "C2H4",
    seed: int = 42,
    intervention_do: Optional[Dict[str, Any]] = None,
    grid_nodes_per_axis: int = 25
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    batch: List[Dict[str, Any]] = []

    for i in range(n_trajectories):
        o2_pct = float(rng.uniform(17.5, 34.0))
        pressure_Pa = float(rng.uniform(56500.0, 102000.0))
        u_eclss = float(rng.uniform(0.0, 0.08))
        e_field = float(rng.uniform(0.0, 2500.0))
        mdot = float(rng.uniform(1.2e-6, 3.8e-6))
        xr = float(rng.uniform(0.10, 0.52))

        traj = {
            "trajectory_id": f"TRAJ_{i + 1:04d}",
            "experiment_id": "BENCHMARK_SFLAME_C2H4",
            "execution_mode": "RAY_SWARM_FAST",
            "fuel_type": base_fuel,
            "diluent_species": "N2",
            "Y_F_burner": 1.0,
            "O2_pct": round(o2_pct, 3),
            "pressure_Pa": round(pressure_Pa, 1),
            "T_initial_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": float(f"{mdot:.4e}"),
            "burner_radius_m": 0.00318,
            "domain_half_width_m": 0.035,
            "grid_nodes_per_axis": int(grid_nodes_per_axis),
            "total_time_s": 1.2,
            "U_ECLSS": round(u_eclss, 5),
            "E_FIELD": round(e_field, 2),
            "uq_perturbations": {
                "A_preexp_factor": round(float(rng.uniform(0.85, 1.15)), 4),
                "D_F_factor": round(float(rng.uniform(0.92, 1.08)), 4),
                "radiative_loss_fraction_Xr": round(xr, 4),
            },
            "intervention_do": intervention_do or {},
        }
        batch.append(traj)

    return batch


def execute_ray_trajectory_swarm(
    trajectory_inputs: List[Dict[str, Any]],
    use_ray_cluster: bool = True,
    comm_sync_state: str = "AUTONOMOUS_SQLITE_FALLBACK"
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    if not trajectory_inputs:
        raise ValueError("trajectory_inputs no puede ser una lista vacia.")

    sample_in = trajectory_inputs[0]
    N_grid = int(sample_in.get("grid_nodes_per_axis", 25))
    L_dom = float(sample_in.get("domain_half_width_m", 0.035))
    r_b = float(sample_in.get("burner_radius_m", 0.00318))

    ray_used = False
    if use_ray_cluster and RAY_AVAILABLE and ray is not None:
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True, num_cpus=4, include_dashboard=False)
        shared_grid_ref = put_shared_grid_in_ray_store(L_dom, N_grid, r_b)
        futures = [
            ray_simulate_trajectory_worker.remote(traj, shared_grid_ref, False)
            for traj in trajectory_inputs
        ]
        results: List[Dict[str, Any]] = ray.get(futures)
        ray_used = True
    else:
        shared_grid_local = create_cartesian_grid_3d(L_dom, N_grid, r_b)
        results = [
            run_trajectory_step_pure(traj, shared_grid=shared_grid_local, return_3d_arrays=False)
            for traj in trajectory_inputs
        ]

    elapsed_s = time.perf_counter() - t0
    T_max_list = [r["max_temperature_K"] for r in results]
    rf_list = [r["predicted_flame_radius_m"] for r in results]
    ext_list = [r["extinction_probability"] for r in results]

    representative_partitions = results[0]["partitions_16"]

    return {
        "status": "SUCCESS_RAY_SWARM_INFERENCE",
        "comm_sync_state": comm_sync_state,
        "sqlite_cached_families": [
            "ACME_S_FLAME_C2H4",
            "ACME_S_FLAME_CH4",
            "ACME_S_FLAME_H2",
            "PSI23_20013D1_EVIDENCE_ONLY",
        ],
        "cluster_execution_metrics": {
            "ray_distributed_active": ray_used,
            "trajectories_evaluated": len(results),
            "execution_time_s": round(elapsed_s, 4),
            "throughput_trajectories_per_s": round(len(results) / max(elapsed_s, 1e-6), 2),
        },
        "ensemble_summary_si": {
            "mean_max_temperature_K": round(float(np.mean(T_max_list)), 2),
            "std_max_temperature_K": round(float(np.std(T_max_list)), 2),
            "mean_flame_radius_m": round(float(np.mean(rf_list)), 5),
            "mean_extinction_probability": round(float(np.mean(ext_list)), 4),
            "cool_flame_fraction_in_swarm": round(
                float(np.mean([1.0 if r["llamas_frias_global_active"] else 0.0 for r in results])), 4
            ),
        },
        "partitions_16": representative_partitions,
        "trajectory_records": results,
    }


if __name__ == "__main__":
    print("=== PRUEBA DEL PUENTE DISTRIBUIDO RAY + WEBGPU (ia/ray_cluster_bridge.py) ===")
    test_batch = generate_trajectory_swarm_inputs(
        n_trajectories=8,
        base_fuel="C2H4",
        intervention_do={"U_ECLSS": 0.03, "E_FIELD": 1200.0},
        grid_nodes_per_axis=25,
    )
    swarm_out = execute_ray_trajectory_swarm(test_batch, use_ray_cluster=False)
    print(f"[OK] Estado: {swarm_out['status']} | comm_sync_state: {swarm_out['comm_sync_state']}")
    print(f"[OK] Metricas de ejecucion: {swarm_out['cluster_execution_metrics']}")
    print(f"[OK] Resumen del enjambre SI: {swarm_out['ensemble_summary_si']}")
    p0 = swarm_out["partitions_16"][0]
    print(f"[OK] Muestra Particion 0 (WebGPU): sector={p0['sector']} | flamelets={p0['flamelets']} | llamas_frias={p0['llamas_frias']}")