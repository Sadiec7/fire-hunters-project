"""
ia/scene_3d_acme.py
Generador de la Escena 3D Basada en Evidencia para NASA ACME s-Flame (Ensayo 20013D1).
"""

import os
import sys
import json
from typing import Dict, Any, Optional, Tuple
import numpy as np
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sensor_registry_20013d1 import get_all_sensors_registry  # type: ignore
    from epistemic_guard import EPISTEMIC_COLORS_HEX, allow_3d_flame_isosurface  # type: ignore
except ImportError:
    from ia.sensor_registry_20013d1 import get_all_sensors_registry
    from ia.epistemic_guard import EPISTEMIC_COLORS_HEX, allow_3d_flame_isosurface


def load_acme_geometry_manifest(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    if manifest_path is None:
        manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acme_geometry_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"experimental_file_key": "20013D1", "meshes": {}}


def _create_sphere_wireframe_traces(
    radius_m: float,
    color_hex: str,
    name: str,
    hover_text: str,
    n_lat: int = 10,
    n_lon: int = 12,
    dash: str = "solid",
    width: int = 2
) -> go.Scatter3d:
    xs, ys, zs = [], [], []
    for phi in np.linspace(0, np.pi, n_lat):
        theta = np.linspace(0, 2 * np.pi, 40)
        xs.extend((radius_m * np.sin(phi) * np.cos(theta)).tolist() + [None])
        ys.extend((radius_m * np.sin(phi) * np.sin(theta)).tolist() + [None])
        zs.extend((radius_m * np.cos(phi) * np.ones_like(theta)).tolist() + [None])
    for th in np.linspace(0, 2 * np.pi, n_lon, endpoint=False):
        phi = np.linspace(0, np.pi, 25)
        xs.extend((radius_m * np.sin(phi) * np.cos(th)).tolist() + [None])
        ys.extend((radius_m * np.sin(phi) * np.sin(th)).tolist() + [None])
        zs.extend((radius_m * np.cos(phi)).tolist() + [None])

    return go.Scatter3d(
        x=xs,
        y=ys,
        z=zs,
        mode="lines",
        name=name,
        line=dict(color=color_hex, width=width, dash=dash),
        hoverinfo="text",
        text=hover_text,
    )


def build_acme_evidence_3d_traces(
    scenario_mode: str = "OBSERVED",
    scm_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    exp_id: str = "20013D1"
) -> Tuple[list, Dict[str, Any]]:
    manifest = load_acme_geometry_manifest()
    sensors = get_all_sensors_registry()
    traces = []

    c_obs = EPISTEMIC_COLORS_HEX["OBSERVED"]["hex"]
    c_inf = EPISTEMIC_COLORS_HEX["INFERRED"]["hex"]
    c_unv = EPISTEMIC_COLORS_HEX["UNVERIFIED"]["hex"]

    traces.append(
        _create_sphere_wireframe_traces(
            radius_m=0.00318,
            color_hex=c_obs,
            name="mesh_burner_sphere [VERIFIED: r_b=3.18 mm]",
            hover_text="<b>mesh_burner_sphere</b><br>Tier: VERIFIED_DIMENSION<br>Radio: 0.00318 m",
            n_lat=8,
            n_lon=10,
            width=4,
        )
    )

    if not allow_3d_flame_isosurface(exp_id):
        traces.append(
            _create_sphere_wireframe_traces(
                radius_m=0.022,
                color_hex=c_unv,
                name="wireframe_flame_lock [CAMPO 3D DE LLAMA DESACTIVADO]",
                hover_text="<b>[CAMPO 3D DE LLAMA DESACTIVADO: SIN CALIBRACIÓN FÍSICA VERIFICADA]</b>",
                n_lat=7,
                n_lon=8,
                dash="dot",
                width=2,
            )
        )

    inlet_color = "#2563EB" if scenario_mode == "OBSERVED" else c_inf
    traces.append(
        go.Scatter3d(
            x=[-0.045, 0.0, 0.0],
            y=[-0.015, 0.0, 0.0],
            z=[-0.060, -0.025, -0.00318],
            mode="lines+markers",
            name="mesh_gas_inlet_mfc2 [GEOMETRIC_APPROX | V]",
            line=dict(color=inlet_color, width=5),
            marker=dict(size=4, color=inlet_color),
        )
    )
    traces.append(
        go.Scatter3d(
            x=[0.045, 0.0, 0.0],
            y=[-0.015, 0.0, 0.0],
            z=[-0.060, -0.025, -0.00318],
            mode="lines+markers",
            name="mesh_gas_inlet_mfc3 [GEOMETRIC_APPROX | V]",
            line=dict(color=inlet_color, width=5, dash="dash"),
            marker=dict(size=4, color=inlet_color),
        )
    )

    tc_x, tc_y, tc_z, tc_texts, tc_sizes = [], [], [], [], []
    for sid in ("TCBurner", "TCA", "TCB", "TCC"):
        s = sensors[sid]
        cx, cy, cz = s["coords_3d_m"]
        tc_x.append(cx)
        tc_y.append(cy)
        tc_z.append(cz)

        if scenario_mode == "ALTERNATIVE" and scm_responses and sid in scm_responses:
            r_scm = scm_responses[sid]
            mult = float(r_scm.get("halo_radius_multiplier_3d", 1.2))
            tc_sizes.append(11.0 * mult)
            tc_texts.append(f"<b>{sid} [INFERRED SCM]</b><br>Δ: {r_scm['relative_delta_pct']:+.2f}%")
        else:
            tc_sizes.append(10.0)
            tc_texts.append(f"<b>{sid} [OBSERVED RAW]</b><br>r = {s['radial_distance_m']} m")

    traces.append(
        go.Scatter3d(
            x=tc_x,
            y=tc_y,
            z=tc_z,
            mode="lines+markers+text",
            name="mesh_tc_rake [TCBurner, TCA, TCB, TCC]",
            text=["TCBurner", "TCA", "TCB", "TCC"],
            textposition="top center",
            line=dict(color=c_inf if scenario_mode == "ALTERNATIVE" else "#0284C7", width=3),
            marker=dict(size=tc_sizes, color=c_inf if scenario_mode == "ALTERNATIVE" else c_obs),
            hoverinfo="text",
            hovertext=tc_texts,
        )
    )

    s_pmt = sensors["PMT3"]
    px, py, pz = s_pmt["coords_3d_m"]
    traces.append(
        go.Scatter3d(
            x=[0.0, px],
            y=[0.0, py],
            z=[0.0, pz],
            mode="lines+markers+text",
            name="mesh_pmt3 [GEOMETRIC_APPROX | PMT3]",
            text=["", "PMT3"],
            textposition="top center",
            line=dict(color="#A855F7", width=2, dash="dashdot"),
            marker=dict(size=[1, 13], color=c_inf if scenario_mode == "ALTERNATIVE" else "#9333EA"),
        )
    )

    s_rad = sensors["RadiometerCenter"]
    rx, ry, rz = s_rad["coords_3d_m"]
    traces.append(
        go.Scatter3d(
            x=[0.0, rx],
            y=[0.0, ry],
            z=[0.0, rz],
            mode="lines+markers+text",
            name="mesh_radiometer_center [VERIFIED: r=0.154 m]",
            text=["", "RadiometerCenter (154 mm)"],
            textposition="top center",
            line=dict(color=c_obs, width=2.5, dash="dot"),
            marker=dict(size=[1, 14], color=c_inf if scenario_mode == "ALTERNATIVE" else c_obs),
        )
    )

    th_ring = np.linspace(0, 2 * np.pi, 50)
    r_cir = 0.165
    x_cir = np.concatenate([r_cir * np.cos(th_ring), [None], r_cir * np.cos(th_ring)])
    y_cir = np.concatenate([r_cir * np.sin(th_ring), [None], r_cir * np.sin(th_ring)])
    z_cir = np.concatenate([np.full_like(th_ring, -0.07), [None], np.full_like(th_ring, 0.07)])

    traces.append(
        go.Scatter3d(
            x=x_cir,
            y=y_cir,
            z=z_cir,
            mode="lines",
            name="mesh_cir_housing [ILLUSTRATIVE_ONLY]",
            line=dict(color="#64748B", width=1.5, dash="dash"),
        )
    )

    return traces, manifest


if __name__ == "__main__":
    tr_obs, _ = build_acme_evidence_3d_traces("OBSERVED")
    print(f"scene_3d_acme.py OK | Sub-mallas 3D generadas: {len(tr_obs)}")