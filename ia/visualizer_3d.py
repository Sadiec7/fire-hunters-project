"""
ia/visualizer_3d.py
Visualización 3D Interactiva (Plotly), Cortes 2D (Matplotlib) y Extracción Radial - Bloque 7.
"""

import os
import sys
import json
from typing import Dict, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def extract_spherical_shell_profiles(
    grid_dict: Dict[str, Any],
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    n_bins: int = 30
) -> Dict[str, np.ndarray]:
    """Promedia azimutalmente los campos 3D en cascarones esféricos concéntricos."""
    R = grid_dict["R"]
    r_b = grid_dict["burner_radius_m"]
    L = grid_dict["domain_half_width_m"]

    r_edges = np.linspace(r_b, L, n_bins + 1)
    r_shells = 0.5 * (r_edges[:-1] + r_edges[1:])

    T_mean = np.zeros(n_bins, dtype=np.float64)
    T_std = np.zeros(n_bins, dtype=np.float64)
    YF_mean = np.zeros(n_bins, dtype=np.float64)
    YO_mean = np.zeros(n_bins, dtype=np.float64)

    for i in range(n_bins):
        mask = (R >= r_edges[i]) & (R < r_edges[i + 1])
        if np.any(mask):
            T_mean[i] = float(np.mean(T_3d[mask]))
            T_std[i] = float(np.std(T_3d[mask]))
            YF_mean[i] = float(np.mean(Y_F_3d[mask]))
            YO_mean[i] = float(np.mean(Y_O_3d[mask]))
        elif i > 0:
            T_mean[i] = T_mean[i - 1]
            YF_mean[i] = YF_mean[i - 1]
            YO_mean[i] = YO_mean[i - 1]

    return {
        "r_shells_m": r_shells,
        "T_mean_K": T_mean,
        "T_std_K": T_std,
        "Y_F_mean": YF_mean,
        "Y_O_mean": YO_mean,
    }


def extract_spherical_radial_profile(
    grid_dict: Dict[str, Any],
    field_3d: np.ndarray,
    n_bins: int = 40
) -> Dict[str, np.ndarray]:
    """Extractor radial individual para cualquier campo escalar 3D."""
    R = grid_dict["R"]
    r_b = grid_dict["burner_radius_m"]
    L = grid_dict["domain_half_width_m"]
    r_edges = np.linspace(r_b, L, n_bins + 1)
    r_centers = 0.5 * (r_edges[:-1] + r_edges[1:])
    prof_mean = np.zeros(n_bins, dtype=np.float64)

    for i in range(n_bins):
        mask = (R >= r_edges[i]) & (R < r_edges[i + 1])
        if np.any(mask):
            prof_mean[i] = float(np.mean(field_3d[mask]))
        elif i > 0:
            prof_mean[i] = prof_mean[i - 1]

    return {"r_m": r_centers, "profile_mean": prof_mean}


def generate_3d_isosurface_plotly(
    grid_dict: Dict[str, Any],
    T_3d: np.ndarray,
    output_html_path: str = "ia/output_flame_3d.html"
) -> Dict[str, Any]:
    """Genera la visualización interactiva 3D de la llama y el quemador en Plotly."""
    X = grid_dict["X"]
    Y = grid_dict["Y"]
    Z = grid_dict["Z"]
    R = grid_dict["R"]
    r_b = grid_dict["burner_radius_m"]

    fig = go.Figure()

    # Superficie de la esfera del quemador poroso
    fig.add_trace(go.Isosurface(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        value=R.flatten(),
        isomin=r_b * 0.9,
        isomax=r_b * 1.05,
        surface_count=1,
        colorscale="Greys",
        opacity=0.9,
        showscale=False,
        name="Quemador Poroso (r_b)",
    ))

    # Isosuperficies térmicas de la llama esférica
    T_max = float(np.max(T_3d))
    iso_min = max(600.0, 0.55 * T_max)
    iso_max = max(900.0, 0.95 * T_max)

    fig.add_trace(go.Isosurface(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        value=T_3d.flatten(),
        isomin=iso_min,
        isomax=iso_max,
        surface_count=3,
        colorscale="Hot",
        opacity=0.45,
        caps=dict(x_show=False, y_show=False, z_show=False),
        colorbar=dict(title="T [K]"),
        name="Llama Esférica 3D",
    ))

    fig.update_layout(
        title="Gemelo Digital 3D NASA ACME / s-Flame (Microgravedad)",
        scene=dict(
            xaxis_title="x [m]",
            yaxis_title="y [m]",
            zaxis_title="z [m]",
            aspectmode="cube",
        ),
        margin=dict(l=10, r=10, b=10, t=40),
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
    fig.write_html(output_html_path)
    return json.loads(fig.to_json())


def generate_2d_slices_and_time_plots(
    sim_results: Dict[str, Any],
    output_png_path: str = "ia/output_summary_panels.png"
) -> str:
    """Genera panel 2x2 con cortes centrales (T, Y_F, Y_O) y evolución temporal / radial."""
    grid_dict = sim_results["grid_dict"]
    T_3d = sim_results["T_3d"]
    Y_F_3d = sim_results["Y_F_3d"]
    Y_O_3d = sim_results["Y_O_3d"]

    N = grid_dict["grid_nodes_per_axis"]
    k_mid = N // 2
    L = grid_dict["domain_half_width_m"]
    extent = [-L, L, -L, L]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    im0 = axes[0, 0].imshow(T_3d[:, :, k_mid].T, origin="lower", extent=extent, cmap="inferno")
    axes[0, 0].set_title("Corte Central 2D: Temperatura T(x, y, 0) [K]")
    axes[0, 0].set_xlabel("x [m]")
    axes[0, 0].set_ylabel("y [m]")
    plt.colorbar(im0, ax=axes[0, 0])

    im1 = axes[0, 1].imshow(Y_F_3d[:, :, k_mid].T, origin="lower", extent=extent, cmap="YlGnBu")
    axes[0, 1].set_title("Corte Central 2D: Combustible Y_F(x, y, 0) [-]")
    axes[0, 1].set_xlabel("x [m]")
    axes[0, 1].set_ylabel("y [m]")
    plt.colorbar(im1, ax=axes[0, 1])

    im2 = axes[1, 0].imshow(Y_O_3d[:, :, k_mid].T, origin="lower", extent=extent, cmap="PuBu")
    axes[1, 0].set_title("Corte Central 2D: Oxidante Y_O(x, y, 0) [-]")
    axes[1, 0].set_xlabel("x [m]")
    axes[1, 0].set_ylabel("y [m]")
    plt.colorbar(im2, ax=axes[1, 0])

    shells = extract_spherical_shell_profiles(grid_dict, T_3d, Y_F_3d, Y_O_3d)
    axes[1, 1].plot(shells["r_shells_m"], shells["T_mean_K"], "r-o", label="T_mean 3D(r) [K]")
    axes[1, 1].set_title("Perfil Radial Esférico Promediado T(r)")
    axes[1, 1].set_xlabel("Radio r [m]")
    axes[1, 1].set_ylabel("Temperatura [K]")
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    plt.savefig(output_png_path, dpi=150)
    plt.close(fig)
    return output_png_path


if __name__ == "__main__":
    from solver_3d import run_transient_simulation_3d
    from contract_si import SimulationInputSI

    sim_out = run_transient_simulation_3d(SimulationInputSI(grid_nodes_per_axis=25), max_steps=60)
    generate_3d_isosurface_plotly(sim_out["grid_dict"], sim_out["T_3d"])
    generate_2d_slices_and_time_plots(sim_out)
    print("Visualizaciones generadas: ia/output_flame_3d.html y ia/output_summary_panels.png")