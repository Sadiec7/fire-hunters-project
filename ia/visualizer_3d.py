"""
ia/visualizer_3d.py
Módulo completo con las 5 funciones requeridas por verify_numerical.py, run_gemelo_3d.py y ray_cluster_bridge.py.
"""

import os
from typing import Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go


def extract_spherical_radial_profile(
    grid_dict: Dict[str, Any],
    field_3d: np.ndarray,
    n_bins: int = 30
) -> Dict[str, np.ndarray]:
    R = grid_dict["R"]
    r_b = grid_dict["burner_radius_m"]
    r_max = grid_dict["domain_half_width_m"]

    edges = np.linspace(r_b, r_max, n_bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    prof_mean = np.zeros(n_bins, dtype=np.float64)
    prof_std = np.zeros(n_bins, dtype=np.float64)

    for i in range(n_bins):
        mask = (R >= edges[i]) & (R < edges[i + 1])
        if np.any(mask):
            vals = field_3d[mask]
            prof_mean[i] = float(np.mean(vals))
            prof_std[i] = float(np.std(vals))
        elif i > 0:
            prof_mean[i] = prof_mean[i - 1]

    return {"r_m": centers, "profile_mean": prof_mean, "profile_std": prof_std}


def extract_spherical_shell_profiles(
    grid_dict: Dict[str, Any],
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    q_chem_3d: Optional[np.ndarray] = None,
    Y_P_3d: Optional[np.ndarray] = None,
    n_shells: int = 30
) -> Dict[str, Any]:
    p_T = extract_spherical_radial_profile(grid_dict, T_3d, n_bins=n_shells)
    p_YF = extract_spherical_radial_profile(grid_dict, Y_F_3d, n_bins=n_shells)
    p_YO = extract_spherical_radial_profile(grid_dict, Y_O_3d, n_bins=n_shells)

    if q_chem_3d is not None:
        p_q = extract_spherical_radial_profile(grid_dict, q_chem_3d, n_bins=n_shells)["profile_mean"]
    else:
        p_q = np.zeros_like(p_T["profile_mean"])

    if Y_P_3d is not None:
        p_YP = extract_spherical_radial_profile(grid_dict, Y_P_3d, n_bins=n_shells)["profile_mean"]
    else:
        p_YP = np.clip(1.0 - p_YF["profile_mean"] - p_YO["profile_mean"] - 0.767, 0.0, 1.0)

    return {
        "r_shells_m": p_T["r_m"],
        "T_mean_K": p_T["profile_mean"],
        "T_std_K": p_T["profile_std"],
        "Y_F_mean": p_YF["profile_mean"],
        "Y_O_mean": p_YO["profile_mean"],
        "Y_P_mean": p_YP,
        "q_chem_mean_W_m3": p_q,
    }


def compute_flame_metrics_3d(
    arg1: Any,
    arg2: Any,
    T_threshold_K: float = 1200.0
) -> Dict[str, float]:
    if isinstance(arg1, dict):
        grid_dict, T_3d = arg1, arg2
    else:
        T_3d, grid_dict = arg1, arg2
    R = grid_dict["R"]
    T_max = float(np.max(T_3d))
    hot_mask = T_3d >= max(T_threshold_K, 0.95 * T_max)
    r_f = float(np.mean(R[hot_mask])) if np.any(hot_mask) else float(grid_dict["burner_radius_m"])
    return {"T_max_K": round(T_max, 2), "max_temperature_K": round(T_max, 2), "flame_radius_m": round(r_f, 5)}


def generate_3d_isosurface_plotly(
    grid_dict: Dict[str, Any],
    T_3d: np.ndarray,
    output_html_path: str = "ia/output_flame_3d.html"
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
    stride = 2 if grid_dict["grid_nodes_per_axis"] > 30 else 1
    X = grid_dict["X"][::stride, ::stride, ::stride]
    Y = grid_dict["Y"][::stride, ::stride, ::stride]
    Z = grid_dict["Z"][::stride, ::stride, ::stride]
    T_sub = T_3d[::stride, ::stride, ::stride]
    T_max = float(np.max(T_sub))

    fig = go.Figure(
        data=go.Isosurface(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            value=T_sub.flatten(),
            isomin=max(550.0, 0.45 * T_max),
            isomax=0.98 * T_max,
            surface_count=3,
            colorscale="Hot",
            opacity=0.65,
            caps=dict(x_show=False, y_show=False, z_show=False),
            colorbar=dict(title="T [K]"),
        )
    )
    fig.update_layout(
        title="NASA ACME s-Flame 3D Benchmark - Temperature Isosurfaces [K]",
        scene=dict(xaxis_title="x [m]", yaxis_title="y [m]", zaxis_title="z [m]"),
    )
    fig.write_html(output_html_path, include_plotlyjs="cdn")
    return output_html_path


def generate_2d_slices_and_time_plots(
    sim_res: Dict[str, Any],
    output_png_path: str = "ia/output_summary_panels.png"
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    g = sim_res["grid_dict"]
    T_3d = sim_res["T_3d"]
    mid = g["grid_nodes_per_axis"] // 2
    ext = [g["x"][0], g["x"][-1], g["y"][0], g["y"][-1]]

    shells = extract_spherical_shell_profiles(
        g, T_3d, sim_res["Y_F_3d"], sim_res["Y_O_3d"], sim_res.get("q_chem_3d"), sim_res.get("Y_P_3d")
    )

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    im0 = axes[0, 0].imshow(T_3d[:, :, mid].T, origin="lower", extent=ext, cmap="inferno")
    axes[0, 0].set_title("Corte Ecuatorial T(x, y, z=0) [K]")
    plt.colorbar(im0, ax=axes[0, 0])

    axes[0, 1].plot(shells["r_shells_m"], shells["T_mean_K"], "r-o", markersize=4)
    axes[0, 1].set_title("Perfil Radial Esférico T(r) [K]")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(shells["r_shells_m"], shells["Y_F_mean"], "b-", label="Y_F")
    axes[1, 0].plot(shells["r_shells_m"], shells["Y_O_mean"], "g--", label="Y_O2")
    axes[1, 0].plot(shells["r_shells_m"], shells["Y_P_mean"], "m:", label="Y_P")
    axes[1, 0].set_title("Perfiles Radiales de Especies [-]")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(sim_res["time_history_s"], sim_res["T_max_history_K"], "k-", lw=2)
    axes[1, 1].set_title("Convergencia Temporal T_max(t) [K]")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_png_path, dpi=140)
    plt.close(fig)
    return output_png_path


if __name__ == "__main__":
    print("visualizer_3d.py OK | 5 funciones activas.")