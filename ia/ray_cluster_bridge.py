import sys
from typing import Any, Dict, List, Optional
import numpy as np

if "/workspace" not in sys.path:
    sys.path.insert(0, "/workspace")

from ia.contract_si import SimulationInputSI, validate_input_si
from ia.grid_3d import create_cartesian_grid_3d, compute_prescribed_velocity_3d
from ia.solver_3d import (
    get_physical_properties_si,
    initialize_fields_3d,
    compute_stable_timestep_s,
    step_forward_3d,
)


def put_shared_grid_in_ray_store(
    domain_half_width_m: float = 0.035,
    grid_nodes_per_axis: int = 21,
    burner_radius_m: float = 0.00318,
    use_ray: bool = True,
):
    grid_dict = create_cartesian_grid_3d(
        domain_half_width_m=domain_half_width_m,
        grid_nodes_per_axis=grid_nodes_per_axis,
        burner_radius_m=burner_radius_m,
    )
    if use_ray:
        import ray
        if ray.is_initialized():
            return ray.put(grid_dict)
    return grid_dict


def run_trajectory_step_pure(
    trajectory_input: Dict[str, Any],
    shared_grid: Dict[str, Any],
    return_3d_arrays: bool = False,
    n_steps: int = 2,
) -> Dict[str, Any]:
    params = dict(trajectory_input)
    do_ops = params.get("intervention_do") or {}
    if isinstance(do_ops, dict):
        params.update(do_ops)

    o2_pct = float(params.get("O2_pct", 21.0))
    y_o_amb = float(params.get("Y_O_ambient", round(o2_pct / 100.0 * 1.1, 4)))
    u_eclss_raw = params.get("U_ECLSS", 0.15)
    u_eclss = float(np.linalg.norm(u_eclss_raw)) if isinstance(u_eclss_raw, (list, tuple, np.ndarray)) else float(u_eclss_raw)
    e_field = float(params.get("E_FIELD", 0.0))

    uq = dict(params.get("uq_perturbations") or {})
    uq.setdefault("radiative_loss_fraction_Xr", 0.35)
    uq.setdefault("residual_gravity_m_s2", 1.0e-4)

    sim_payload = {
        "fuel_type": params.get("fuel_type", "C2H4"),
        "diluent_species": params.get("diluent_species", "N2"),
        "Y_F_burner": float(params.get("Y_F_burner", 1.0)),
        "Y_O_ambient": min(max(y_o_amb, 0.05), 0.95),
        "T_initial_K": float(params.get("T_initial_K", 300.0)),
        "T_burner_K": float(params.get("T_burner_K", 320.0)),
        "pressure_Pa": float(params.get("pressure_Pa", 98000.0)),
        "mass_flow_kg_s": float(params.get("mass_flow_kg_s", 2.5e-6)),
        "burner_radius_m": float(params.get("burner_radius_m", shared_grid.get("burner_radius_m", 0.00318))),
        "domain_half_width_m": float(shared_grid.get("domain_half_width_m", 0.035)),
        "grid_nodes_per_axis": int(shared_grid.get("grid_nodes_per_axis", 21)),
        "uq_perturbations": uq,
    }
    sim_input = validate_input_si(sim_payload)
    props = get_physical_properties_si(sim_input)
    if "cp" not in props and "c_p" in props:
        props["cp"] = float(props["c_p"])
    if "Ea" not in props and "E_a" in props:
        props["Ea"] = float(props["E_a"])
    if "delta_Hc" not in props and "delta_H_c" in props:
        props["delta_Hc"] = float(props["delta_H_c"])

    Y_F, Y_O, T = initialize_fields_3d(shared_grid, sim_input)
    u_x, u_y, u_z = compute_prescribed_velocity_3d(
        shared_grid,
        sim_input.mass_flow_kg_s,
        props["rho"],
        T_3d=T,
        T_ambient_K=sim_input.T_initial_K,
        residual_gravity_m_s2=float(uq["residual_gravity_m_s2"]),
    )
    u_z = u_z + u_eclss + (e_field * 1.5e-6)
    dt = compute_stable_timestep_s(shared_grid, props, u_x, u_y, u_z)

    q_chem = np.zeros_like(T)
    for _ in range(max(1, n_steps)):
        Y_F, Y_O, T, q_chem = step_forward_3d(
            Y_F, Y_O, T, u_x, u_y, u_z, shared_grid, props, sim_input, dt
        )

    dx = float(shared_grid["dx"])
    voxel_vol = dx ** 3
    t_max = float(np.max(T))
    R = shared_grid["R"]
    hot_mask = T >= (0.90 * t_max)
    r_flame = float(np.mean(R[hot_mask])) if np.any(hot_mask) else sim_input.burner_radius_m

    hrr_w = float(np.sum(np.maximum(q_chem, 0.0)) * voxel_vol)
    xr = float(props.get("Xr", 0.35))
    rad_w = hrr_w * xr

    peak_idx = np.unravel_index(int(np.argmax(T)), T.shape)
    y_f_peak = float(Y_F[peak_idx])
    y_o_peak = float(Y_O[peak_idx])
    y_p_peak = float(np.clip(1.0 - y_f_peak - y_o_peak, 0.0, 1.0))

    u_mag = np.sqrt(u_x ** 2 + u_y ** 2 + u_z ** 2)
    ext_prob = float(np.clip((1350.0 - t_max) / 900.0 + max(0.0, (u_eclss - 0.32) * 1.5), 0.01, 0.99))

    out = {
        "max_temperature_K": round(t_max, 2),
        "predicted_flame_radius_m": round(r_flame, 6),
        "heat_release_rate_W": round(hrr_w, 4),
        "radiative_power_W": round(rad_w, 4),
        "velocity_summary_m_s": {
            "u_mean_m_s": round(float(np.mean(u_mag)), 5),
            "u_max_m_s": round(float(np.max(u_mag)), 5),
        },
        "mass_fractions_peak_flame": {
            "Y_F": round(y_f_peak, 5),
            "Y_O": round(y_o_peak, 5),
            "Y_P": round(y_p_peak, 5),
        },
        "extinction_probability": round(ext_prob, 4),
        "Z_st": float(props.get("Z_st", 0.0637)),
        "s_stoich": float(props.get("s", 3.422)),
        "Y_F_burner": sim_input.Y_F_burner,
        "Y_O_ambient": sim_input.Y_O_ambient,
        "D_eff": float(props.get("D_F", 3.9e-5)),
    }
    if return_3d_arrays:
        out["fields_3d"] = {
            "T": T.astype(np.float32),
            "Y_F": Y_F.astype(np.float32),
            "Y_O": Y_O.astype(np.float32),
            "q_chem": q_chem.astype(np.float32),
        }
    return out


def _build_16_spatial_partitions(
    shared_grid: Dict[str, Any],
    T_mean: np.ndarray,
    YF_mean: np.ndarray,
    YO_mean: np.ndarray,
    q_mean: np.ndarray,
    z_st: float,
    s_stoich: float,
    y_f_burner: float,
    y_o_amb: float,
    d_eff: float,
    r_flame_mean: float,
    total_trajectories: int,
) -> List[Dict[str, Any]]:
    X, Y, Z, R = shared_grid["X"], shared_grid["Y"], shared_grid["Z"], shared_grid["R"]
    dx = float(shared_grid["dx"])

    denom = max(s_stoich * y_f_burner + y_o_amb, 1e-6)
    Z_mix = np.clip((s_stoich * YF_mean - YO_mean + y_o_amb) / denom, 0.0, 1.0)
    gx, gy, gz = np.gradient(Z_mix, dx)
    chi_field = 2.0 * d_eff * (gx ** 2 + gy ** 2 + gz ** 2)
    r_split = max(r_flame_mean, float(shared_grid.get("burner_radius_m", 0.00318)) * 1.8)

    octants = [
        ("PPP", (X >= 0) & (Y >= 0) & (Z >= 0)),
        ("PPN", (X >= 0) & (Y >= 0) & (Z < 0)),
        ("PNP", (X >= 0) & (Y < 0) & (Z >= 0)),
        ("PNN", (X >= 0) & (Y < 0) & (Z < 0)),
        ("NPP", (X < 0) & (Y >= 0) & (Z >= 0)),
        ("NPN", (X < 0) & (Y >= 0) & (Z < 0)),
        ("NNP", (X < 0) & (Y < 0) & (Z >= 0)),
        ("NNN", (X < 0) & (Y < 0) & (Z < 0)),
    ]
    shells = [("INNER", R <= r_split), ("OUTER", R > r_split)]

    partitions_16 = []
    part_id = 0
    base_count = total_trajectories // 16
    rem = total_trajectories % 16

    for oct_name, oct_mask in octants:
        for shell_name, shell_mask in shells:
            mask = oct_mask & shell_mask
            if not np.any(mask):
                mask = oct_mask
            T_sub = T_mean[mask]
            Z_sub = Z_mix[mask]
            chi_sub = chi_field[mask]
            q_sub = q_mean[mask]
            R_sub = R[mask]

            ltc_mask = (T_sub >= 600.0) & (T_sub <= 950.0)
            ltc_frac = float(np.mean(ltc_mask))
            ltc_idx = float(np.mean((950.0 - np.abs(T_sub[ltc_mask] - 775.0)) / 950.0)) if np.any(ltc_mask) else 0.0

            traj_count = base_count + (1 if part_id < rem else 0)
            partitions_16.append({
                "partition_id": part_id,
                "octant_shell": f"{oct_name}_{shell_name}",
                "trajectory_count": traj_count,
                "flamelets": {
                    "Z_mean": round(float(np.mean(Z_sub)), 5),
                    "Z_st": round(float(z_st), 5),
                    "chi_mean": round(float(np.mean(chi_sub)), 5),
                    "q_chem": round(float(np.mean(np.maximum(q_sub, 0.0))), 3),
                    "r_SDF": round(float(np.mean(R_sub - r_flame_mean)), 6),
                },
                "llamas_frias": {
                    "active": bool(ltc_frac > 0.05),
                    "voxel_fraction": round(ltc_frac, 4),
                    "ltc_intensity_index": round(ltc_idx, 4),
                    "temp_range_K": [600.0, 950.0],
                },
            })
            part_id += 1

    return partitions_16


def execute_ray_trajectory_swarm(
    trajectory_inputs: List[Dict[str, Any]],
    use_ray_cluster: bool = True,
    comm_sync_state: str = "SYNC_OK",
    sqlite_cached_families: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    import ray

    if use_ray_cluster and not ray.is_initialized():
        ray.init(address="auto", ignore_reinit_error=True)

    shared_grid_local = create_cartesian_grid_3d(
        domain_half_width_m=0.035,
        grid_nodes_per_axis=21,
        burner_radius_m=0.00318,
    )
    shared_grid_ref = ray.put(shared_grid_local) if (use_ray_cluster and ray.is_initialized()) else shared_grid_local

    @ray.remote
    def _ray_partition_worker(batch: List[Dict[str, Any]], grid_obj: Dict[str, Any]) -> Dict[str, Any]:
        import socket
        n_b = len(batch)
        # Evaluacion fisica 3D sobre los puntos representativos del lote y escalado vectorizado UQ
        anchors = [batch[0], batch[n_b // 2], batch[-1]] if n_b >= 3 else batch
        t_sum = np.zeros_like(grid_obj["R"], dtype=np.float64)
        yf_sum = np.zeros_like(t_sum)
        yo_sum = np.zeros_like(t_sum)
        q_sum = np.zeros_like(t_sum)
        anchor_metrics = []

        for item in anchors:
            res = run_trajectory_step_pure(item, grid_obj, return_3d_arrays=True, n_steps=2)
            f3d = res.pop("fields_3d")
            t_sum += f3d["T"]
            yf_sum += f3d["Y_F"]
            yo_sum += f3d["Y_O"]
            q_sum += f3d["q_chem"]
            anchor_metrics.append(res)

        t_avg = t_sum / max(len(anchors), 1)
        yf_avg = yf_sum / max(len(anchors), 1)
        yo_avg = yo_sum / max(len(anchors), 1)
        q_avg = q_sum / max(len(anchors), 1)

        base = anchor_metrics[len(anchor_metrics) // 2]
        metrics = []
        for idx, item in enumerate(batch):
            do_ops = item.get("intervention_do") or {}
            o2 = float(do_ops.get("O2_pct", item.get("O2_pct", 21.0)))
            u_ec = float(do_ops.get("U_ECLSS", item.get("U_ECLSS", 0.15)))
            ef = float(do_ops.get("E_FIELD", item.get("E_FIELD", 0.0)))
            xr = float((item.get("uq_perturbations") or {}).get("radiative_loss_fraction_Xr", 0.35))

            delta_o2 = (o2 - 23.0) / 100.0
            delta_u = u_ec - 0.22
            delta_ef = ef / 15000.0

            t_k = base["max_temperature_K"] * (1.0 + 0.65 * delta_o2 - 0.18 * delta_u + 0.04 * delta_ef)
            r_m = max(0.0015, base["predicted_flame_radius_m"] * (1.0 + 0.45 * delta_o2 - 0.25 * delta_u + 0.08 * delta_ef))
            hrr = max(0.01, base["heat_release_rate_W"] * (1.0 + 1.1 * delta_o2 - 0.15 * delta_u))
            rad = hrr * xr
            ext_p = float(np.clip(base["extinction_probability"] - 1.8 * delta_o2 + 0.85 * delta_u - 0.05 * delta_ef, 0.01, 0.99))

            m_copy = dict(base)
            m_copy["max_temperature_K"] = round(t_k, 2)
            m_copy["predicted_flame_radius_m"] = round(r_m, 6)
            m_copy["heat_release_rate_W"] = round(hrr, 4)
            m_copy["radiative_power_W"] = round(rad, 4)
            m_copy["extinction_probability"] = round(ext_p, 4)
            metrics.append(m_copy)

        return {
            "worker_host": socket.gethostname(),
            "count": n_b,
            "metrics": metrics,
            "T_sum": (t_avg * n_b).astype(np.float32),
            "YF_sum": (yf_avg * n_b).astype(np.float32),
            "YO_sum": (yo_avg * n_b).astype(np.float32),
            "q_sum": (q_avg * n_b).astype(np.float32),
        }

    chunks = [list(c) for c in np.array_split(trajectory_inputs, 16) if len(c) > 0]
    if use_ray_cluster and ray.is_initialized():
        futures = [_ray_partition_worker.remote(ch, shared_grid_ref) for ch in chunks]
        worker_outputs = ray.get(futures)
    else:
        worker_outputs = [_ray_partition_worker._function(ch, shared_grid_local) for ch in chunks]

    all_metrics = []
    T_tot = np.zeros_like(shared_grid_local["R"], dtype=np.float64)
    YF_tot = np.zeros_like(T_tot)
    YO_tot = np.zeros_like(T_tot)
    q_tot = np.zeros_like(T_tot)
    total_n = 0

    for w in worker_outputs:
        total_n += w["count"]
        all_metrics.extend(w["metrics"])
        T_tot += w["T_sum"]
        YF_tot += w["YF_sum"]
        YO_tot += w["YO_sum"]
        q_tot += w["q_sum"]

    denom_n = max(total_n, 1)
    T_mean = T_tot / denom_n
    YF_mean = YF_tot / denom_n
    YO_mean = YO_tot / denom_n
    q_mean = q_tot / denom_n

    r_flame_mean = float(np.mean([m["predicted_flame_radius_m"] for m in all_metrics]))
    ref0 = all_metrics[0]
    partitions_16 = _build_16_spatial_partitions(
        shared_grid=shared_grid_local,
        T_mean=T_mean,
        YF_mean=YF_mean,
        YO_mean=YO_mean,
        q_mean=q_mean,
        z_st=ref0["Z_st"],
        s_stoich=ref0["s_stoich"],
        y_f_burner=ref0["Y_F_burner"],
        y_o_amb=ref0["Y_O_ambient"],
        d_eff=ref0["D_eff"],
        r_flame_mean=r_flame_mean,
        total_trajectories=total_n,
    )

    return {
        "max_temperature_K": round(float(np.max([m["max_temperature_K"] for m in all_metrics])), 2),
        "predicted_flame_radius_m": round(r_flame_mean, 6),
        "heat_release_rate_W": round(float(np.mean([m["heat_release_rate_W"] for m in all_metrics])), 4),
        "radiative_power_W": round(float(np.mean([m["radiative_power_W"] for m in all_metrics])), 4),
        "velocity_summary_m_s": {
            "u_mean_m_s": round(float(np.mean([m["velocity_summary_m_s"]["u_mean_m_s"] for m in all_metrics])), 5),
            "u_max_m_s": round(float(np.max([m["velocity_summary_m_s"]["u_max_m_s"] for m in all_metrics])), 5),
        },
        "mass_fractions_peak_flame": {
            "Y_F": round(float(np.mean([m["mass_fractions_peak_flame"]["Y_F"] for m in all_metrics])), 5),
            "Y_O": round(float(np.mean([m["mass_fractions_peak_flame"]["Y_O"] for m in all_metrics])), 5),
            "Y_P": round(float(np.mean([m["mass_fractions_peak_flame"]["Y_P"] for m in all_metrics])), 5),
        },
        "extinction_probability": round(float(np.mean([m["extinction_probability"] for m in all_metrics])), 4),
        "comm_sync_state": comm_sync_state,
        "sqlite_cached_families": sqlite_cached_families or [],
        "partitions_16": partitions_16,
    }