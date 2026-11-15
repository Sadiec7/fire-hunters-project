# -*- coding: utf-8 -*-
"""
ia/domain_query.py
Buscador Inteligente de Dominio Experimental s-Flame y Puente con la Red Bayesiana.
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame).
Autores: Ángel ("Lito" / "Perrita") & Kay García Sánchez
"""

import os
import sys
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd

# Permitir importación tanto al correr "python ia/domain_query.py" como desde la raíz
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from ia.contract_si import SimulationInputSI, validate_input_si
    from ia.thermo_kinetics import get_physical_properties_si
except ImportError:
    from contract_si import SimulationInputSI, validate_input_si
    from thermo_kinetics import get_physical_properties_si


# Advertencia científica obligatoria para extrapolaciones (Sección 5.3 y Bloque 6)
EXTRAPOLATION_WARNING_ES: str = (
    "ADVERTENCIA CIENTÍFICA: Las condiciones ingresadas constituyen una extrapolación "
    "fuera del dominio experimental documentado en NASA s-Flame. Los resultados "
    "representan predicciones del modelo simplificado y NO deben interpretarse como "
    "mediciones experimentales."
)


# =============================================================================
# 1. CARGA DEL CATÁLOGO EXPERIMENTAL DE NASA s-Flame (Tarea A6.1 - Función 1)
# =============================================================================
def load_sflame_catalog(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Lee la tabla de experimentos reales de NASA s-Flame desde ia/nasa_sflame_experiments.csv.
    Incluye respaldo automático en caso de que el script se invoque desde otra ruta.
    Garantiza que únicamente se consulten experimentos de la campaña ACME s-Flame.
    """
    if csv_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "nasa_sflame_experiments.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df

    # Respaldo automático en memoria con los mismos datos verificados del Bloque 1
    fallback_data = [
        {
            "experiment_id": "SFLAME_REF_C2H4", "fuel_type": "C2H4",
            "Y_F_burner": 1.000, "Y_O_ambient": 0.233, "pressure_Pa": 98000.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 2.50e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0224,
            "measured_max_temp_K": 1677.0, "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_39B3", "fuel_type": "C2H4",
            "Y_F_burner": 1.000, "Y_O_ambient": 0.233, "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 2.50e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0221,
            "measured_max_temp_K": 1685.0, "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_51A1", "fuel_type": "C2H4",
            "Y_F_burner": 0.500, "Y_O_ambient": 0.233, "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 3.20e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0175,
            "measured_max_temp_K": 1540.0, "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 45.0,
        },
        {
            "experiment_id": "SFLAME_87D1", "fuel_type": "CH4",
            "Y_F_burner": 1.000, "Y_O_ambient": 0.233, "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 2.20e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0210,
            "measured_max_temp_K": 1620.0, "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_94A4", "fuel_type": "CH4",
            "Y_F_burner": 0.600, "Y_O_ambient": 0.260, "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 2.80e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0182,
            "measured_max_temp_K": 1690.0, "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_H2_01", "fuel_type": "H2",
            "Y_F_burner": 0.150, "Y_O_ambient": 0.233, "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 1.80e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0195,
            "measured_max_temp_K": 1750.0, "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 55.0,
        },
        {
            "experiment_id": "SFLAME_H2_02", "fuel_type": "H2",
            "Y_F_burner": 0.250, "Y_O_ambient": 0.210, "pressure_Pa": 85000.0,
            "T_ambient_K": 298.15, "T_burner_K": 300.0, "mass_flow_kg_s": 2.10e-6,
            "burner_radius_m": 0.00318, "measured_flame_radius_m": 0.0235,
            "measured_max_temp_K": 1810.0, "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 55.0,
        },
    ]
    return pd.DataFrame(fallback_data)


# =============================================================================
# 2. CLASIFICADOR DE DOMINIO DE OPERACIÓN (Tarea A6.1 - Función 2)
# =============================================================================
def classify_operating_domain(
    sim_input: Any,
    catalog_df: Optional[pd.DataFrame] = None,
    match_tol_rel: float = 0.05,
) -> Dict[str, Any]:
    """
    Determina si las condiciones de operación ingresadas por el usuario corresponden a:
      1) DOCUMENTED_EXPERIMENT: Coincide dentro del +/-5% con una corrida real de s-Flame.
      2) INTERPOLATION_INSIDE_DOMAIN: Cae dentro del rango mínimo-máximo experimental
         de s-Flame (con margen de tolerancia instrumental del 5%) para ese combustible.
      3) EXTRAPOLATION_OUT_OF_DOMAIN: Alguna variable clave cae fuera de los rangos
         experimentales documentados de s-Flame.
    """
    if isinstance(sim_input, dict):
        sim_obj = validate_input_si(sim_input)
    else:
        sim_obj = sim_input

    if catalog_df is None:
        catalog_df = load_sflame_catalog()

    # Filtrar por el mismo combustible
    fuel_df = catalog_df[catalog_df["fuel_type"] == sim_obj.fuel_type].copy()
    if fuel_df.empty:
        return {
            "classification": "EXTRAPOLATION_OUT_OF_DOMAIN",
            "regime_alias": "EXTRAPOLATION_OUT_OF_DOMAIN",
            "matched_experiment_id": None,
            "matched_experiment_data": None,
            "nearest_neighbors": [],
            "out_of_range_variables": ["fuel_type"],
            "scientific_warning": EXTRAPOLATION_WARNING_ES,
        }

    # Calcular diferencias relativas por cada variable clave: (p_0, Y_O_ambient, Y_F_burner, mdot)
    rel_diff_p = np.abs(fuel_df["pressure_Pa"] - sim_obj.pressure_Pa) / fuel_df["pressure_Pa"]
    rel_diff_YO = np.abs(fuel_df["Y_O_ambient"] - sim_obj.Y_O_ambient) / fuel_df["Y_O_ambient"]
    rel_diff_YF = np.abs(fuel_df["Y_F_burner"] - sim_obj.Y_F_burner) / fuel_df["Y_F_burner"]
    rel_diff_mdot = np.abs(fuel_df["mass_flow_kg_s"] - sim_obj.mass_flow_kg_s) / fuel_df["mass_flow_kg_s"]

    # Distancia euclidiana normalizada y diferencia máxima por fila
    fuel_df["norm_distance"] = np.sqrt(
        rel_diff_p**2 + rel_diff_YO**2 + rel_diff_YF**2 + rel_diff_mdot**2
    )
    fuel_df["max_rel_diff"] = np.maximum.reduce(
        [rel_diff_p, rel_diff_YO, rel_diff_YF, rel_diff_mdot]
    )

    fuel_df_sorted = fuel_df.sort_values(by="norm_distance", ascending=True)
    best_row = fuel_df_sorted.iloc[0]

    # Vecinos más cercanos para trazabilidad
    neighbors: List[Dict[str, Any]] = []
    for _, row in fuel_df_sorted.head(2).iterrows():
        neighbors.append(
            {
                "experiment_id": str(row["experiment_id"]),
                "fuel_type": str(row["fuel_type"]),
                "pressure_Pa": float(row["pressure_Pa"]),
                "Y_O_ambient": float(row["Y_O_ambient"]),
                "Y_F_burner": float(row["Y_F_burner"]),
                "mass_flow_kg_s": float(row["mass_flow_kg_s"]),
                "measured_flame_radius_m": float(row["measured_flame_radius_m"]),
                "measured_max_temp_K": float(row["measured_max_temp_K"]),
                "norm_distance": float(row["norm_distance"]),
            }
        )

    # CASO 1: Experimento directamente documentado (todas las variables dentro de +/- 5%)
    if float(best_row["max_rel_diff"]) <= match_tol_rel:
        matched_data = {
            "experiment_id": str(best_row["experiment_id"]),
            "fuel_type": str(best_row["fuel_type"]),
            "measured_flame_radius_m": float(best_row["measured_flame_radius_m"]),
            "measured_max_temp_K": float(best_row["measured_max_temp_K"]),
            "uncertainty_radius_m": float(best_row["uncertainty_radius_m"]),
            "uncertainty_temp_K": float(best_row["uncertainty_temp_K"]),
        }
        return {
            "classification": "DOCUMENTED_EXPERIMENT",
            "regime_alias": "DOCUMENTED_CONDITION",
            "matched_experiment_id": str(best_row["experiment_id"]),
            "matched_experiment_data": matched_data,
            "nearest_neighbors": neighbors,
            "out_of_range_variables": [],
            "scientific_warning": None,
        }

    # Revisar si cae dentro de los límites mínimo-máximo del catálogo s-Flame (con 5% de holgura)
    out_of_range_vars: List[str] = []
    checks = [
        ("pressure_Pa", sim_obj.pressure_Pa, float(fuel_df["pressure_Pa"].min()), float(fuel_df["pressure_Pa"].max())),
        ("Y_O_ambient", sim_obj.Y_O_ambient, float(fuel_df["Y_O_ambient"].min()), float(fuel_df["Y_O_ambient"].max())),
        ("Y_F_burner", sim_obj.Y_F_burner, float(fuel_df["Y_F_burner"].min()), float(fuel_df["Y_F_burner"].max())),
        ("mass_flow_kg_s", sim_obj.mass_flow_kg_s, float(fuel_df["mass_flow_kg_s"].min()), float(fuel_df["mass_flow_kg_s"].max())),
    ]
    for var_name, val, vmin, vmax in checks:
        low_bound = vmin * (1.0 - match_tol_rel)
        high_bound = vmax * (1.0 + match_tol_rel)
        if not (low_bound <= val <= high_bound):
            out_of_range_vars.append(var_name)

    # CASO 2: Interpolación dentro del dominio experimental
    if len(out_of_range_vars) == 0:
        return {
            "classification": "INTERPOLATION_INSIDE_DOMAIN",
            "regime_alias": "INTERPOLATION_IN_DOMAIN",
            "matched_experiment_id": None,
            "matched_experiment_data": None,
            "nearest_neighbors": neighbors,
            "out_of_range_variables": [],
            "scientific_warning": (
                "NOTA METODOLÓGICA: Condición de interpolación dentro de los rangos "
                f"experimentales de NASA s-Flame para {sim_obj.fuel_type}. Experimentos "
                f"de referencia más cercanos: {[n['experiment_id'] for n in neighbors]}."
            ),
        }

    # CASO 3: Extrapolación fuera del dominio experimental
    return {
        "classification": "EXTRAPOLATION_OUT_OF_DOMAIN",
        "regime_alias": "EXTRAPOLATION_OUT_OF_DOMAIN",
        "matched_experiment_id": None,
        "matched_experiment_data": None,
        "nearest_neighbors": neighbors,
        "out_of_range_variables": out_of_range_vars,
        "scientific_warning": EXTRAPOLATION_WARNING_ES,
    }


# =============================================================================
# 3. PUENTE DE MÉTRICAS FÍSICAS PARA LA RED BAYESIANA DE KAY (Tarea A6.1 - Función 3)
# =============================================================================
def compute_bayesian_bridge_metrics(
    sim_input: Any,
    sim_results_summary: Optional[Dict[str, Any]] = None,
    domain_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calcula las métricas físicas deterministas y adimensionales que alimentan los nodos
    de la Red Bayesiana de Seguridad contra Incendios en Microgravedad de Kay:
      - stoichiometric_Z_st: Fracción de mezcla estequiométrica [-]
      - burke_schumann_radius_m: Radio teórico de llama por difusión esférica 1D [m]
      - damkohler_number: Número de Damköhler global Da = tau_flow / tau_chem [-]
      - heat_release_rate_W: Potencia térmica nominal liberada por la llama [W]
      - thermal_margin_K: Margen térmico respecto al umbral de daño estructural (~800 K) [K]
    """
    if isinstance(sim_input, dict):
        sim_obj = validate_input_si(sim_input)
    else:
        sim_obj = sim_input

    props = get_physical_properties_si(sim_obj)
    if domain_result is None:
        domain_result = classify_operating_domain(sim_obj)

    Z_st = float(props["Z_st"])
    rho_D_eff = float(props["rho_D_eff"])
    mdot = float(sim_obj.mass_flow_kg_s)

    # Radio estequiométrico analítico 1D de Burke-Schumann:
    # Z(r_f) = Z_st = 1 - exp(-mdot / (4 * pi * rho * D * r_f))
    denom_bs = -4.0 * np.pi * rho_D_eff * np.log(max(1.0 - Z_st, 1.0e-9))
    r_f_est_m = float(mdot / max(denom_bs, 1.0e-12))

    # Si ya corrió el solver 3D, usar T_max y r_f de la simulación 3D; si no, estimar
    if sim_results_summary is not None:
        T_max_K = float(sim_results_summary.get("max_temperature_K", 1677.0))
        r_f_m = float(sim_results_summary.get("predicted_flame_radius_m", r_f_est_m))
    else:
        T_max_K = 1677.0
        r_f_m = r_f_est_m

    # Tiempo característico de residencia difusiva/convectiva en la esfera de llama: tau_flow = r_f^2 / D_F
    tau_flow_s = (r_f_m**2) / float(props["D_F"])

    # Tiempo químico característico de Arrhenius evaluado en la zona de reacción
    rho = float(props["rho"])
    A = float(props["A"])
    E_a = float(props["E_a"])
    R_u = float(props["R_u"])
    k_arr = A * np.exp(-E_a / (R_u * max(T_max_K, 300.0)))
    C_O_char = rho * sim_obj.Y_O_ambient * 0.5
    tau_chem_s = 1.0 / max(k_arr * C_O_char, 1.0e-12)

    damkohler_number = float(tau_flow_s / tau_chem_s)

    # Calor total liberado si se quema el flujo inyectado de combustible: Q_dot = mdot * Y_F_burner * delta_H_c [W]
    heat_release_rate_W = float(mdot * sim_obj.Y_F_burner * float(props["delta_H_c"]))

    # Margen térmico frente a temperatura crítica de materiales aeroespaciales (T_crit = 800 K)
    T_critical_habitat_K = 800.0
    thermal_margin_K = float(T_max_K - T_critical_habitat_K)

    return {
        "damkohler_number": damkohler_number,
        "thermal_margin_K": thermal_margin_K,
        "stoichiometric_Z_st": Z_st,
        "heat_release_rate_W": heat_release_rate_W,
        "estimated_flame_radius_m": r_f_m,
        "max_temperature_K": T_max_K,
        "domain_classification": domain_result["classification"],
        "is_extrapolated": domain_result["classification"] == "EXTRAPOLATION_OUT_OF_DOMAIN",
    }


def query_experimental_domain(
    user_input_dict: Any, csv_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Alias de compatibilidad directa con proyecto_acme (1).pdf (Tarea 6.1).
    Une la clasificación de dominio y las métricas resumen para la Red Bayesiana.
    """
    catalog = load_sflame_catalog(csv_path)
    dom_res = classify_operating_domain(user_input_dict, catalog)
    bayesian_metrics = compute_bayesian_bridge_metrics(
        user_input_dict, domain_result=dom_res
    )
    dom_res["bayesian_network_bridge"] = bayesian_metrics
    return dom_res


# =============================================================================
# 4. BLOQUE DE PRUEBA DIRECTA EN TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=== PRUEBA DE CONSULTA DE DOMINIO EXPERIMENTAL (ia/domain_query.py) ===")

    # Caso 1: Experimento Documentado (Caso maestro SFLAME_REF_C2H4)
    caso_doc = SimulationInputSI(
        fuel_type="C2H4", Y_F_burner=1.0, Y_O_ambient=0.233,
        pressure_Pa=98000.0, mass_flow_kg_s=2.5e-6
    )
    res_doc = classify_operating_domain(caso_doc)
    print(f"[1] Caso Maestro -> Clasificación: {res_doc['classification']} (ID: {res_doc['matched_experiment_id']})")

    # Caso 2: Interpolación dentro del dominio de C2H4 (Y_F=0.75, mdot=2.8e-6)
    caso_interp = SimulationInputSI(
        fuel_type="C2H4", Y_F_burner=0.75, Y_O_ambient=0.233,
        pressure_Pa=100000.0, mass_flow_kg_s=2.8e-6
    )
    res_interp = classify_operating_domain(caso_interp)
    print(f"[2] Caso Intermedio -> Clasificación: {res_interp['classification']}")
    print(f"    Vecinos: {[n['experiment_id'] for n in res_interp['nearest_neighbors']]}")

    # Caso 3: Extrapolación fuera del dominio (presión muy baja 40 kPa y alto flujo)
    caso_extrap = SimulationInputSI(
        fuel_type="C2H4", Y_F_burner=1.0, Y_O_ambient=0.35,
        pressure_Pa=40000.0, mass_flow_kg_s=8.0e-6
    )
    res_extrap = classify_operating_domain(caso_extrap)
    print(f"[3] Caso Extrapolado -> Clasificación: {res_extrap['classification']}")
    print(f"    Variables fuera de rango: {res_extrap['out_of_range_variables']}")
    print(f"    Alerta: {res_extrap['scientific_warning']}")

    # Prueba del puente con la Red Bayesiana de Kay
    bridge = compute_bayesian_bridge_metrics(caso_doc, domain_result=res_doc)
    print("[4] Puente Red Bayesiana (Kay):", bridge)