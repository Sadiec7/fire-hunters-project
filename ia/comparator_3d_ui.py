# -*- coding: utf-8 -*-
"""
ia/comparator_3d_ui.py
Interfaz Interactiva Split-Screen del Comparador Experimental Contrafactual 3D (NASA 20013D1).
Cubre Puntos 2.R, 3.R, 4.R, 5.R, 6.R, 7.R y genera también el Reporte Técnico del Punto 7.A.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_bridge_20013d1 import load_experiment_package_20013d1  # type: ignore
    from sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS  # type: ignore
    from epistemic_guard import get_epistemic_locks_20013d1  # type: ignore
    from time_sync_auditor import audit_temporal_alignment  # type: ignore
    from scm_counterfactual_bridge import evaluate_counterfactual_comparison  # type: ignore
    from scene_3d_acme import build_acme_evidence_3d_figure, REQUIRED_SUB_MESH_NAMES  # type: ignore
except ImportError:
    from ia.data_bridge_20013d1 import load_experiment_package_20013d1
    from ia.sensor_registry_20013d1 import get_all_sensors_registry_20013d1, MANDATORY_SENSOR_IDS
    from ia.epistemic_guard import get_epistemic_locks_20013d1
    from ia.time_sync_auditor import audit_temporal_alignment
    from ia.scm_counterfactual_bridge import evaluate_counterfactual_comparison
    from ia.scene_3d_acme import build_acme_evidence_3d_figure, REQUIRED_SUB_MESH_NAMES


def generate_stage2_technical_validation_report_md(
    output_md_path: Optional[str] = None
) -> str:
    """
    TAREA 7.A (Documento Técnico de Validación y Honestidad Científica):
    Clasifica rigurosamente cada componente del Gemelo Conceptual Basado en Evidencia en:
      (1) Partes verificadas experimentalmente (VERIFIED_DIMENSION / OBSERVED),
      (2) Aproximaciones geométricas y estructurales (GEOMETRIC_APPROXIMATION / INFERRED), y
      (3) Elementos que no representan simulaciones físicas directas (ILLUSTRATIVE_ONLY / UNVERIFIED).
    """
    if output_md_path is None:
        output_md_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "STAGE2_VALIDATION_REPORT_20013D1.md"
        )

    md_content = """# Documento Técnico de Validación y Honestidad Científica — Etapa 2 (Ensayo NASA `20013D1`)
**Proyecto NASA Space Apps:** Flame in Freefall (ACME s-Flame $\\leftrightarrow$ IGNIS-$\\mu$)  
**Responsables de Ingeniería (`ia/`):** Ángel ("Lito" / "Perrita") & Rodolfo ("Tornolfo")  
**Identificador del Ensayo Auditado:** `20013D1` (Repositorio NASA PSI-23 / `ACME_S_FLAME_PSI23`)

---

## 1. Clasificación Rigurosa de Componentes del Gemelo Conceptual 3D

| Componente / Sub-malla / Canal | Categoría Normativa (`verification_tier`) | Semáforo Epistémico | Soporte Documental y Alcance Científico |
| :--- | :--- | :--- | :--- |
| **`mesh_burner_sphere`** (Quemador poroso esférico) | `VERIFIED_DIMENSION` | 🟢 `OBSERVED` (`#168039`) | Esfera de acero inoxidable sinterizado con radio verificado $r_b = 0.00318\\text{ m}$ ($6.35\\text{ mm}$ de diámetro) y tubo de soporte de $0.0016\\text{ m}$. |
| **`mesh_radiometer_center`** (`RadiometerCenter`) | `VERIFIED_DIMENSION` | 🟢 `OBSERVED` (`#168039`) | Radiómetro termopila Schmidt-Boelter ubicado a distancia radial nominal verificada $r = 0.154\\text{ m}$ ($154\\text{ mm}$). Señal cruda en `mV_raw_irradiance` (`20013D1_data.csv`). |
| **`mesh_tc_rake`** (`TCBurner`, `TCA`, `TCB`, `TCC`) | `GEOMETRIC_APPROXIMATION` | 🟢 `OBSERVED` (`#168039`) | Coordenadas 3D conceptuales del rastrillo de termopares ($r \\approx 3.2, 8, 15, 25\\text{ mm}$). Señales crudas verificadas en `mV_raw` sin conversión a Kelvin `[K]`. |
| **`mesh_pmt3`** (`PMT3` $\\mathrm{OH^*/CH^*}$) | `GEOMETRIC_APPROXIMATION` | 🟢 `OBSERVED` (`#168039`) | Posición angular aproximada del tubo fotomultiplicador ($r \\approx 0.125\\text{ m}$). Señal cruda registrada en `V_raw_counts` (`20013D1_data.csv`). |
| **`mesh_gas_inlet_mfc2` / `mfc3`** (`MFC2`, `MFC3`) | `GEOMETRIC_APPROXIMATION` | 🟢 `OBSERVED` (`#168039`) | Líneas esquemáticas de alimentación de gas. Las 42 consignas en `20013D1_mfcSetpoints.csv` se conservan en Voltios `[V]` con candado activo `[CALIBRACIÓN V -> kg/s NO VERIFICADA]`. |
| **Gravedad Residual ($g_{\\mathrm{res}}$)** | `GEOMETRIC_APPROXIMATION` | 🟢 `OBSERVED` (`#168039`) | Orden de magnitud documentado para el rack CIR en la ISS: $g_{\\mathrm{res}} \\approx 1.0 \\times 10^{-4}\\text{ m/s}^2$. |
| **Respuestas Contrafactuales SCM y Cotas $P_{\\Pi}(\\Delta > 0)$** | `STRUCTURAL_CAUSAL_MODEL` | 🟡 `INFERRED` (`#B4690E`) | Diferencias $\\Delta$ inferidas por el SCM de IGNIS-$\\mu$ y cotas acopladas $44.83\\% \\le P_{\\Pi}(\\Delta > 0) \\le 82.21\\%$ con `causal_effect_identified = False`. |
| **`mesh_cir_housing`** (Carcasa exterior CIR) | `ILLUSTRATIVE_ONLY` | 🔴 `UNVERIFIED` (`#6C757D`) | Geometría envolvente meramente ilustrativa para orientación espacial; no interviene en ningún cálculo físico ni probabilístico. |
| **Esfera Wireframe de Bloqueo de Llama 3D** | `NON_SIMULATED_GUARD` | 🔴 `UNVERIFIED` (`#B22222`) | En el ensayo `20013D1` (`66.7% H2 with CH4`, `composition_basis_verified = False`), queda prohibido renderizar campos 3D continuos de temperatura o bolas de fuego. |

---

## 2. Candados Epistémicos y de Sincronización Activos en Código

1. **Bloqueo de Conversión $\\mathrm{V} \\to \\mathrm{kg/s}$ y $\\mathrm{mV} \\to \\mathrm{K}$ (`data_bridge_20013d1.py`):** La función `enforce_calibration_lock()` impide transformar los 42 eventos en voltios de `MFC2`/`MFC3` a caudales másicos y prohíbe etiquetar las señales crudas de `TCBurner`, `TCA`, `TCB` y `TCC` como temperaturas físicas en Kelvin `[K]`.
2. **Bloqueo de Animación Continua (`time_sync_auditor.py`):** Dado que `mfc_timestamps_status = "RECONSTRUCTED_FROM_LOG"` y `sensor_mfc_alignment_verified = False`, el indicador `allow_realtime_combustion_playback` permanece en `False`, habilitando exclusivamente la inspección discreta de los 42 eventos MFC y gráficas con ejes temporales independientes.
3. **Honestidad Causal (`scm_counterfactual_bridge.py`):** El comparador declara explícitamente `causal_effect_identified = False` y advierte que el intervalo $44.83\\% \\le P_{\\Pi}(\\Delta > 0) \\le 82.21\\%$ representa cotas de acoplamiento sobre distribuciones observacionales bajo supuestos estructurales del SCM, y no probabilidades físicas directas de incendio.
"""
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return output_md_path


def build_split_screen_comparator_html(
    output_html_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    TAREAS 2.R, 3.R, 4.R, 5.R, 6.R y 7.R:
    Genera la interfaz Split-Screen completa en HTML5 + Plotly.js con:
      - Panel Izquierdo Azul (Escenario Observado - Evidencia NASA 20013D1, etiqueta OBSERVED #168039)
      - Panel Derecho Naranja (Escenario Alternativo - Inferencia SCM IGNIS-mu, etiqueta INFERRED #B4690E)
      - Botón Central 'COMPARE EXPERIMENTAL SCENARIOS' con recuadro 44.83% <= P_Pi(Delta > 0) <= 82.21%
      - Selector Discreto de los 42 Eventos MFC en Voltios [V] (botón Play continuo deshabilitado)
      - Inspector de Canales interactivo para TCBurner, TCA, TCB, TCC, PMT3, RadiometerCenter, MFC2 y MFC3.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if output_html_path is None:
        output_html_path = os.path.join(base_dir, "output_comparator_split_screen_20013d1.html")

    comp_data = evaluate_counterfactual_comparison("20013D1")
    sensors_reg = get_all_sensors_registry_20013d1()
    report_md_path = generate_stage2_technical_validation_report_md()

    fig_obs = build_acme_evidence_3d_figure("OBSERVED", comp_data)
    fig_alt = build_acme_evidence_3d_figure("ALTERNATIVE", comp_data)

    fig_obs_json = fig_obs.to_json()
    fig_alt_json = fig_alt.to_json()
    comp_json_str = json.dumps(comp_data, ensure_ascii=False)
    sensors_json_str = json.dumps(sensors_reg, ensure_ascii=False)

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>IGNIS-μ & ACME s-Flame (20013D1) — Comparador Experimental Contrafactual 3D</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: #070B19; color: #E6EDF3; padding: 14px; }}
    .top-header {{
      display: flex; justify-content: space-between; align-items: center;
      background: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 12px 18px; margin-bottom: 12px;
    }}
    .traffic-lights {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .badge {{ padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; letter-spacing: 0.4px; }}
    .badge-obs {{ background: #168039; color: #FFFFFF; border: 1px solid #2EA043; }}
    .badge-inf {{ background: #B4690E; color: #FFFFFF; border: 1px solid #D98218; }}
    .badge-unv {{ background: #B22222; color: #FFFFFF; border: 1px solid #F85149; }}
    .sync-banner {{
      background: rgba(178, 34, 34, 0.22); border: 1px solid #B22222; color: #FFDAD6;
      padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; font-size: 13px;
      display: flex; justify-content: space-between; align-items: center; gap: 12px;
    }}
    .btn-disabled {{
      background: #334155; color: #94A3B8; border: 1px solid #475569; padding: 6px 12px;
      border-radius: 6px; cursor: not-allowed; font-weight: 600; font-size: 12px;
    }}
    .center-action-bar {{
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      background: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 14px; margin-bottom: 14px;
    }}
    .btn-compare {{
      background: linear-gradient(90deg, #0D47A1 0%, #E65100 100%);
      color: #FFFFFF; border: 2px solid #F59E0B; padding: 12px 28px; border-radius: 8px;
      font-size: 15px; font-weight: 800; cursor: pointer; letter-spacing: 0.8px;
      box-shadow: 0 4px 16px rgba(230, 81, 0, 0.35); transition: transform 0.15s ease;
    }}
    .btn-compare:hover {{ transform: scale(1.02); }}
    .bounds-card {{
      margin-top: 12px; background: rgba(180, 105, 14, 0.18); border: 2px solid #B4690E;
      border-radius: 8px; padding: 12px 22px; text-align: center; max-width: 920px; display: block;
    }}
    .bounds-math {{ font-size: 22px; font-weight: 800; color: #FBBF24; margin: 4px 0; }}
    .bounds-disclaimer {{ font-size: 12px; color: #E2E8F0; line-height: 1.4; }}
    .split-screen-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px;
    }}
    .scenario-panel {{
      background: #0B132B; border-radius: 10px; padding: 12px;
    }}
    .panel-blue {{ border: 2px solid #1E88E5; }}
    .panel-orange {{ border: 2px solid #FB8C00; }}
    .panel-header {{
      display: flex; justify-content: space-between; align-items: center;
      padding-bottom: 8px; margin-bottom: 8px; border-bottom: 1px solid #1E293B;
    }}
    .viewport-3d {{ width: 100%; height: 430px; border-radius: 8px; overflow: hidden; }}
    .bottom-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .card-box {{
      background: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 14px;
    }}
    .controls-row {{ display: flex; gap: 12px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }}
    select, input[type=range] {{
      background: #1E293B; color: #F8FAFC; border: 1px solid #475569; padding: 6px 10px; border-radius: 6px;
    }}
    .plot-2d {{ width: 100%; height: 290px; }}
    .meta-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
    .meta-table th, .meta-table td {{
      border: 1px solid #1E293B; padding: 6px 8px; text-align: left;
    }}
    .meta-table th {{ background: #1E293B; color: #93C5FD; }}
  </style>
</head>
<body>

  <div class="top-header">
    <div>
      <h2 style="font-size:18px;">🚀 NASA ACME s-Flame (Ensayo 20013D1) — Gemelo Conceptual Basado en Evidencia & Comparador Contrafactual 3D</h2>
      <div style="font-size:12px; color:#94A3B8; margin-top:3px;">
        Botella registrada: <b>66.7% H2 with CH4</b> (composition_basis_verified = False) | Gravedad residual: g_res ≈ 1.0e-4 m/s²
      </div>
    </div>
    <div class="traffic-lights">
      <span class="badge badge-obs">🟢 OBSERVADO (#168039)</span>
      <span class="badge badge-inf">🟡 INFERIDO SCM (#B4690E)</span>
      <span class="badge badge-unv">🔴 NO VERIFICADO (#B22222)</span>
    </div>
  </div>

  <!-- PUNTO 6: Banner de Sincronización Experimental y Bloqueo de Animación Falsa -->
  <div class="sync-banner">
    <div>
      <b>⚠️ BLOQUEO DE SINCRONIZACIÓN TEMPORAL (Punto 6):</b>
      Las marcas temporales de los 42 eventos MFC son reconstruidas (<code>RECONSTRUCTED_FROM_LOG</code>) y su alineación con las señales de los sensores no está verificada (<code>sensor_mfc_alignment_verified = False</code>). Se prohíbe animar la evolución como reproducción física continua.
    </div>
    <button class="btn-disabled" disabled title="Deshabilitado por time_sync_auditor.py">
      ⏹ Play Animación Continua de Llama [BLOQUEADO]
    </button>
  </div>

  <!-- PUNTO 4 Y 7: Botón Central COMPARE EXPERIMENTAL SCENARIOS + Cotas Acopladas -->
  <div class="center-action-bar">
    <button class="btn-compare" onclick="runCounterfactualComparison()">
      🔥 COMPARE EXPERIMENTAL SCENARIOS (20013D1 OBSERVED vs. SCM ALTERNATIVE)
    </button>
    <div id="boundsCard" class="bounds-card">
      <div style="font-size:12px; font-weight:700; color:#FDE68A;">
        COTAS CONTRAFACTUALES DE ACOPLAMIENTO (MODELO CAUSAL ESTRUCTURAL IGNIS-μ) — [🟡 INFERRED]
      </div>
      <div class="bounds-math">
        44.83% &le; P<sub>&Pi;</sub>(&Delta; &gt; 0) &le; 82.21%
      </div>
      <div class="bounds-disclaimer">
        <b>causal_effect_identified = False:</b> Cotas de acoplamiento sobre distribuciones observacionales dependientes de supuestos estructurales del SCM. No representan probabilidades físicas directas de incendio ni efectos causales físicos identificados.
      </div>
    </div>
  </div>

  <!-- PUNTO 7: Vista Doble Split-Screen 3D -->
  <div class="split-screen-grid">
    <div class="scenario-panel panel-blue">
      <div class="panel-header">
        <div>
          <strong style="color:#60A5FA;">🔵 PANEL IZQUIERDO: ESCENARIO OBSERVADO (NASA 20013D1)</strong>
          <div style="font-size:11px; color:#94A3B8;">Consignas originales MFC2/MFC3 [V] + 6 Sensores registrados en PSI-23</div>
        </div>
        <span class="badge badge-obs">🟢 OBSERVED</span>
      </div>
      <div id="scene3dObserved" class="viewport-3d"></div>
    </div>

    <div class="scenario-panel panel-orange">
      <div class="panel-header">
        <div>
          <strong style="color:#FBBF24;">🟠 PANEL DERECHO: ESCENARIO ALTERNATIVO (SCM IGNIS-μ)</strong>
          <div style="font-size:11px; color:#94A3B8;">Intervención: do(MFC2_V = 1.14·V_obs, MFC3_V = 0.92·V_obs) | Halos 3D ∝ |&Delta;|</div>
        </div>
        <span class="badge badge-inf">🟡 INFERRED (SCM)</span>
      </div>
      <div id="scene3dAlternative" class="viewport-3d"></div>
    </div>
  </div>

  <!-- PUNTOS 2, 3 Y 6: Selector de los 42 Eventos MFC en Voltios [V] + Inspector de los 6 Canales -->
  <div class="bottom-grid">
    <div class="card-box">
      <div class="controls-row" style="justify-content:space-between;">
        <strong>📊 Programa de 42 Eventos Reconstruidos MFC2 / MFC3 (Estrictamente en Voltios [V])</strong>
        <span class="badge badge-unv">[CALIBRACIÓN V &rarr; kg/s NO VERIFICADA]</span>
      </div>
      <div class="controls-row">
        <label for="eventSlider" style="font-size:13px;">Selector Discreto de Evento MFC (1 al 42):</label>
        <input type="range" id="eventSlider" min="1" max="42" value="18" oninput="updateMfcEvent(this.value)" />
        <span id="eventLabel" style="font-size:13px; font-weight:700; color:#38BDF8;">Evento #18</span>
      </div>
      <div id="mfcStepPlot" class="plot-2d"></div>
    </div>

    <div class="card-box">
      <div class="controls-row" style="justify-content:space-between;">
        <div>
          <strong>🔎 Inspector de Instrumentación y Respuesta Contrafactual (&Delta; SCM)</strong>
        </div>
        <div>
          <label for="sensorSelect" style="font-size:12px;">Canal seleccionado:</label>
          <select id="sensorSelect" onchange="updateSensorInspector(this.value)">
            <option value="TCA">TCA (Termopar r ~ 8 mm)</option>
            <option value="TCBurner">TCBurner (Termopar Quemador r ~ 3.2 mm)</option>
            <option value="TCB">TCB (Termopar r ~ 15 mm)</option>
            <option value="TCC">TCC (Termopar r ~ 25 mm)</option>
            <option value="PMT3">PMT3 (Quimioluminiscencia OH*/CH*)</option>
            <option value="RadiometerCenter">RadiometerCenter (Schmidt-Boelter r = 154 mm)</option>
          </select>
        </div>
      </div>
      <div id="sensorPlot" class="plot-2d"></div>
      <table class="meta-table">
        <thead>
          <tr>
            <th>Canal</th>
            <th>Archivo PSI-23</th>
            <th>Unidad Original</th>
            <th>Estado Verificación</th>
            <th>&Delta; Medio SCM</th>
          </tr>
        </thead>
        <tbody id="sensorMetaBody"></tbody>
      </table>
    </div>
  </div>

<script>
  const COMP_DATA = {comp_json_str};
  const SENSORS_REG = {sensors_json_str};
  const FIG_OBS = {fig_obs_json};
  const FIG_ALT = {fig_alt_json};

  Plotly.newPlot('scene3dObserved', FIG_OBS.data, FIG_OBS.layout, {{responsive: true}});
  Plotly.newPlot('scene3dAlternative', FIG_ALT.data, FIG_ALT.layout, {{responsive: true}});

  // Clic en cualquier nodo 3D de sensor abre su canal en el Inspector (Tarea 3.R)
  ['scene3dObserved', 'scene3dAlternative'].forEach(divId => {{
    const el = document.getElementById(divId);
    el.on('plotly_click', function(data) {{
      if (data.points && data.points.length > 0) {{
        const pt = data.points[0];
        if (pt.customdata && pt.customdata[0] && SENSORS_REG[pt.customdata[0]]) {{
          const sId = pt.customdata[0];
          if (['TCBurner','TCA','TCB','TCC','PMT3','RadiometerCenter'].includes(sId)) {{
            document.getElementById('sensorSelect').value = sId;
            updateSensorInspector(sId);
          }}
        }}
      }}
    }});
  }});

  function renderMfcProgramPlot(selectedEventIdx) {{
    const evsObs = COMP_DATA.observed_scenario_blue.mfc_program.events_table;
    const evsAlt = COMP_DATA.alternative_scenario_orange.mfc_program_alternative.events_table;
    const idxArr = evsObs.map(e => e.event_index);
    const mfc2Obs = evsObs.map(e => e.MFC2_setpoint_V);
    const mfc3Obs = evsObs.map(e => e.MFC3_setpoint_V);
    const mfc2Alt = evsAlt.map(e => e.MFC2_setpoint_V);
    const mfc3Alt = evsAlt.map(e => e.MFC3_setpoint_V);

    const traces = [
      {{ x: idxArr, y: mfc2Obs, mode: 'lines+markers', line: {{shape: 'hv', color: '#38BDF8', width: 2}}, name: 'MFC2 Observado [V]' }},
      {{ x: idxArr, y: mfc3Obs, mode: 'lines+markers', line: {{shape: 'hv', color: '#168039', width: 2}}, name: 'MFC3 Observado [V]' }},
      {{ x: idxArr, y: mfc2Alt, mode: 'lines', line: {{shape: 'hv', color: '#F59E0B', width: 2, dash: 'dot'}}, name: 'MFC2 Alternativo SCM [V]' }},
      {{ x: idxArr, y: mfc3Alt, mode: 'lines', line: {{shape: 'hv', color: '#EA580C', width: 2, dash: 'dot'}}, name: 'MFC3 Alternativo SCM [V]' }}
    ];

    const layout = {{
      paper_bgcolor: '#0F172A', plot_bgcolor: '#0F172A',
      font: {{ color: '#E2E8F0', size: 11 }},
      margin: {{ l: 48, r: 16, t: 24, b: 38 }},
      xaxis: {{ title: 'Índice de Evento Reconstruido (1 a 42)', gridcolor: '#1E293B' }},
      yaxis: {{ title: 'Consigna MFC [Voltios V]', gridcolor: '#1E293B' }},
      shapes: [{{
        type: 'line', x0: selectedEventIdx, x1: selectedEventIdx, y0: 0, y1: 4.2,
        line: {{ color: '#F43F5E', width: 2, dash: 'dash' }}
      }}],
      legend: {{ orientation: 'h', y: 1.14 }}
    }};
    Plotly.react('mfcStepPlot', traces, layout, {{responsive: true}});
  }}

  function updateMfcEvent(val) {{
    const idx = parseInt(val, 10);
    const ev = COMP_DATA.observed_scenario_blue.mfc_program.events_table[idx - 1];
    document.getElementById('eventLabel').innerText =
      `Evento #${{idx}} (t_rec=${{ev.reconstructed_time_s}} s | MFC2=${{ev.MFC2_setpoint_V}} V, MFC3=${{ev.MFC3_setpoint_V}} V | ${{ev.operational_phase}})`;
    renderMfcProgramPlot(idx);
  }}

  function updateSensorInspector(sensorId) {{
    const obs = SENSORS_REG[sensorId];
    const scm = COMP_DATA.alternative_scenario_orange.scm_sensor_responses[sensorId];

    const traces = [
      {{
        x: obs.time_s, y: obs.raw_signal_values,
        mode: 'lines', name: `${{sensorId}} Observado (🟢 OBSERVED)`,
        line: {{ color: '#168039', width: 2.5 }}
      }},
      {{
        x: obs.time_s, y: scm.inferred_series_raw,
        mode: 'lines', name: `${{sensorId}} Inferido SCM (🟡 INFERRED)`,
        line: {{ color: '#F59E0B', width: 2.5, dash: 'dash' }}
      }}
    ];

    const layout = {{
      title: {{ text: `${{obs.label}} — Señal Cruda [${{obs.original_unit}}] (Eje Temporal Independiente DAQ)`, font: {{size: 12, color: '#F8FAFC'}} }},
      paper_bgcolor: '#0F172A', plot_bgcolor: '#0F172A',
      font: {{ color: '#E2E8F0', size: 11 }},
      margin: {{ l: 54, r: 16, t: 32, b: 38 }},
      xaxis: {{ title: 'Tiempo Adquisición Instrumental DAQ [s]', gridcolor: '#1E293B' }},
      yaxis: {{ title: `Señal Cruda [${{obs.original_unit}}]`, gridcolor: '#1E293B' }},
      legend: {{ orientation: 'h', y: 1.14 }}
    }};
    Plotly.react('sensorPlot', traces, layout, {{responsive: true}});

    document.getElementById('sensorMetaBody').innerHTML = `
      <tr>
        <td><b>${{sensorId}}</b></td>
        <td><code>${{obs.source_file_psi23}}</code></td>
        <td><code>${{obs.original_unit}}</code></td>
        <td><span class="badge badge-unv" style="font-size:10px;">${{obs.raw_signal_status}} / ${{obs.unit_verification_status}}</span></td>
        <td style="color:#FBBF24; font-weight:700;">${{scm.delta_mean_raw >= 0 ? '+' : ''}}${{scm.delta_mean_raw}} ${{obs.original_unit}} (${{scm.delta_relative_pct}}%)</td>
      </tr>
    `;
  }}

  function runCounterfactualComparison() {{
    const card = document.getElementById('boundsCard');
    card.style.borderColor = '#FBBF24';
    card.style.boxShadow = '0 0 22px rgba(251, 191, 36, 0.45)';
    updateSensorInspector(document.getElementById('sensorSelect').value);
  }}

  updateMfcEvent(18);
  updateSensorInspector('TCA');
</script>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return {
        "status": "STAGE2_COMPARATOR_READY",
        "experiment_id": "20013D1",
        "html_split_screen_path": output_html_path,
        "technical_report_md_path": report_md_path,
        "sub_meshes_verified": REQUIRED_SUB_MESH_NAMES,
        "coupling_bounds": comp_data["alternative_scenario_orange"]["counterfactual_coupling_bounds"],
    }


if __name__ == "__main__":
    print("=== PRUEBA FINAL ETAPA 2 - COMPARADOR EXPERIMENTAL 3D (ia/comparator_3d_ui.py) ===")
    summary = build_split_screen_comparator_html()
    print(f"[OK] Estado General            : {summary['status']} (Ensayo {summary['experiment_id']})")
    print(f"[OK] Dashboard Split-Screen 3D : {summary['html_split_screen_path']}")
    print(f"[OK] Reporte Técnico Punto 7.A : {summary['technical_report_md_path']}")
    print(f"[OK] Sub-mallas 3D Incluidas   : {len(summary['sub_meshes_verified'])} -> {summary['sub_meshes_verified']}")
    print(f"[OK] Cotas Contrafactuales SCM : {summary['coupling_bounds']['equation_latex']}")