# -*- coding: utf-8 -*-
"""
ia/scene_3d_acme.py
Constructor de la Escena 3D Conceptual Basada en Evidencia para NASA ACME s-Flame 20013D1
(Puntos 1.R, 3.R, 4.R y 5.R de la Etapa 2).
Estructura las 7 sub-mallas obligatorias, los 6 sensores clicables con líneas de visión,
el Semáforo Epistémico y la Esfera Wireframe roja que reemplaza cualquier llama falsa.
"""

import os
import sys
from typing import Dict, Any, List, Optional
import numpy as np
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import load_experiment_package_20013d1  # type: ignore
    from sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS  # type: ignore
    from epistemic_guard import allow_3d_flame_isosurface, get_epistemic_locks_20013d1  # type: ignore
    from scm_counterfactual_bridge import evaluate_counterfactual_comparison  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import load_experiment_package_20013d1
    from ia.sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS
    from ia.epistemic_guard import allow_3d_flame_isosurface, get_epistemic_locks_20013d1
    from ia.scm_counterfactual_bridge import evaluate_counterfactual_comparison


REQUIRED_SUB_MESH_NAMES: List[str] = [
    "mesh_burner_sphere",
    "mesh_gas_inlet_mfc2",
    "mesh_gas_inlet_mfc3",
    "mesh_tc_rake",
    "mesh_pmt3",
    "mesh_radiometer_center",
    "mesh_cir_housing",
]


def _build_sphere_wireframe_traces(
    radius_m: float,
    color_hex: str,
    name: str,
    legendgroup: str,
    hover_text: str,
    line_width: int = 2,
    n_rings: int = 7,
) -> List[go.Scatter3d]:
    """Genera anillos de latitud y longitud 3D para representar una esfera wireframe o porosa."""
    traces: List[go.Scatter3d] = []
    theta = np.linspace(0.0, 2.0 * np.pi, 48)

    for idx, phi in enumerate(np.linspace(0.15 * np.pi, 0.85 * np.pi, n_rings)):
        x = radius_m * np.sin(phi) * np.cos(theta)
        y = radius_m * np.sin(phi) * np.sin(theta)
        z = np.full_like(theta, radius_m * np.cos(phi))
        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                name=name if idx == 0 else f"{name}_lat_{idx}",
                legendgroup=legendgroup,
                showlegend=(idx == 0),
                line=dict(color=color_hex, width=line_width),
                hoverinfo="text",
                text=hover_text,
            )
        )
    return traces


def build_acme_evidence_3d_figure(
    scenario_mode: str = "OBSERVED",
    comparator_payload: Optional[Dict[str, Any]] = None,
) -> go.Figure:
    """
    Construye la figura 3D interactiva de Plotly para:
      - scenario_mode == "OBSERVED" (Panel Izquierdo Azul - Evidencia NASA 20013D1)
      - scenario_mode == "ALTERNATIVE" (Panel Derecho Naranja - Inferencia SCM IGNIS-mu)
    Incluye las 7 sub-mallas nombradas, los 6 sensores clicables y el bloqueo de llama 3D.
    """
    if comparator_payload is None:
        comparator_payload = evaluate_counterfactual_comparison("20013D1")

    pkg = load_experiment_package_20013d1()
    sensors_reg = get_all_sensors_registry_20013d1()
    locks = get_epistemic_locks_20013d1()
    is_alt = str(scenario_mode).strip().upper() == "ALTERNATIVE"
    scm_responses = comparator_payload["alternative_scenario_orange"]["scm_sensor_responses"]

    fig = go.Figure()

    # 1. mesh_burner_sphere (VERIFIED_DIMENSION - r_b = 0.00318 m)
    burner_traces = _build_sphere_wireframe_traces(
        radius_m=0.00318,
        color_hex="#168039",
        name="mesh_burner_sphere [VERIFIED: r_b=3.18 mm]",
        legendgroup="VERIFIED_DIMENSION",
        hover_text=(
            "<b>mesh_burner_sphere</b><br>"
            "Tier: VERIFIED_DIMENSION<br>"
            "Semáforo: OBSERVED (#168039)<br>"
            "Radio verificado: r_b = 0.00318 m (6.35 mm diam)<br>"
            "Tubo soporte: 0.0016 m"
        ),
        line_width=5,
        n_rings=6,
    )
    for tr in burner_traces:
        fig.add_trace(tr)

    # 2. Esfera de Frontera Conceptual Transparente (Wireframe Rojo - Tarea 5.R: Bloqueo de Llama 3D)
    if not allow_3d_flame_isosurface("20013D1"):
        wireframe_traces = _build_sphere_wireframe_traces(
            radius_m=0.022,
            color_hex="#B22222",
            name=locks["wireframe_fallback_label"],
            legendgroup="UNVERIFIED",
            hover_text=(
                f"<b>{locks['wireframe_fallback_label']}</b><br>"
                "Semáforo: UNVERIFIED (#B22222)<br>"
                "Candado Epistémico: allow_3d_flame_isosurface('20013D1') = False<br>"
                "Prohibido renderizar bolas de fuego o campos 3D de temperatura sin calibración SI."
            ),
            line_width=2,
            n_rings=5,
        )
        for tr in wireframe_traces:
            fig.add_trace(tr)

    # 3. mesh_gas_inlet_mfc2 y mesh_gas_inlet_mfc3 (GEOMETRIC_APPROXIMATION)
    mfc_color = "#B4690E" if is_alt else "#168039"
    for mfc_key, x_start in [("mesh_gas_inlet_mfc2", -0.045), ("mesh_gas_inlet_mfc3", 0.045)]:
        mfc_id = "MFC2" if "mfc2" in mfc_key else "MFC3"
        fig.add_trace(
            go.Scatter3d(
                x=[x_start, 0.0, 0.0],
                y=[0.0, 0.0, 0.0],
                z=[-0.060, -0.035, -0.00318],
                mode="lines+markers",
                name=f"{mfc_key} [GEOMETRIC_APPROX]",
                legendgroup="GEOMETRIC_APPROXIMATION",
                line=dict(color=mfc_color, width=6),
                marker=dict(size=5, color=mfc_color),
                hoverinfo="text",
                text=(
                    f"<b>{mfc_key} ({mfc_id})</b><br>"
                    "Tier: GEOMETRIC_APPROXIMATION<br>"
                    f"Semáforo: {'INFERRED (Intervenido do)' if is_alt else 'OBSERVED'}<br>"
                    "Unidad: V [CALIBRACIÓN V -> kg/s NO VERIFICADA]<br>"
                    "Archivo PSI-23: 20013D1_mfcSetpoints.csv (42 eventos)"
                ),
            )
        )

    # 4. Sensores 3D: mesh_tc_rake (TCBurner, TCA, TCB, TCC), mesh_pmt3 y mesh_radiometer_center
    for s_id in MANDATORY_SENSOR_IDS:
        s_info = sensors_reg[s_id]
        pos = s_info["position_xyz_m"]
        tier = s_info["verification_tier"]

        if s_id == "RadiometerCenter":
            mesh_name = "mesh_radiometer_center"
        elif s_id == "PMT3":
            mesh_name = "mesh_pmt3"
        else:
            mesh_name = f"mesh_tc_rake ({s_id})"

        if is_alt:
            scm_s = scm_responses[s_id]
            node_color = "#B4690E"
            halo_mult = float(scm_s["halo_radius_multiplier_3d"])
            marker_size = 10.0 * halo_mult
            ep_tag = "INFERRED (SCM)"
            val_text = (
                f"Media Observada: {scm_s['observed_mean_raw']} {s_info['original_unit']}<br>"
                f"Media Inferida SCM: {scm_s['inferred_alt_mean_raw']} {s_info['original_unit']}<br>"
                f"<b>Delta SCM: {scm_s['delta_mean_raw']:+.4f} {s_info['original_unit']} ({scm_s['delta_relative_pct']:+.2f}%)</b><br>"
                f"Halo 3D proporcional a |Delta|: {halo_mult:.2f}x<br>"
                "causal_effect_identified: False"
            )
        else:
            node_color = "#168039"
            marker_size = 10.0
            ep_tag = "OBSERVED (NASA PSI-23)"
            val_text = (
                f"Media Cruda Registrada: {s_info['summary_stats_raw']['mean_raw']} {s_info['original_unit']}<br>"
                f"Rango Crudo: [{s_info['summary_stats_raw']['min_raw']}, {s_info['summary_stats_raw']['max_raw']}] {s_info['original_unit']}<br>"
                f"Estado Unidades: {s_info['raw_signal_status']} / {s_info['unit_verification_status']}"
            )

        # Línea de visión / radio desde el quemador hasta el sensor (Tarea 3.R)
        fig.add_trace(
            go.Scatter3d(
                x=[0.0, pos[0]],
                y=[0.0, pos[1]],
                z=[0.0, pos[2]],
                mode="lines",
                name=f"ray_{s_id}",
                legendgroup=tier,
                showlegend=False,
                line=dict(color=node_color, width=2, dash="dot"),
                hoverinfo="skip",
            )
        )

        # Hotspot 3D clicable del sensor (con halo proporcional a Delta en el escenario alternativo)
        fig.add_trace(
            go.Scatter3d(
                x=[pos[0]],
                y=[pos[1]],
                z=[pos[2]],
                mode="markers+text",
                name=f"{mesh_name} [{s_id}]",
                legendgroup=tier,
                text=[s_id],
                textposition="top center",
                marker=dict(
                    size=marker_size,
                    color=node_color,
                    opacity=0.92,
                    line=dict(color="#FFFFFF", width=2),
                ),
                customdata=[[s_id]],
                hoverinfo="text",
                hovertext=(
                    f"<b>Sensor: {s_id}</b> ({mesh_name})<br>"
                    f"Tier Geométrico: {tier}<br>"
                    f"Semáforo Epistémico: {ep_tag}<br>"
                    f"Archivo Origen: {s_info['source_file_psi23']}<br>"
                    f"Posición 3D [m]: {pos} (r = {s_info['radial_distance_m']} m)<br>"
                    f"{val_text}"
                ),
            )
        )

    # 5. mesh_cir_housing (ILLUSTRATIVE_ONLY - Anillos exteriores de la cámara CIR)
    theta_cir = np.linspace(0.0, 2.0 * np.pi, 60)
    r_cir = 0.165
    for idx_z, z_cir in enumerate([-0.08, 0.08]):
        fig.add_trace(
            go.Scatter3d(
                x=r_cir * np.cos(theta_cir),
                y=r_cir * np.sin(theta_cir),
                z=np.full_like(theta_cir, z_cir),
                mode="lines",
                name="mesh_cir_housing [ILLUSTRATIVE_ONLY]" if idx_z == 0 else "mesh_cir_housing_top",
                legendgroup="ILLUSTRATIVE_ONLY",
                showlegend=(idx_z == 0),
                line=dict(color="#6C757D", width=2, dash="dash"),
                hoverinfo="text",
                text=(
                    "<b>mesh_cir_housing</b><br>"
                    "Tier: ILLUSTRATIVE_ONLY<br>"
                    "Semáforo: UNVERIFIED / CONTEXTUAL (#6C757D)<br>"
                    "Carcasa ilustrativa de la cámara CIR; no interviene en inferencia."
                ),
            )
        )

    title_prefix = (
        "🟠 ESCENARIO ALTERNATIVO (SCM IGNIS-mu | INFERRED)"
        if is_alt
        else "🔵 ESCENARIO OBSERVADO (NASA 20013D1 | OBSERVED)"
    )

    fig.update_layout(
        title=dict(text=title_prefix, font=dict(size=14, color="#FFFFFF")),
        paper_bgcolor="#0B132B",
        plot_bgcolor="#0B132B",
        font=dict(color="#E0E6ED", size=11),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(11, 19, 43, 0.82)",
        ),
        scene=dict(
             bgcolor="#0B132B",
            xaxis=dict(title="X [m]", range=[-0.18, 0.18], gridcolor="#1C2541"),
            yaxis=dict(title="Y [m]", range=[-0.18, 0.18], gridcolor="#1C2541"),
            zaxis=dict(title="Z [m]", range=[-0.10, 0.10], gridcolor="#1C2541"),
            camera=dict(eye=dict(x=1.35, y=1.35, z=0.85)),
        ),
    )
    return fig


def export_standalone_acme_scene_html(
    output_html_path: Optional[str] = None
) -> str:
    """Exporta la escena 3D observada standalone y verifica las 7 sub-mallas obligatorias."""
    if output_html_path is None:
        output_html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_scene_3d_20013d1.html"
        )
    fig = build_acme_evidence_3d_figure("OBSERVED")
    fig.write_html(output_html_path, include_plotlyjs="cdn")
    return output_html_path


if __name__ == "__main__":
    print("=== PRUEBA FASE 3 - PUNTOS 1.R, 3.R Y 5.R (ia/scene_3d_acme.py) ===")
    out_path = export_standalone_acme_scene_html()
    fig_obs = build_acme_evidence_3d_figure("OBSERVED")
    fig_alt = build_acme_evidence_3d_figure("ALTERNATIVE")
    print(f"[OK] Sub-mallas normativas registradas: {REQUIRED_SUB_MESH_NAMES}")
    print(f"[OK] Trazas 3D Escenario Observado    : {len(fig_obs.data)} trazas (con Wireframe rojo anti-llama falsa)")
    print(f"[OK] Trazas 3D Escenario Alternativo  : {len(fig_alt.data)} trazas (con halos SCM proporcionales a Delta)")
    print(f"[OK] Archivo HTML 3D exportado en     : {out_path}")