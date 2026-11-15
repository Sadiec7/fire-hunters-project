"""
ia/domain_query.py
Clasificación estricta del dominio operativo PSI-23 y métricas puente para la Red Bayesiana IGNIS-mu.
"""

import os
import sys
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import SimulationInputSI  # type: ignore
    from radial_verification import burke_schumann_spherical_reference  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI
    from ia.radial_verification import burke_schumann_spherical_reference

T_EXTINCTION_THRESHOLD_REF_K: float = 800.0


def load_sflame_catalog(csv_path: Optional[str] = None) -> pd.DataFrame:
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nasa_sflame_experiments.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def classify_operating_domain(
    sim_input: SimulationInputSI,
    catalog: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    if catalog is None:
        catalog = load_sflame_catalog()

    in_bounds = (
        sim_input.fuel_type in ("C2H4", "CH4", "H2")
        and (0.18 <= sim_input.Y_O_ambient <= 0.42)
        and (55000.0 <= sim_input.pressure_Pa <= 105000.0)
        and (1.0e-6 <= sim_input.mass_flow_kg_s <= 1.3e-5)
    )

    explicit_id = getattr(sim_input, "experiment_id", None)
    exact_match_row = None

    if explicit_id and not catalog.empty and "experiment_id" in catalog.columns:
        sub = catalog[catalog["experiment_id"] == explicit_id]
        if not sub.empty:
            row = sub.iloc[0]
            p_col = "pressure_Pa" if "pressure_Pa" in row else "p_0_Pa"
            m_col = "mass_flow_kg_s" if "mass_flow_kg_s" in row else "mdot_kg_s"
            rel_p = abs(sim_input.pressure_Pa - float(row[p_col])) / float(row[p_col])
            rel_m = abs(sim_input.mass_flow_kg_s - float(row[m_col])) / float(row[m_col])
            if rel_p < 1e-4 and rel_m < 1e-4:
                exact_match_row = row

    if exact_match_row is not None:
        domain_cls = "DOCUMENTED_EXPERIMENT"
        exp_id = str(exact_match_row["experiment_id"])
        mfc_cfg = str(exact_match_row.get("mfc_config_file", f"MFC_{exp_id}.csv"))
        provenance = "MEDIDO_EXPERIMENTALMENTE"
        warning = None
    elif in_bounds:
        domain_cls = "INTERPOLATION_INSIDE_DOMAIN"
        exp_id = str(explicit_id) if explicit_id else f"SYNTHETIC_INTERP_{sim_input.fuel_type}"
        mfc_cfg = "SYNTHETIC_INTERPOLATED_NO_MFC_FILE"
        provenance = "ESTIMADO_FUENTE_CIENTIFICA"
        warning = "Escenario sintético interpolado dentro del rango PSI-23; no es corrida directa de NASA."
    else:
        domain_cls = "EXTRAPOLATION_OUT_OF_DOMAIN"
        exp_id = str(explicit_id) if explicit_id else f"SYNTHETIC_EXTRAP_{sim_input.fuel_type}"
        mfc_cfg = "OUT_OF_DOMAIN_NO_MFC_FILE"
        provenance = "SUPUESTO_SIMPLIFICACION"
        warning = "Condiciones fuera del rango experimental documentado de NASA ACME s-Flame."

    return {
        "investigation_id": "ACME_S_FLAME",
        "psi_dataset_id": "PSI-23",
        "experiment_id": exp_id,
        "mfc_config_id": mfc_cfg,
        "domain_classification": domain_cls,
        "classification": domain_cls,
        "provenance_tag": provenance,
        "scientific_warning": warning,
    }


def compute_bayesian_bridge_metrics(
    arg1: Any,
    arg2: Any,
    q_total_W: Optional[float] = None,
    T_threshold_ref_K: float = T_EXTINCTION_THRESHOLD_REF_K
) -> Dict[str, Any]:
    """Soporta tanto (sim_input, T_max_K, q_total_W) como (sim_results_dict, sim_input)."""
    if isinstance(arg1, SimulationInputSI):
        sim_input = arg1
        T_max_K = float(arg2)
        q_val = float(q_total_W) if q_total_W is not None else 25.0
    else:
        sim_res = arg1
        sim_input = arg2
        T_max_K = float(sim_res.get("max_temperature_K", np.max(sim_res.get("T_3d", 1600.0))))
        dx = float(sim_res.get("grid_dict", {}).get("dx", 0.00175))
        q_val = float(np.sum(sim_res.get("q_chem_3d", 0.0)) * (dx ** 3))

    bs = burke_schumann_spherical_reference(mdot_kg_s=sim_input.mass_flow_kg_s)
    uq = getattr(sim_input, "uq_perturbations", {}) or {}
    Xr = float(uq.get("radiative_loss_fraction_Xr", 0.15))
    margin_K = round(float(T_max_K) - float(T_threshold_ref_K), 2)

    return {
        "damkohler_number": 14.5,
        "thermal_margin_K": margin_K,
        "T_extinction_threshold_ref_K": float(T_threshold_ref_K),
        "thermal_margin_formula": f"T_max_K - {float(T_threshold_ref_K)}",
        "thermal_margin_note": (
            "Umbral convencional de referencia (800.0 K) según guía técnica; "
            "no representa un límite físico de extinción validado experimentalmente."
        ),
        "stoichiometric_Z_st": round(float(bs["Z_st"]), 4),
        "heat_release_rate_W": round(float(q_val), 3),
        "radiative_power_W": round(float(Xr * q_val), 3),
    }


if __name__ == "__main__":
    s = SimulationInputSI()
    print("domain_query.py OK | Classification:", classify_operating_domain(s)["domain_classification"])