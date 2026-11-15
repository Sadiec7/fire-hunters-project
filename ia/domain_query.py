# -*- coding: utf-8 -*-
"""
ARCHIVO: ia/domain_query.py
RESPONSABLE: Ángel ("Lito" / "Perrita")
DESCRIPCIÓN: Clasificador del dominio operativo respecto al catálogo NASA PSI-23
             (s-Flame), generador del bloque obligatorio `experiment_context`
             (Entregable 1) y cálculo de métricas puente incluyendo potencia
             radiativa Q_rad = X_r * Q_chem [W] (Entregable 3).
"""

import os
import csv
import math
from typing import Dict, Any, List, Optional


DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "nasa_sflame_experiments.csv")


def load_sflame_catalog(csv_path: str = DEFAULT_CSV_PATH) -> List[Dict[str, Any]]:
    """
    Carga el catálogo experimental de NASA s-Flame (PSI-23) desde el archivo CSV.
    Si el archivo no existe en disco, retorna el catálogo embebido de respaldo.
    """
    catalog: List[Dict[str, Any]] = []
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                catalog.append({
                    "experiment_id": str(row["experiment_id"]).strip(),
                    "psi_id": str(row.get("psi_id", "PSI-23")).strip(),
                    "mfc_config_file": str(row.get("mfc_config_file", f"MFC_CFG_{row['experiment_id']}.csv")).strip(),
                    "test_day_id": str(row.get("test_day_id", "CIR_DAY_01")).strip(),
                    "fuel_type": str(row["fuel_type"]).strip().upper(),
                    "diluent_species": str(row.get("diluent_species", "N2")).strip(),
                    "Y_F_burner": float(row["Y_F_burner"]),
                    "Y_O_ambient": float(row["Y_O_ambient"]),
                    "pressure_Pa": float(row["pressure_Pa"]),
                    "T_ambient_K": float(row["T_ambient_K"]),
                    "T_burner_K": float(row["T_burner_K"]),
                    "mass_flow_kg_s": float(row["mass_flow_kg_s"]),
                    "burner_radius_m": float(row["burner_radius_m"]),
                    "measured_flame_radius_m": float(row["measured_flame_radius_m"]),
                    "measured_max_temp_K": float(row["measured_max_temp_K"]),
                    "uncertainty_radius_m": float(row["uncertainty_radius_m"]),
                    "uncertainty_temp_K": float(row["uncertainty_temp_K"]),
                })
        if catalog:
            return catalog

    # Respaldo embebido en caso de ejecución aislada
    return [
        {
            "experiment_id": "SFLAME_REF_C2H4",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_REF_C2H4.csv",
            "test_day_id": "CIR_DAY_01",
            "fuel_type": "C2H4",
            "diluent_species": "N2",
            "Y_F_burner": 1.000,
            "Y_O_ambient": 0.233,
            "pressure_Pa": 98000.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 2.50e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0224,
            "measured_max_temp_K": 1677.0,
            "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_39B3",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_39B3.csv",
            "test_day_id": "CIR_DAY_04",
            "fuel_type": "C2H4",
            "diluent_species": "N2",
            "Y_F_burner": 1.000,
            "Y_O_ambient": 0.233,
            "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 2.50e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0221,
            "measured_max_temp_K": 1685.0,
            "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_51A1",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_51A1.csv",
            "test_day_id": "CIR_DAY_07",
            "fuel_type": "C2H4",
            "diluent_species": "N2",
            "Y_F_burner": 0.500,
            "Y_O_ambient": 0.233,
            "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 3.20e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0175,
            "measured_max_temp_K": 1540.0,
            "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 45.0,
        },
        {
            "experiment_id": "SFLAME_87D1",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_87D1.csv",
            "test_day_id": "CIR_DAY_11",
            "fuel_type": "CH4",
            "diluent_species": "N2",
            "Y_F_burner": 1.000,
            "Y_O_ambient": 0.233,
            "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 2.20e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0210,
            "measured_max_temp_K": 1620.0,
            "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_94A4",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_94A4.csv",
            "test_day_id": "CIR_DAY_14",
            "fuel_type": "CH4",
            "diluent_species": "N2",
            "Y_F_burner": 0.600,
            "Y_O_ambient": 0.260,
            "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 2.80e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0182,
            "measured_max_temp_K": 1690.0,
            "uncertainty_radius_m": 0.0005,
            "uncertainty_temp_K": 50.0,
        },
        {
            "experiment_id": "SFLAME_H2_01",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_H2_01.csv",
            "test_day_id": "CIR_DAY_16",
            "fuel_type": "H2",
            "diluent_species": "N2",
            "Y_F_burner": 0.150,
            "Y_O_ambient": 0.233,
            "pressure_Pa": 101325.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 1.80e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0195,
            "measured_max_temp_K": 1750.0,
            "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 55.0,
        },
        {
            "experiment_id": "SFLAME_H2_02",
            "psi_id": "PSI-23",
            "mfc_config_file": "MFC_CFG_H2_02.csv",
            "test_day_id": "CIR_DAY_18",
            "fuel_type": "H2",
            "diluent_species": "He",
            "Y_F_burner": 0.250,
            "Y_O_ambient": 0.210,
            "pressure_Pa": 85000.0,
            "T_ambient_K": 298.15,
            "T_burner_K": 300.0,
            "mass_flow_kg_s": 2.10e-6,
            "burner_radius_m": 0.00318,
            "measured_flame_radius_m": 0.0235,
            "measured_max_temp_K": 1810.0,
            "uncertainty_radius_m": 0.0006,
            "uncertainty_temp_K": 55.0,
        },
    ]


def _extract_param(sim_input: Any, key: str, default: Any = None) -> Any:
    """Extrae un atributo tanto si sim_input es objeto SimulationInputSI como dict."""
    if isinstance(sim_input, dict):
        return sim_input.get(key, default)
    return getattr(sim_input, key, default)


def classify_operating_domain(
    sim_input: Any,
    csv_path: str = DEFAULT_CSV_PATH
) -> Dict[str, Any]:
    """
    ENTREGABLE 1 (IGNIS-mu / PSI-23):
    Clasifica las condiciones de entrada frente al catálogo experimental de
    NASA s-Flame y devuelve el bloque estructurado `experiment_context` con las
    cinco llaves obligatorias pedidas por la jefa:
      1. investigation_id: "ACME_S_FLAME"
      2. psi_dataset_id: "PSI-23"
      3. experiment_id: ej. "SFLAME_39B3", "SFLAME_51A1", "SFLAME_REF_C2H4", etc.
      4. mfc_config_id: ej. "MFC_CFG_39B3.csv"
      5. domain_classification: "DOCUMENTED_EXPERIMENT",
         "INTERPOLATION_INSIDE_DOMAIN" o "EXTRAPOLATION_OUT_OF_DOMAIN"
    """
    catalog = load_sflame_catalog(csv_path)

    fuel_type = str(_extract_param(sim_input, "fuel_type", "C2H4")).upper()
    Y_F = float(_extract_param(sim_input, "Y_F_burner", 1.0))
    Y_O = float(_extract_param(sim_input, "Y_O_ambient", 0.233))
    p_Pa = float(_extract_param(sim_input, "pressure_Pa", 98000.0))
    mdot = float(_extract_param(sim_input, "mass_flow_kg_s", 2.5e-6))

    # Filtrar experimentos del mismo combustible
    same_fuel_exps = [exp for exp in catalog if exp["fuel_type"] == fuel_type]
    search_pool = same_fuel_exps if same_fuel_exps else catalog

    best_exp: Dict[str, Any] = search_pool[0]
    min_distance = float("inf")

    for exp in search_pool:
        rel_YF = (Y_F - exp["Y_F_burner"]) / max(exp["Y_F_burner"], 0.1)
        rel_YO = (Y_O - exp["Y_O_ambient"]) / max(exp["Y_O_ambient"], 0.1)
        rel_p = (p_Pa - exp["pressure_Pa"]) / max(exp["pressure_Pa"], 1.0)
        rel_m = (mdot - exp["mass_flow_kg_s"]) / max(exp["mass_flow_kg_s"], 1e-9)

        dist = math.sqrt(rel_YF**2 + rel_YO**2 + rel_p**2 + rel_m**2)
        if dist < min_distance:
            min_distance = dist
            best_exp = exp

    # Determinar clasificación del dominio operativo
    if same_fuel_exps and min_distance <= 0.035:
        domain_classification = "DOCUMENTED_EXPERIMENT"
    else:
        # Evaluar si cae dentro de la envolvente global documentada en s-Flame
        all_YF = [e["Y_F_burner"] for e in catalog]
        all_YO = [e["Y_O_ambient"] for e in catalog]
        all_p = [e["pressure_Pa"] for e in catalog]
        all_m = [e["mass_flow_kg_s"] for e in catalog]

        inside_envelope = (
            (min(all_YF) * 0.90 <= Y_F <= max(all_YF) * 1.05) and
            (min(all_YO) * 0.90 <= Y_O <= max(all_YO) * 1.05) and
            (min(all_p) * 0.90 <= p_Pa <= max(all_p) * 1.05) and
            (min(all_m) * 0.85 <= mdot <= max(all_m) * 1.15)
        )
        if same_fuel_exps and inside_envelope:
            domain_classification = "INTERPOLATION_INSIDE_DOMAIN"
        else:
            domain_classification = "EXTRAPOLATION_OUT_OF_DOMAIN"

    # Permitir override explícito si el usuario especificó experiment_id o mfc_config_id
    explicit_exp_id = _extract_param(sim_input, "experiment_id", None)
    explicit_mfc_id = _extract_param(sim_input, "mfc_config_id", None)

    matched_exp_id = str(explicit_exp_id) if explicit_exp_id else best_exp["experiment_id"]
    matched_mfc_id = str(explicit_mfc_id) if explicit_mfc_id else best_exp["mfc_config_file"]

    # Bloque exacto del Entregable 1 solicitado por la líder de IGNIS-mu
    experiment_context = {
        "investigation_id": "ACME_S_FLAME",
        "psi_dataset_id": best_exp.get("psi_id", "PSI-23"),
        "experiment_id": matched_exp_id,
        "mfc_config_id": matched_mfc_id,
        "domain_classification": domain_classification,
        "test_day_id": best_exp.get("test_day_id", "CIR_DAY_01"),
    }

    return {
        "experiment_context": experiment_context,
        "domain_classification": domain_classification,
        "closest_experiment_id": best_exp["experiment_id"],
        "normalized_distance": round(float(min_distance), 6),
        "reference_experiment_data": best_exp,
        "provenance_tag": (
            "MEDIDO_EXPERIMENTALMENTE"
            if domain_classification == "DOCUMENTED_EXPERIMENT"
            else "ESTIMADO_FUENTE_CIENTIFICA"
        ),
    }


def compute_bayesian_bridge_metrics(
    sim_input: Any,
    props_si: Dict[str, Any],
    sim_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    ENTREGABLE 3 (IGNIS-mu / PSI-23):
    Calcula las métricas físicas agregadas y agrega la potencia radiativa
    emitida estimada Q_rad = X_r * Q_chem [W] para comparar directamente
    contra los radiómetros de banda ancha de PSI-23.
    """
    Y_F_b = float(_extract_param(sim_input, "Y_F_burner", 1.0))
    Y_O_inf = float(_extract_param(sim_input, "Y_O_ambient", 0.233))
    s_stoich = float(props_si.get("stoich_oxygen_fuel_mass_ratio_s", 3.428))

    # Fracción de mezcla estequiométrica Z_st
    Z_st = 1.0 / (1.0 + (s_stoich * Y_F_b) / max(Y_O_inf, 1e-12))

    # Potencia química integrada [W]
    Q_chem_W = float(sim_summary.get("integrated_heat_release_W", 0.0))
    if Q_chem_W <= 0.0:
        mdot = float(_extract_param(sim_input, "mass_flow_kg_s", 2.5e-6))
        dHc = float(props_si.get("heat_of_combustion_J_kg", 4.71e7))
        Q_chem_W = mdot * Y_F_b * dHc

    # Fracción de pérdida radiativa X_r (nominal o perturbada por UQ)
    X_r = float(props_si.get("radiative_loss_fraction_Xr", 0.35))
    Q_rad_W = X_r * Q_chem_W
    Q_net_W = (1.0 - X_r) * Q_chem_W

    # Tiempo característico difusivo y de reacción (Número de Damköhler global)
    r_f_m = float(sim_summary.get("flame_radius_m", 0.022))
    D_F = float(props_si.get("D_F_m2_s", 2.0e-5))
    tau_diff_s = (r_f_m ** 2) / max(D_F, 1e-12)

    A_preexp = float(props_si.get("A_preexp_m3_kg_s", 1.2e9))
    E_a = float(props_si.get("E_a_J_mol", 1.25e5))
    R_u = 8.314462618
    T_max_K = float(sim_summary.get("max_temperature_K", 1677.0))
    rho = float(props_si.get("rho_kg_m3", 1.15))

    k_chem = rho * A_preexp * math.exp(-E_a / max(R_u * T_max_K, 1.0))
    tau_chem_s = 1.0 / max(k_chem, 1e-12)
    damkohler_number = tau_diff_s / max(tau_chem_s, 1e-12)

    return {
        "stoichiometric_mixture_fraction_Z_st": round(Z_st, 6),
        "damkohler_number_Da": round(damkohler_number, 4),
        "integrated_heat_release_Q_chem_W": round(Q_chem_W, 4),
        "radiative_loss_fraction_Xr": round(X_r, 4),
        "estimated_radiative_power_Q_rad_W": round(Q_rad_W, 4),
        "net_thermal_power_Q_net_W": round(Q_net_W, 4),
        "characteristic_diffusion_time_s": round(tau_diff_s, 4),
        "units": {
            "stoichiometric_mixture_fraction_Z_st": "-",
            "damkohler_number_Da": "-",
            "integrated_heat_release_Q_chem_W": "W",
            "radiative_loss_fraction_Xr": "-",
            "estimated_radiative_power_Q_rad_W": "W",
            "net_thermal_power_Q_net_W": "W",
            "characteristic_diffusion_time_s": "s",
        },
    }


if __name__ == "__main__":
    test_case = {
        "fuel_type": "C2H4",
        "Y_F_burner": 1.0,
        "Y_O_ambient": 0.233,
        "pressure_Pa": 101325.0,
        "mass_flow_kg_s": 2.50e-6,
    }
    res = classify_operating_domain(test_case)
    print("=== PRUEBA ENTREGABLE 1 (domain_query.py) ===")
    print("experiment_context:", res["experiment_context"])
    bridge = compute_bayesian_bridge_metrics(
        test_case,
        {"radiative_loss_fraction_Xr": 0.35},
        {"flame_radius_m": 0.0221, "max_temperature_K": 1685.0},
    )
    print("Q_rad [W] (Entregable 3):", bridge["estimated_radiative_power_Q_rad_W"])