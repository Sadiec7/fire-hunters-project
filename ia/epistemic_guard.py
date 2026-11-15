"""
ia/epistemic_guard.py
Semáforo Epistémico unificado (OBSERVED / INFERRED / UNVERIFIED), Candado contra Llamas 3D Falsas
y Auditor de Sincronización Temporal para NASA ACME s-Flame 20013D1 (Puntos 5 y 6).
"""

from typing import Dict, Any

EPISTEMIC_COLORS_HEX: Dict[str, Dict[str, str]] = {
    "OBSERVED": {
        "hex": "#168039",
        "color_hex": "#168039",
        "label_es": "OBSERVADO (Evidencia Directa PSI-23)",
        "description": "Voltajes MFC registrados, geometría verificada del quemador (r_b=3.18 mm) y radiómetro (154 mm).",
    },
    "INFERRED": {
        "hex": "#B4690E",
        "color_hex": "#B4690E",
        "label_es": "INFERIDO (Modelo Causal Estructural SCM)",
        "description": "Respuestas contrafactuales delta y cotas acopladas 44.83% <= P_Pi(Delta > 0) <= 82.21%.",
    },
    "UNVERIFIED": {
        "hex": "#B22222",
        "color_hex": "#B22222",
        "label_es": "NO VERIFICADO (Bloqueado / Pendiente de Calibración)",
        "description": "Conversión V->kg/s, calibración mV->K, sincronización temporal MFC-sensores y campo 3D de llama.",
    },
}

EPISTEMIC_PALETTE = EPISTEMIC_COLORS_HEX


def allow_3d_flame_isosurface(exp_id: str) -> bool:
    if "20013D1" in str(exp_id).upper():
        return False
    return True


def get_flame_field_lock_banner(exp_id: str = "20013D1") -> Dict[str, Any]:
    allowed = allow_3d_flame_isosurface(exp_id)
    return {
        "experiment_id": exp_id,
        "allow_3d_flame_isosurface": allowed,
        "replacement_geometry": "CONCEPTUAL_BOUNDARY_WIREFRAME_SPHERE" if not allowed else "3D_ISOSURFACE",
        "badge_color_hex": "#B22222" if not allowed else "#168039",
        "banner_text": (
            "[CAMPO 3D DE LLAMA DESACTIVADO: SIN CALIBRACIÓN FÍSICA VERIFICADA]"
            if not allowed else "[CAMPO 3D HABILITADO]"
        ),
    }


def classify_epistemic_element(element_key: str, exp_id: str = "20013D1") -> Dict[str, str]:
    key_u = element_key.upper()
    if any(k in key_u for k in ("MFC2_V", "MFC3_V", "BURNER_SPHERE", "RADIOMETER_CENTER", "OBSERVED")):
        tag = "OBSERVED"
    elif any(k in key_u for k in ("SCM", "COUNTERFACTUAL", "DELTA", "COUPLING_BOUNDS", "ALTERNATIVE", "INFERRED")):
        tag = "INFERRED"
    else:
        tag = "UNVERIFIED"

    info = EPISTEMIC_COLORS_HEX[tag]
    return {
        "element_key": element_key,
        "epistemic_tag": tag,
        "color_hex": info["hex"],
        "badge_label": info["label_es"],
        "explanation": info["description"],
    }


def classify_epistemic_status(item_type: str, is_calibrated: bool = False, is_scm_output: bool = False) -> Dict[str, Any]:
    if is_scm_output:
        tag = "INFERRED"
    elif is_calibrated or item_type in ("RAW_VOLTAGE_SIGNAL", "VERIFIED_HARDWARE_DIM"):
        tag = "OBSERVED"
    else:
        tag = "UNVERIFIED"
    return {"epistemic_tag": tag, **EPISTEMIC_COLORS_HEX[tag]}


def audit_temporal_alignment(exp_id: str = "20013D1") -> Dict[str, Any]:
    is_20013d1 = "20013D1" in str(exp_id).upper()
    return {
        "experiment_id": exp_id,
        "mfc_timestamps_status": "RECONSTRUCTED_FROM_LOG",
        "timezone_verified": False,
        "sensor_mfc_alignment_verified": not is_20013d1,
        "allow_realtime_combustion_playback": not is_20013d1,
        "allowed_ui_timeline_mode": "DISCRETE_MFC_EVENT_INSPECTOR_ONLY (Events 1..42)",
        "sync_warning_message": (
            "Las marcas temporales de los MFC son reconstruidas y su correspondencia exacta con "
            "las señales instrumentales no está verificada. Se prohíbe animar la evolución como "
            "reproducción física continua de la combustión."
        ),
    }


if __name__ == "__main__":
    print("epistemic_guard.py OK | allow_3d_flame_isosurface('20013D1') =", allow_3d_flame_isosurface("20013D1"))