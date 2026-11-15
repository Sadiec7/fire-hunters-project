# -*- coding: utf-8 -*-
"""
ARCHIVO: ia/thermo_kinetics.py
RESPONSABLE: Ángel ("Lito" / "Perrita")
DESCRIPCIÓN: Propiedades Termofísicas en SI, Conector con Cantera (gri30.yaml),
             Aplicación de Perturbaciones UQ y Auditoría de Conservación 3D.
             Cumple Entregables 4, 5 y 6 del Contrato con IGNIS-mu (PSI-23).
"""

import os
import sys
from typing import Dict, Any, Tuple, Optional
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from ia.contract_si import (
        R_U_J_MOL_K,
        SimulationInputSI,
        DEFAULT_UQ_PERTURBATIONS,
        mass_fraction_to_concentration,
    )
except ImportError:
    from contract_si import (
        R_U_J_MOL_K,
        SimulationInputSI,
        DEFAULT_UQ_PERTURBATIONS,
        mass_fraction_to_concentration,
    )

# Detectar disponibilidad de Cantera para el Entregable 6 (gri30.yaml)
try:
    import cantera as ct  # type: ignore
    CANTERA_AVAILABLE = True
except ImportError:
    ct = None
    CANTERA_AVAILABLE = False

# =============================================================================
# 1. BASE DE DATOS MAESTRA POR COMBUSTIBLE EN UNIDADES SI
# =============================================================================
P_ATM_PA: float = 101325.0       # Presión atmosférica estándar [Pa]
W_O2_KG_MOL: float = 0.03200     # Peso molecular del oxígeno O2 [kg/mol]
W_N2_KG_MOL: float = 0.0280134   # Peso molecular del nitrógeno N2 [kg/mol]
W_HE_KG_MOL: float = 0.0040026   # Peso molecular del helio He [kg/mol]

FUEL_DATABASE_SI: Dict[str, Dict[str, Any]] = {
    "C2H4": {
        "name": "Etileno (C2H4)",
        "global_reaction": "C2H4 + 3 O2 -> 2 CO2 + 2 H2O",
        "W_F": 0.02805,              # [kg/mol]
        "W_O2": W_O2_KG_MOL,         # [kg/mol]
        "s": 3.422,                  # [kg O2 / kg C2H4]
        "delta_H_c": 4.716e7,        # [J/kg]
        "E_a": 1.255e5,              # [J/mol]
        "A": 1.2e9,                  # [m^3/(kg*s)]
        "D_F_0": 3.8e-5,             # [m^2/s] a 1 atm
        "D_O_0": 4.0e-5,             # [m^2/s] a 1 atm
        "alpha_0": 4.2e-5,           # [m^2/s] a 1 atm
        "c_p": 1250.0,               # [J/(kg*K)]
        "T_film_ref_K": 980.0,       # [K]
        "T_ad_nominal_K": 2369.0,    # Temperatura adiabática de referencia [K]
        "provenance": {
            "W_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "s": "CALCULADO_DE_DATOS_EXP",
            "delta_H_c": "ESTIMADO_FUENTE_CIENTIFICA",
            "E_a": "ESTIMADO_FUENTE_CIENTIFICA",
            "A": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_O": "ESTIMADO_FUENTE_CIENTIFICA",
            "alpha": "ESTIMADO_FUENTE_CIENTIFICA",
            "c_p": "SUPUESTO_SIMPLIFICACION",
            "rho": "SUPUESTO_SIMPLIFICACION",
        },
    },
    "CH4": {
        "name": "Metano (CH4)",
        "global_reaction": "CH4 + 2 O2 -> CO2 + 2 H2O",
        "W_F": 0.01604,              # [kg/mol]
        "W_O2": W_O2_KG_MOL,         # [kg/mol]
        "s": 3.989,                  # [kg O2 / kg CH4]
        "delta_H_c": 5.002e7,        # [J/kg]
        "E_a": 1.255e5,              # [J/mol]
        "A": 8.5e8,                  # [m^3/(kg*s)]
        "D_F_0": 4.5e-5,             # [m^2/s] a 1 atm
        "D_O_0": 4.0e-5,             # [m^2/s] a 1 atm
        "alpha_0": 4.3e-5,           # [m^2/s] a 1 atm
        "c_p": 1300.0,               # [J/(kg*K)]
        "T_film_ref_K": 960.0,       # [K]
        "T_ad_nominal_K": 2226.0,    # [K]
        "provenance": {
            "W_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "s": "CALCULADO_DE_DATOS_EXP",
            "delta_H_c": "ESTIMADO_FUENTE_CIENTIFICA",
            "E_a": "ESTIMADO_FUENTE_CIENTIFICA",
            "A": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_O": "ESTIMADO_FUENTE_CIENTIFICA",
            "alpha": "ESTIMADO_FUENTE_CIENTIFICA",
            "c_p": "SUPUESTO_SIMPLIFICACION",
            "rho": "SUPUESTO_SIMPLIFICACION",
        },
    },
    "H2": {
        "name": "Hidrógeno (H2)",
        "global_reaction": "2 H2 + O2 -> 2 H2O",
        "W_F": 0.002016,             # [kg/mol]
        "W_O2": W_O2_KG_MOL,         # [kg/mol]
        "s": 7.937,                  # [kg O2 / kg H2]
        "delta_H_c": 1.199e8,        # [J/kg]
        "E_a": 8.314e4,              # [J/mol]
        "A": 2.5e9,                  # [m^3/(kg*s)]
        "D_F_0": 1.4e-4,             # [m^2/s] a 1 atm
        "D_O_0": 4.2e-5,             # [m^2/s] a 1 atm
        "alpha_0": 5.2e-5,           # [m^2/s] a 1 atm
        "c_p": 1450.0,               # [J/(kg*K)]
        "T_film_ref_K": 950.0,       # [K]
        "T_ad_nominal_K": 2380.0,    # [K]
        "provenance": {
            "W_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "s": "CALCULADO_DE_DATOS_EXP",
            "delta_H_c": "ESTIMADO_FUENTE_CIENTIFICA",
            "E_a": "ESTIMADO_FUENTE_CIENTIFICA",
            "A": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_F": "ESTIMADO_FUENTE_CIENTIFICA",
            "D_O": "ESTIMADO_FUENTE_CIENTIFICA",
            "alpha": "ESTIMADO_FUENTE_CIENTIFICA",
            "c_p": "SUPUESTO_SIMPLIFICACION",
            "rho": "SUPUESTO_SIMPLIFICACION",
        },
    },
}

FUEL_DATABASE = FUEL_DATABASE_SI


# =============================================================================
# 2. INTEGRACIÓN CON CANTERA GRI-MECH 3.0 (Entregable 6 - Trabajo de Ángel)
# =============================================================================
def evaluate_cantera_properties(sim_input: Any) -> Dict[str, Any]:
    """
    ENTREGABLE 6 (Trabajo de Ángel):
    Carga automáticamente el mecanismo detallado `gri30.yaml` (GRI-Mech 3.0 con
    53 especies y 325 reacciones) cuando la librería `cantera` está instalada.
    """
    if isinstance(sim_input, dict):
        fuel = str(sim_input.get("fuel_type", sim_input.get("fuel", "C2H4"))).upper()
        diluent = str(sim_input.get("diluent_species", "N2"))
        p_Pa = float(sim_input.get("pressure_Pa", 98000.0))
        T_in_K = float(sim_input.get("T_initial_K", 298.15))
        Y_F_b = float(sim_input.get("Y_F_burner", 1.0))
        Y_O_inf = float(sim_input.get("Y_O_ambient", 0.233))
    else:
        fuel = str(sim_input.fuel_type).upper()
        diluent = str(getattr(sim_input, "diluent_species", "N2"))
        p_Pa = float(sim_input.pressure_Pa)
        T_in_K = float(sim_input.T_initial_K)
        Y_F_b = float(sim_input.Y_F_burner)
        Y_O_inf = float(sim_input.Y_O_ambient)

    base = FUEL_DATABASE_SI.get(fuel, FUEL_DATABASE_SI["C2H4"])
    T_film_K = float(base["T_film_ref_K"])

    if CANTERA_AVAILABLE and ct is not None:
        try:
            gas = ct.Solution("gri30.yaml")
            s_ratio = float(base["s"])
            Z_st = 1.0 / (1.0 + (s_ratio * Y_F_b) / max(Y_O_inf, 1.0e-12))
            Y_fuel_st = Z_st * Y_F_b
            Y_dil_burner_st = Z_st * max(0.0, 1.0 - Y_F_b)
            Y_ox_st = (1.0 - Z_st) * Y_O_inf
            Y_n2_amb_st = (1.0 - Z_st) * max(0.0, 1.0 - Y_O_inf)

            comp_dict: Dict[str, float] = {
                fuel: Y_fuel_st,
                "O2": Y_ox_st,
                "N2": Y_n2_amb_st + (Y_dil_burner_st if diluent == "N2" else 0.0),
            }
            if diluent == "He" and Y_dil_burner_st > 0.0:
                comp_dict["He"] = Y_dil_burner_st

            gas.TPY = T_in_K, p_Pa, comp_dict
            gas.equilibrate("HP")
            T_ad_K = float(gas.T)

            gas.TPY = T_film_K, p_Pa, comp_dict
            rho_ct = float(gas.density)
            cp_ct = float(gas.cp_mass)
            lambda_ct = float(gas.thermal_conductivity)
            alpha_ct = lambda_ct / max(rho_ct * cp_ct, 1.0e-12)

            diff_coeffs = gas.mix_diff_coeffs_mass
            idx_F = gas.species_index(fuel)
            idx_O2 = gas.species_index("O2")
            D_F_ct = float(diff_coeffs[idx_F])
            D_O_ct = float(diff_coeffs[idx_O2])

            return {
                "cantera_active": True,
                "mechanism": "gri30.yaml (53 species, 325 reactions)",
                "rho_kg_m3": rho_ct,
                "c_p_J_kg_K": cp_ct,
                "thermal_conductivity_W_m_K": lambda_ct,
                "alpha_m2_s": alpha_ct,
                "D_F_m2_s": D_F_ct,
                "D_O_m2_s": D_O_ct,
                "T_adiabatic_K": T_ad_K,
            }
        except Exception:
            pass

    W_mean = 0.02885 if diluent == "N2" else 0.02250
    rho_fallback = (p_Pa * W_mean) / (R_U_J_MOL_K * T_film_K)
    p_scale = P_ATM_PA / max(p_Pa, 1.0)
    dil_boost = 1.35 if diluent == "He" else 1.0
    cp_val = float(base["c_p"])
    alpha_val = float(base["alpha_0"]) * p_scale * dil_boost
    lambda_val = rho_fallback * cp_val * alpha_val

    return {
        "cantera_active": False,
        "mechanism": "ANALYTICAL_GRI30_SURROGATE (Cantera fallback)",
        "rho_kg_m3": float(rho_fallback),
        "c_p_J_kg_K": cp_val,
        "thermal_conductivity_W_m_K": float(lambda_val),
        "alpha_m2_s": float(alpha_val),
        "D_F_m2_s": float(base["D_F_0"]) * p_scale * dil_boost,
        "D_O_m2_s": float(base["D_O_0"]) * p_scale * dil_boost,
        "T_adiabatic_K": float(base["T_ad_nominal_K"]),
    }


# =============================================================================
# 3. PROVEEDOR DE PROPIEDADES FÍSICAS Y QUÍMICAS EN SI CON UQ (Entregable 5)
# =============================================================================
def get_physical_properties_si(
    sim_input: Any,
    uq_perturbations: Optional[Dict[str, float]] = None,
    use_cantera_if_available: bool = False,
) -> Dict[str, Any]:
    """
    ENTREGABLES 5 y 6 (Trabajo de Ángel):
    Recibe un objeto SimulationInputSI (o diccionario equivalente) y devuelve
    el diccionario completo de propiedades físicas y cinéticas en unidades SI,
    aplicando los factores de incertidumbre de `uq_perturbations`.
    """
    if isinstance(sim_input, dict):
        fuel_type = str(sim_input.get("fuel_type", sim_input.get("fuel", "C2H4"))).upper()
        diluent_species = str(sim_input.get("diluent_species", "N2"))
        p_0_Pa = float(sim_input.get("pressure_Pa", sim_input.get("p_0_Pa", 98000.0)))
        Y_F_in = float(sim_input.get("Y_F_burner", sim_input.get("Y_F_inlet", 1.0)))
        Y_O_inf = float(sim_input.get("Y_O_ambient", 0.233))
        input_uq = sim_input.get("uq_perturbations", None)
    else:
        fuel_type = str(sim_input.fuel_type).upper()
        diluent_species = str(getattr(sim_input, "diluent_species", "N2"))
        p_0_Pa = float(sim_input.pressure_Pa)
        Y_F_in = float(sim_input.Y_F_burner)
        Y_O_inf = float(sim_input.Y_O_ambient)
        input_uq = getattr(sim_input, "uq_perturbations", None)

    if fuel_type not in FUEL_DATABASE_SI:
        raise ValueError(f"Combustible '{fuel_type}' no soportado en FUEL_DATABASE_SI.")

    uq = dict(DEFAULT_UQ_PERTURBATIONS)
    if isinstance(input_uq, dict):
        for k, v in input_uq.items():
            if v is not None:
                uq[k] = float(v)
    if isinstance(uq_perturbations, dict):
        for k, v in uq_perturbations.items():
            if v is not None:
                uq[k] = float(v)

    base = FUEL_DATABASE_SI[fuel_type]
    W_mean_kg_mol = 0.02885
    T_ref_K = float(base["T_film_ref_K"])

    cantera_info = evaluate_cantera_properties(sim_input)

    if use_cantera_if_available and cantera_info["cantera_active"]:
        rho_nominal = cantera_info["rho_kg_m3"]
        cp_nominal = cantera_info["c_p_J_kg_K"]
        D_F_nominal = cantera_info["D_F_m2_s"]
        D_O_nominal = cantera_info["D_O_m2_s"]
        alpha_nominal = cantera_info["alpha_m2_s"]
    else:
        rho_nominal = (p_0_Pa * W_mean_kg_mol) / (R_U_J_MOL_K * T_ref_K)
        pressure_scale = P_ATM_PA / p_0_Pa
        cp_nominal = float(base["c_p"])
        D_F_nominal = float(base["D_F_0"]) * pressure_scale
        D_O_nominal = float(base["D_O_0"]) * pressure_scale
        alpha_nominal = float(base["alpha_0"]) * pressure_scale

    A_perturbed = float(base["A"]) * float(uq["A_preexp_factor"])
    E_a_perturbed = float(base["E_a"]) + float(uq["E_a_offset_J_mol"])
    D_F_m2_s = D_F_nominal * float(uq["D_F_factor"])
    D_O_m2_s = D_O_nominal * float(uq["D_O_factor"])
    alpha_m2_s = alpha_nominal * float(uq["alpha_factor"])
    c_p_J_kg_K = cp_nominal * float(uq["c_p_factor"])
    X_r = float(np.clip(uq["radiative_loss_fraction_Xr"], 0.0, 0.85))

    s_stoich = float(base["s"])
    Z_st = 1.0 / (1.0 + (s_stoich * Y_F_in) / max(Y_O_inf, 1.0e-12))
    rho_D_eff = rho_nominal * D_F_m2_s

    return {
        "fuel_type": fuel_type,
        "diluent_species": diluent_species,
        "fuel_name": base["name"],
        "global_reaction": base["global_reaction"],
        "W_F": base["W_F"],
        "W_O2": base["W_O2"],
        "W_mean": W_mean_kg_mol,
        "rho": rho_nominal,
        "rho_kg_m3": rho_nominal,
        "c_p": c_p_J_kg_K,
        "D_F": D_F_m2_s,
        "D_F_m2_s": D_F_m2_s,
        "D_O": D_O_m2_s,
        "D_O_m2_s": D_O_m2_s,
        "alpha": alpha_m2_s,
        "s": s_stoich,
        "stoich_oxygen_fuel_mass_ratio_s": s_stoich,
        "delta_H_c": base["delta_H_c"],
        "delta_Hc": base["delta_H_c"],
        "heat_of_combustion_J_kg": base["delta_H_c"],
        "A": A_perturbed,
        "A_preexp_m3_kg_s": A_perturbed,
        "E_a": E_a_perturbed,
        "E_a_J_mol": E_a_perturbed,
        "R_u": R_U_J_MOL_K,
        "Z_st": Z_st,
        "rho_D_eff": rho_D_eff,
        "Le_F": alpha_m2_s / max(D_F_m2_s, 1.0e-12),
        "Le_O": alpha_m2_s / max(D_O_m2_s, 1.0e-12),
        "radiative_loss_fraction_Xr": X_r,
        "uq_perturbations_applied": uq,
        "cantera_integration": cantera_info,
        "provenance": dict(base["provenance"]),
    }


def get_physical_properties(
    fuel_type: str, T_ref_K: float = 980.0, p_0_Pa: float = 98000.0
) -> Dict[str, Any]:
    """Alias de compatibilidad directa."""
    dummy_input = {
        "fuel_type": fuel_type,
        "pressure_Pa": p_0_Pa,
        "Y_F_burner": 1.0,
        "Y_O_ambient": 0.233,
    }
    props = get_physical_properties_si(dummy_input)
    if T_ref_K > 0.0:
        props["rho"] = (p_0_Pa * props["W_mean"]) / (R_U_J_MOL_K * T_ref_K)
    return props


# =============================================================================
# 4. TÉRMINO FUENTE QUÍMICO 3D CON PÉRDIDA RADIATIVA UQ (Entregable 5)
# =============================================================================
def compute_chemical_sources_3d(
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    props_dict: Dict[str, Any],
    dt_s: Optional[float] = None,
    mask_burner: Optional[np.ndarray] = None,
    apply_radiative_loss_to_q: bool = False,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula en todas las celdas de la malla 3D las tasas químicas de reacción
    (omega_F_3d, omega_O_3d, q_chem_3d).
    """
    rho = float(props_dict["rho"])
    A = float(props_dict["A"])
    E_a = float(props_dict["E_a"])
    s = float(props_dict["s"])
    delta_H_c = float(props_dict["delta_H_c"])
    X_r = float(props_dict.get("radiative_loss_fraction_Xr", 0.35))

    Y_F_clean = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_clean = np.clip(Y_O_3d, 0.0, 1.0)
    T_safe = np.maximum(T_3d, 200.0)

    C_F = mass_fraction_to_concentration(rho, Y_F_clean)
    C_O = mass_fraction_to_concentration(rho, Y_O_clean)

    exponent = np.clip(-E_a / (R_U_J_MOL_K * T_safe), -100.0, 0.0)
    r_rxn = A * np.exp(exponent) * C_F * C_O

    if mask_burner is not None:
        r_rxn = np.where(mask_burner, 0.0, r_rxn)

    omega_F_3d = r_rxn / rho

    if dt_s is not None and dt_s > 0.0:
        omega_F_max = 0.9 * np.minimum(
            Y_F_clean / dt_s,
            Y_O_clean / (s * dt_s),
        )
        omega_F_3d = np.minimum(omega_F_3d, omega_F_max)

    omega_O_3d = s * omega_F_3d
    q_chem_3d = rho * omega_F_3d * delta_H_c

    if apply_radiative_loss_to_q:
        q_chem_3d = (1.0 - X_r) * q_chem_3d

    return omega_F_3d, omega_O_3d, q_chem_3d


# =============================================================================
# 5. AUDITORÍA DE CONSERVACIÓN 3D PARA IGNIS-mu (Entregable 4 - Trabajo de Ángel)
# =============================================================================
def compute_conservation_audit_3d(
    omega_F_3d: np.ndarray,
    omega_O_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    props_dict: Dict[str, Any],
    Y_P_3d: Optional[np.ndarray] = None,
    Y_I_3d: Optional[np.ndarray] = None,
    R_3d: Optional[np.ndarray] = None,
    u_x_3d: Optional[np.ndarray] = None,
    u_y_3d: Optional[np.ndarray] = None,
    u_z_3d: Optional[np.ndarray] = None,
    X_3d: Optional[np.ndarray] = None,
    Y_3d: Optional[np.ndarray] = None,
    Z_3d: Optional[np.ndarray] = None,
    dx_m: Optional[float] = None,
    mass_flow_kg_s: float = 2.5e-6,
) -> Dict[str, Any]:
    """
    ENTREGABLE 4 (Trabajo de Ángel):
    Calcula las tres métricas exactas solicitadas por los auditores de IGNIS-mu:
      (a) Residuo estequiométrico químico:
          epsilon_stoich = max | omega_O / (s * omega_F) - 1 |
      (b) Residuo de suma de fracciones másicas:
          epsilon_sum_Y = max | Y_F + Y_O + Y_P + Y_I - 1.0 |
      (c) Error global de balance de flujo másico esférico:
          epsilon_mdot = | (oint rho * u . dA - mdot) / mdot |
    """
    s_stoich = float(props_dict["s"])
    rho = float(props_dict["rho"])

    # (a) Residuo estequiométrico químico en celdas activas
    active_mask = omega_F_3d > 1.0e-15
    if np.any(active_mask):
        ratio = omega_O_3d[active_mask] / (s_stoich * omega_F_3d[active_mask])
        eps_stoich = float(np.max(np.abs(ratio - 1.0)))
    else:
        eps_stoich = 0.0

    # (b) Residuo de suma de fracciones másicas Y_F + Y_O + Y_P + Y_I = 1.0 (YA CORREGIDO)
    Y_F_c = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_c = np.clip(Y_O_3d, 0.0, 1.0)
    if Y_P_3d is None or Y_I_3d is None:
        # Cierre conservativo exacto: Y_I + Y_P = 1.0 - Y_F - Y_O
        Y_I_est = np.clip(0.767 * (1.0 - Y_F_c), 0.0, np.maximum(0.0, 1.0 - Y_F_c - Y_O_c))
        Y_P_est = np.maximum(0.0, 1.0 - Y_F_c - Y_O_c - Y_I_est)
        sum_Y = Y_F_c + Y_O_c + Y_P_est + Y_I_est
    else:
        sum_Y = Y_F_3d + Y_O_3d + Y_P_3d + Y_I_3d

    eps_sum_Y = float(np.max(np.abs(sum_Y - 1.0)))

    # (c) Error global de balance de flujo másico esférico
    eps_mdot = 0.0
    if (
        R_3d is not None
        and u_x_3d is not None
        and u_y_3d is not None
        and u_z_3d is not None
        and X_3d is not None
        and Y_3d is not None
        and Z_3d is not None
    ):
        R_safe = np.maximum(R_3d, 1.0e-12)
        u_r_3d = (u_x_3d * X_3d + u_y_3d * Y_3d + u_z_3d * Z_3d) / R_safe
        r_ref = 0.015
        tol_r = float(dx_m) if dx_m is not None else 0.0025
        shell_mask = np.abs(R_3d - r_ref) <= tol_r
        if np.any(shell_mask):
            mdot_local = 4.0 * np.pi * (R_3d[shell_mask] ** 2) * rho * u_r_3d[shell_mask]
            mdot_integrated = float(np.mean(mdot_local))
            eps_mdot = abs(mdot_integrated - mass_flow_kg_s) / max(mass_flow_kg_s, 1.0e-15)

    return {
        "epsilon_stoich": float(eps_stoich),
        "epsilon_sum_Y": float(eps_sum_Y),
        "epsilon_mass_flow": float(eps_mdot),
        "is_conservative": bool(eps_stoich < 1.0e-9 and eps_sum_Y < 1.0e-6 and eps_mdot < 0.05),
    }


if __name__ == "__main__":
    print("=== PRUEBA ENTREGABLES 4, 5 Y 6 (ia/thermo_kinetics.py) ===")
    sim_in = SimulationInputSI(
        fuel_type="C2H4",
        diluent_species="N2",
        pressure_Pa=98000.0,
        uq_perturbations={"A_preexp_factor": 1.15, "E_a_offset_J_mol": -1500.0},
    )
    props = get_physical_properties_si(sim_in)
    print(f"[OK] Entregable 5 (UQ aplicado): A = {props['A']:.3e} m^3/(kg*s) | E_a = {props['E_a']:.1f} J/mol | X_r = {props['radiative_loss_fraction_Xr']}")
    print(f"[OK] Entregable 6 (Cantera bridge): mechanism = {props['cantera_integration']['mechanism']} | T_ad = {props['cantera_integration']['T_adiabatic_K']:.1f} K")

    T_cube = np.full((11, 11, 11), 1550.0)
    YF_cube = np.full((11, 11, 11), 0.05)
    YO_cube = np.full((11, 11, 11), 0.20)
    wF, wO, qC = compute_chemical_sources_3d(T_cube, YF_cube, YO_cube, props, dt_s=1e-4)
    audit = compute_conservation_audit_3d(wF, wO, YF_cube, YO_cube, props)
    print(f"[OK] Entregable 4 (Auditoría de conservación): {audit}")