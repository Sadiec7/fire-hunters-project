"""
ia/comparator_3d_ui.py
Funcionalidad Estrella Etapa 2: El Comparador Experimental Contrafactual 3D (Ensayo NASA 20013D1).
Tabla del Panel Derecho limpia (sin la columna 'Efecto Causal ID').
"""

import os
import sys
import json
from typing import Dict, Any
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from scm_counterfactual_bridge import evaluate_counterfactual_comparison, ALTERNATIVE_PROGRAMS_PRESETS  # type: ignore
    from scene_3d_acme import build_acme_evidence_3d_traces  # type: ignore
except ImportError:
    from ia.scm_counterfactual_bridge import evaluate_counterfactual_comparison, ALTERNATIVE_PROGRAMS_PRESETS
    from ia.scene_3d_acme import build_acme_evidence_3d_traces


def build_split_screen_comparator_html(
    comparison_payload: Dict[str, Any],
    output_html_path: str = "output_comparator_20013d1.html"
) -> str:
    alt_block = comparison_payload["alternative_scenario_orange"]
    scm_resp = alt_block["scm_sensor_responses"]
    bounds = comparison_payload["counterfactual_coupling_bounds"]
    sync_status = comparison_payload["synchronization_status"]

    traces_obs, _ = build_acme_evidence_3d_traces("OBSERVED", None, "20013D1")
    traces_alt, _ = build_acme_evidence_3d_traces("ALTERNATIVE", scm_resp, "20013D1")

    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "scene"}, {"type": "scene"}]],
        subplot_titles=(
            "PANEL IZQUIERDO (AZUL): ESCENARIO OBSERVADO [OBSERVED #168039]",
            "PANEL DERECHO (NARANJA): ESCENARIO ALTERNATIVO SCM [INFERRED #B4690E]",
        ),
        horizontal_spacing=0.04,
    )

    for tr in traces_obs:
        fig.add_trace(tr, row=1, col=1)
    for tr in traces_alt:
        tr.showlegend = False
        fig.add_trace(tr, row=1, col=2)

    scene_cfg = dict(
        xaxis=dict(title="X [m]", range=[-0.18, 0.18], backgroundcolor="#0F172A", gridcolor="#334155"),
        yaxis=dict(title="Y [m]", range=[-0.18, 0.18], backgroundcolor="#0F172A", gridcolor="#334155"),
        zaxis=dict(title="Z [m]", range=[-0.09, 0.09], backgroundcolor="#0F172A", gridcolor="#334155"),
        aspectmode="manual",
        aspectratio=dict(x=1.2, y=1.2, z=0.75),
    )

    fig.update_layout(
        paper_bgcolor="#0B1120",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Segoe UI, Roboto, sans-serif"),
        height=560,
        margin=dict(l=10, r=10, t=50, b=10),
        scene=scene_cfg,
        scene2=scene_cfg,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(15, 23, 42, 0.85)",
        ),
    )

    plotly_div = fig.to_html(full_html=False, include_plotlyjs="cdn")
    data_json_str = json.dumps(comparison_payload, ensure_ascii=False)

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Gemelo Conceptual Basado en Evidencia - Comparador 3D NASA 20013D1</title>
<style>
  body {{ margin:0; padding:18px; background:#070B19; color:#F1F5F9; font-family:'Segoe UI',Roboto,sans-serif; }}
  .top-header {{ display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1E293B; padding-bottom:12px; margin-bottom:14px; }}
  .badge {{ padding:5px 10px; border-radius:6px; font-weight:700; font-size:12px; display:inline-block; margin-right:6px; }}
  .b-obs {{ background:#168039; color:#fff; }}
  .b-inf {{ background:#B4690E; color:#fff; }}
  .b-unv {{ background:#B22222; color:#fff; }}
  .sync-banner {{ background:rgba(178,34,34,0.22); border:1px solid #B22222; padding:10px 14px; border-radius:8px; margin-bottom:14px; font-size:13px; }}
  .cta-bar {{ display:flex; flex-direction:column; align-items:center; gap:10px; margin:14px 0; }}
  .btn-compare {{ background:linear-gradient(90deg,#1D4ED8,#D97706); color:#fff; border:2px solid #F8FAFC; padding:12px 28px; font-size:16px; font-weight:800; border-radius:8px; cursor:pointer; }}
  .bounds-box {{ background:#0F172A; border:2px solid #B4690E; border-radius:10px; padding:12px 22px; text-align:center; max-width:860px; }}
  .bounds-eq {{ font-size:22px; font-weight:800; color:#FBBF24; margin:4px 0; }}
  .grid-bottom {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-top:18px; }}
  .card {{ background:#0F172A; border:1px solid #1E293B; border-radius:10px; padding:14px; }}
  .card-blue {{ border-top:4px solid #1D4ED8; }}
  .card-orange {{ border-top:4px solid #D97706; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }}
  th, td {{ padding:8px; border-bottom:1px solid #1E293B; text-align:left; }}
  th {{ color:#94A3B8; }}
  .ctrl-row {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-top:8px; }}
  .btn-disabled {{ background:#334155; color:#94A3B8; border:1px solid #475569; padding:7px 14px; border-radius:6px; cursor:not-allowed; }}
  select, input[type=range] {{ background:#1E293B; color:#fff; border:1px solid #475569; padding:6px 10px; border-radius:6px; }}
</style>
</head>
<body>

<div class="top-header">
  <div>
    <h2 style="margin:0;">NASA ACME s-Flame | Gemelo Conceptual Basado en Evidencia y Comparador Contrafactual 3D</h2>
    <div style="color:#94A3B8; font-size:13px; margin-top:4px;">
      Ensayo: <b>20013D1</b> (PSI-23) | Botella: <code>66.7% H2 with CH4</code>
      <span class="badge b-unv">[BASE COMPOSICIONAL NO VERIFICADA]</span>
      <span class="badge b-unv">[CALIBRACIÓN V → kg/s NO VERIFICADA]</span>
    </div>
  </div>
  <div>
    <span class="badge b-obs">OBSERVED #168039</span>
    <span class="badge b-inf">INFERRED (SCM) #B4690E</span>
    <span class="badge b-unv">UNVERIFIED #B22222</span>
  </div>
</div>

<div class="sync-banner">
  <b>🔒 CANDADO DE SINCRONIZACIÓN Y CAMPO DE LLAMA (Puntos 5 y 6):</b>
  {sync_status["sync_warning_message"]}
  <b>[CAMPO 3D DE LLAMA DESACTIVADO: SIN CALIBRACIÓN FÍSICA VERIFICADA]</b>
</div>

<div class="cta-bar">
  <div class="ctrl-row">
    <button class="btn-disabled" disabled>⏹ Play / Animación Continua de Llama (BLOQUEADO)</button>
    <label><b>Selector Discreto de Eventos MFC (1..42):</b>
      <input type="range" id="evtSlider" min="1" max="42" value="12" oninput="updateEventInspector(this.value)">
      <span id="evtLabel" style="font-weight:700; color:#38BDF8;">Evento #12</span>
    </label>
    <label><b>Inspector de Sensor 3D:</b>
      <select id="sensorSelect" onchange="updateSensorInspector(this.value)">
        <option value="TCBurner">TCBurner (r=3.2 mm)</option>
        <option value="TCA">TCA (r=8.0 mm)</option>
        <option value="TCB" selected>TCB (r=15.0 mm)</option>
        <option value="TCC">TCC (r=25.0 mm)</option>
        <option value="PMT3">PMT3 (OH*/CH*)</option>
        <option value="RadiometerCenter">RadiometerCenter (r=154 mm - VERIFIED)</option>
      </select>
    </label>
    <button class="btn-compare" onclick="highlightComparison()">⚡ COMPARE EXPERIMENTAL SCENARIOS</button>
  </div>

  <div class="bounds-box" id="boundsBox">
    <div style="font-size:12px; text-transform:uppercase; color:#FBBF24; letter-spacing:1px;">
      Cotas Contrafactuales Acopladas (Modelo Causal Estructural SCM - IGNIS-μ)
    </div>
    <div class="bounds-eq">44.83% &le; P<sub>&Pi;</sub>(&Delta; &gt; 0) &le; 82.21%</div>
    <div style="font-size:12px; color:#CBD5E1;">
      {bounds["scientific_disclaimer"]}
    </div>
  </div>
</div>

{plotly_div}

<div class="grid-bottom">
  <div class="card card-blue">
    <h3 style="margin-top:0; color:#60A5FA;">
      📘 Panel Izquierdo: Evidencia Experimental (20013D1) <span class="badge b-obs">OBSERVED</span>
    </h3>
    <div id="eventReadout" style="font-size:14px; background:#1E293B; padding:10px; border-radius:6px;"></div>
    <h4 style="margin:12px 0 6px 0;">Inspector de Canal Seleccionado (<span id="inspName">TCB</span>)</h4>
    <div id="sensorReadout" style="font-size:13px; color:#E2E8F0;"></div>
  </div>

  <div class="card card-orange">
    <h3 style="margin-top:0; color:#FBBF24;">
      📙 Panel Derecho: Respuestas Inferidas SCM y Diferencias &Delta; <span class="badge b-inf">INFERRED (SCM)</span>
    </h3>
    <table>
      <thead>
        <tr>
          <th>Sensor 3D</th>
          <th>Unidad Registrada</th>
          <th>Media Obs.</th>
          <th>Media SCM Alt.</th>
          <th>&Delta; Inferido (%)</th>
        </tr>
      </thead>
      <tbody id="scmTableBody"></tbody>
    </table>
  </div>
</div>

<script>
const COMP_DATA = {data_json_str};

function updateEventInspector(evtIdx) {{
  const i = parseInt(evtIdx) - 1;
  const p = COMP_DATA.observed_scenario_blue.mfc_program;
  const pAlt = COMP_DATA.alternative_scenario_orange.mfc_program_alternative;
  document.getElementById('evtLabel').innerText = 'Evento #' + evtIdx + ' (' + p.timestamps_reconstructed[i] + ')';
  document.getElementById('eventReadout').innerHTML =
    '<b>Timestamp Reconstruido:</b> ' + p.timestamps_reconstructed[i] + ' <span class="badge b-unv">TZ NO VERIFICADA</span><br>' +
    '<b>Consigna Observada (Azul):</b> MFC2 = <b>' + p.MFC2_values_V[i].toFixed(4) + ' V</b> | MFC3 = <b>' + p.MFC3_values_V[i].toFixed(4) + ' V</b><br>' +
    '<b>Consigna Alternativa do(·) (Naranja):</b> MFC2 = <b>' + pAlt.MFC2_values_V[i].toFixed(4) + ' V</b> | MFC3 = <b>' + pAlt.MFC3_values_V[i].toFixed(4) + ' V</b>';
}}

function updateSensorInspector(sensorId) {{
  const s = COMP_DATA.observed_scenario_blue.sensor_payloads[sensorId];
  const r = COMP_DATA.alternative_scenario_orange.scm_sensor_responses[sensorId];
  document.getElementById('inspName').innerText = sensorId;
  document.getElementById('sensorReadout').innerHTML =
    '<b>Nombre:</b> ' + s.display_name + '<br>' +
    '<b>Coordenadas 3D [m]:</b> [' + s.coords_3d_m.join(', ') + '] (r = ' + s.radial_distance_m + ' m) | <b>Tier:</b> ' + s.verification_tier + '<br>' +
    '<b>Archivo Origen PSI-23:</b> <code>' + s.psi23_source_file + '</code><br>' +
    '<b>Unidad Registrada:</b> <code>' + s.original_registered_unit + '</code> ' + s.lock_badge + '<br>' +
    '<b>Contraste SCM:</b> Media Obs = ' + r.observed_mean_raw + ' &rarr; Media Alt SCM = ' + r.alternative_inferred_mean_raw +
    ' (<b>&Delta; = ' + (r.relative_delta_pct >= 0 ? '+' : '') + r.relative_delta_pct + '%</b>)';
}}

function populateScmTable() {{
  const tbody = document.getElementById('scmTableBody');
  tbody.innerHTML = '';
  const resps = COMP_DATA.alternative_scenario_orange.scm_sensor_responses;
  Object.keys(resps).forEach(sid => {{
    const r = resps[sid];
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td><b>' + sid + '</b></td>' +
      '<td><code>' + r.unit + '</code></td>' +
      '<td>' + r.observed_mean_raw + '</td>' +
      '<td>' + r.alternative_inferred_mean_raw + '</td>' +
      '<td style="color:#FBBF24; font-weight:700;">' + (r.relative_delta_pct >= 0 ? '+' : '') + r.relative_delta_pct + '%</td>';
    tbody.appendChild(tr);
  }});
}}

function highlightComparison() {{
  const box = document.getElementById('boundsBox');
  box.style.boxShadow = '0 0 28px rgba(251, 191, 36, 0.75)';
  box.style.transform = 'scale(1.02)';
  setTimeout(() => {{ box.style.transform = 'scale(1.0)'; }}, 400);
}}

updateEventInspector(12);
updateSensorInspector('TCB');
populateScmTable();
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return output_html_path


def run_stage2_comparator_pipeline(
    exp_id: str = "20013D1",
    preset_id: str = "ALT_HIGH_DRIVE_STEP",
    output_json_path: str = "output_comparator_contract_20013d1.json",
    output_html_path: str = "output_comparator_20013d1.html"
) -> Dict[str, Any]:
    alt_prog = ALTERNATIVE_PROGRAMS_PRESETS.get(preset_id, ALTERNATIVE_PROGRAMS_PRESETS["ALT_HIGH_DRIVE_STEP"])
    payload = evaluate_counterfactual_comparison(exp_id=exp_id, alt_mfc_program=alt_prog)

    os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    html_out = build_split_screen_comparator_html(payload, output_html_path=output_html_path)
    print(f"comparator_3d_ui.py OK | JSON: {output_json_path} | HTML Split-Screen: {html_out}")
    return payload


if __name__ == "__main__":
    run_stage2_comparator_pipeline()