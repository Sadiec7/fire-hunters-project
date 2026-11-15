# -*- coding: utf-8 -*-
"""
ia/epistemic_guard.py
Semáforo Epistémico (OBSERVED / INFERRED / UNVERIFIED) y Candado de Llama 3D (Punto 5 - Tarea 5.A).
Proyecto NASA Space Apps: Flame in Freefall (ACME s-Flame / IGNIS-mu - Etapa 2).
"""

from typing import Dict, Any

EPISTEMIC_PALETTE: Dict[str, Dict[str, str]] = {
    "OBSERVED": {
        "tag": "OBSERVED",
        "label_es": "OBSERVADO (EVIDENCIA EXPERIMENTAL PSI-23)",
        "color_hex": "#168039",
        "border_hex": "#1E9E49",
        "description": (
            "Información obtenida directamente de los registros de NASA PSI-23 "
            "(voltajes MFC registrados, señales crudas de los 6 sensores, radio del quemador r_b = 3.18 mm, "
            "distancia radial del radiómetro r = 154 mm)."
        ),
    },
    "INFERRED": {
        "tag": "INFERRED",
        "label_es": "INFERIDO (MODELO CAUSAL ESTRUCTURAL SCM IGNIS-mu)",
        "color_hex": "#B4690E",
        "border_hex": "#D98218",
        "description": (
            "Resultados calculados por el modelo estadístico o causal estructural (SCM) de IGNIS-mu "
            "para escenarios alternativos y las cotas de acoplamiento 44.83% <= P_Pi(Delta > 0) <= 82.21%."
        ),
    },
    "UNVERIFIED": {
        "tag": "UNVERIFIED",
        "label_es": "NO VERIFICADO (CANDADO EPISTÉMICO ACTIVO)",
        "color_hex": "#B22222",
        "border_hex": "#DC3545",
        "description": (
            "Configuraciones sin soporte suficiente: calibraciones V -> kg/s o mV -> K pendientes, "
            "base composicional no verificada de la botella '66.7% H2 with CH4' y campos 3D continuos "
            "de llama/temperatura no validados físicamente."
        ),
    },
}


def allow_3d_flame_isosurface(exp_id: str) -> bool:
    """
    TAREA 5.A (Candado de Superficie de Llama 3D):
    Devuelve False obligatoriamente para el ensayo '20013D1', impidiendo que el visor 3D
    renderice bolas de fuego volumétricas o campos de temperatura continuos no validados.
    """
    clean_id = str(exp_id or "").strip().upper()
    if "20013D1" in clean_id:
        return False
    return True


def classify_epistemic_item(item_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asigna automáticamente la etiqueta normativa del Semáforo Epistémico
    ('OBSERVED', 'INFERRED' o 'UNVERIFIED') junto con su código de color hexadecimal.
    """
    kind = str(item_type).strip().upper()

    if kind in ("RAW_SENSOR_SERIES", "MFC_VOLTAGE_PROGRAM", "VERIFIED_HARDWARE_DIMENSION"):
        tier_info = EPISTEMIC_PALETTE["OBSERVED"]
    elif kind in ("SCM_COUNTERFACTUAL_RESPONSE", "COUPLING_BOUNDS_SCM", "BAYESIAN_INFERENCE"):
        tier_info = EPISTEMIC_PALETTE["INFERRED"]
    elif kind in ("UNTOUCHED_CALIBRATION_SI", "UNVERIFIED_BOTTLE_COMPOSITION", "CONTINUOUS_3D_FLAME_FIELD"):
        tier_info = EPISTEMIC_PALETTE["UNVERIFIED"]
    else:
        explicit_tag = str(metadata.get("epistemic_tag", "UNVERIFIED")).upper()
        tier_info = EPISTEMIC_PALETTE.get(explicit_tag, EPISTEMIC_PALETTE["UNVERIFIED"])

    return {
        "item_type": kind,
        "epistemic_tag": tier_info["tag"],
        "badge_label": tier_info["label_es"],
        "color_hex": tier_info["color_hex"],
        "border_hex": tier_info["border_hex"],
        "scientific_rationale": tier_info["description"],
    }


def get_epistemic_locks_20013d1() -> Dict[str, Any]:
    """
    Exporta el bloque exacto `epistemic_locks` requerido por el Contrato JSON Estándar
    del Comparador 3D (Sección 4 del Plan Maestro Etapa 2).
    """
    allow_flame = allow_3d_flame_isosurface("20013D1")
    return {
        "mfc_voltage_to_massflow_verified": False,
        "thermocouple_to_kelvin_verified": False,
        "mfc_sensor_time_sync_verified": False,
        "allow_3d_flame_field_rendering": allow_flame,
        "allow_continuous_combustion_animation": False,
        "wireframe_fallback_label": "[CAMPO 3D DE LLAMA DESACTIVADO: SIN CALIBRACIÓN FÍSICA VERIFICADA]",
        "palette_legend": EPISTEMIC_PALETTE,
    }


if __name__ == "__main__":
    print("=== PRUEBA FASE 2 - PUNTO 5 (ia/epistemic_guard.py) ===")
    locks = get_epistemic_locks_20013d1()
    print(f"[OK] Candado allow_3d_flame_isosurface('20013D1') = {allow_3d_flame_isosurface('20013D1')}")
    print(f"[OK] Etiqueta Wireframe 3D: {locks['wireframe_fallback_label']}")
    for key in ("RAW_SENSOR_SERIES", "SCM_COUNTERFACTUAL_RESPONSE", "CONTINUOUS_3D_FLAME_FIELD"):
        res = classify_epistemic_item(key, {})
        print(f"[OK] {key:30s} -> {res['epistemic_tag']:10s} ({res['color_hex']}) | {res['badge_label']}")