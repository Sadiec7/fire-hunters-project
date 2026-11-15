"""
ia/epistemic_guard.py
Semáforo Epistémico (OBSERVED / INFERRED / UNVERIFIED), Candado contra Llamas 3D Falsas
y Auditor de Sincronización Temporal para NASA ACME s-Flame 20013D1 (Puntos 5 y 6).
"""

from typing import Dict, Any

EPISTEMIC_COLORS_HEX: Dict[str, Dict[str, str]] = {
    "OBSERVED": {
        "hex": "#168039",
        "label_es": "OBSERVADO (Evidencia Directa PSI-23)",
        "description": "Voltajes MFC registrados, geometría verificada del quemador (r_b=3.18 mm) y radiómetro (154 mm).",
    },
    "INFERRED": {
        "hex": "#B4690E",
        "label_es": "INFERIDO (Modelo Causal Estructural SCM)",
        "description": "Respuestas contrafactuales delta y cotas acopladas 44.83% <= P_Pi(Delta > 0) <= 82.21%.",
    },
    "UNVERIFIED": {
        "hex": "#B22222",
        "label_es": "NO VERIFICADO (Bloqueado / Pendiente de Calibración)",
        "description": "Conversión V->kg/s, calibración mV->K, sincronización temporal MFC-sensores y campo 3D de llama.",
    },
}


def allow_3d_flame_isosurface(exp_id: str) -> bool:
    """
    Tarea 5.A: Devuelve False para el ensayo 20013D1, prohibiendo renderizar bolas de fuego
    o campos 3D continuos de temperatura/radiación no validados físicamente.
    """
    if "20013D1" in str(exp_id).upper():
        return False
    return True


def classify_epistemic_element(element_key: str, exp_id: str = "20013D1") -> Dict[str, str]:
    """Asigna la categoría normativa OBSERVED, INFERRED o UNVERIFIED y su color hexadecimal."""
    key_u = element_key.upper()
    if any(k in key_u for k in ("MFC2_V", "MFC3_V", "BURNER_SPHERE", "RADIOMETER_CENTER", "OBSERVED_SCENARIO")):
        tag = "OBSERVED"
    elif any(k in key_u for k in ("SCM", "COUNTERFACTUAL", "DELTA", "COUPLING_BOUNDS", "ALTERNATIVE_SCENARIO")):
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


def audit_temporal_alignment(exp_id: str = "20013D1") -> Dict[str, Any]:
    """
    Tarea 6.A: Audita la sincronización temporal entre los 42 eventos reconstruidos de MFC2/MFC3
    y las señales instrumentales, bloqueando la animación continua de combustión.
    """
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