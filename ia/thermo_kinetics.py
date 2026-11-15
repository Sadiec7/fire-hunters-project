# -*- coding: utf-8 -*-
"""
ia/thermo_kinetics.py
Propiedades Termofísicas en SI y Cinética Química Global 3D Diferenciada por Combustible.
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame).
Autor: Ángel ("Lito" / "Perrita")
"""

import os
import sys
from typing import Dict, Any, Tuple, Optional
import numpy as np

# Permitir importación tanto al correr "python ia/thermo_kinetics.py" como desde la raíz
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from ia.contract_si import (
        R_U_J_MOL_K,
        SimulationInputSI,
        mass_fraction_to_concentration,
    )
except ImportError:
    from contract_si import (
        R_U_J_MOL_K,
        SimulationInputSI,
        mass_fraction_to_concentration,
    )

# =============================================================================
# 1. BASE DE DATOS MAESTRA POR COMBUSTIBLE EN UNIDADES SI (Tabla 6.1 Oficial)
# =============================================================================
P_ATM_PA: float = 101325.0       # Presión atmosférica estándar de referencia [Pa]
W_O2_KG_MOL: float = 0.03200     # Peso molecular del oxígeno O2 [kg/mol]
W_N2_KG_MOL: float = 0.0280134   # Peso molecular del nitrógeno N2 [kg/mol]

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
        "D_F_0": 3.8e-5,             # Difusividad efectiva del combustible a 1 atm [m^2/s]
        "D_O_0": 4.0e-5,             # Difusividad efectiva del O2 a 1 atm [m^2/s]
        "alpha_0": 4.2e-5,           # Difusividad térmica efectiva a 1 atm [m^2/s]
        "c_p": 1250.0,               # Capacidad calorífica media de mezcla [J/(kg*K)]
        "T_film_ref_K": 980.0,       # Temperatura media de película para evaluar rho [K]
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
        "D_F_0": 4.5e-5,             # Difusividad efectiva del metano a 1 atm [m^2/s]
        "D_O_0": 4.0e-5,             # Difusividad efectiva del O2 a 1 atm [m^2/s]
        "alpha_0": 4.3e-5,           # Difusividad térmica efectiva a 1 atm [m^2/s]
        "c_p": 1300.0,               # Capacidad calorífica media de mezcla [J/(kg*K)]
        "T_film_ref_K": 960.0,       # Temperatura media de película [K]
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
        "D_F_0": 1.4e-4,             # Alta difusividad molecular del H2 (Le < 1) [m^2/s]
        "D_O_0": 4.2e-5,             # Difusividad efectiva del O2 a 1 atm [m^2/s]
        "alpha_0": 5.2e-5,           # Difusividad térmica efectiva a 1 atm [m^2/s]
        "c_p": 1450.0,               # Capacidad calorífica media de mezcla [J/(kg*K)]
        "T_film_ref_K": 950.0,       # Temperatura media de película [K]
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

# Alias de compatibilidad entre ambos manuales
FUEL_DATABASE = FUEL_DATABASE_SI


# =============================================================================
# 2. PROVEEDOR DE PROPIEDADES FÍSICAS Y QUÍMICAS EN SI (Bloque 3 - Tarea A3.2)
# =============================================================================
def get_physical_properties_si(sim_input: Any) -> Dict[str, Any]:
    """
    Recibe un objeto SimulationInputSI (o un diccionario equivalente) y devuelve
    el diccionario completo de propiedades físicas y cinéticas en unidades SI:
    rho, c_p, D_F, D_O, alpha, s, delta_H_c, A, E_a, Z_st, rho_D_eff y provenance.
    Escala las difusividades inversamente con la presión (D ~ p_atm / p_0) y calcula
    la densidad efectiva mediante la ley de gas ideal a la temperatura de película.
    """
    if isinstance(sim_input, dict):
        fuel_type = str(sim_input.get("fuel_type", sim_input.get("fuel", "C2H4")))
        p_0_Pa = float(sim_input.get("pressure_Pa", sim_input.get("p_0_Pa", 98000.0)))
        Y_F_in = float(sim_input.get("Y_F_burner", sim_input.get("Y_F_inlet", 1.0)))
        Y_O_inf = float(sim_input.get("Y_O_ambient", 0.233))
    else:
        fuel_type = sim_input.fuel_type
        p_0_Pa = sim_input.pressure_Pa
        Y_F_in = sim_input.Y_F_burner
        Y_O_inf = sim_input.Y_O_ambient

    if fuel_type not in FUEL_DATABASE_SI:
        raise ValueError(f"Combustible '{fuel_type}' no soportado en FUEL_DATABASE_SI.")

    base = FUEL_DATABASE_SI[fuel_type]

    # Peso molecular medio efectivo de la atmósfera de transporte (dominada por N2/O2)
    W_mean_kg_mol = 0.02885
    T_ref_K = base["T_film_ref_K"]

    # Densidad media de película por ley de gas ideal: rho = (p_0 * W_mean) / (R_u * T_ref)
    rho_kg_m3 = (p_0_Pa * W_mean_kg_mol) / (R_U_J_MOL_K * T_ref_K)

    # Escalado de coeficientes de difusión con la presión de la cámara (D proporcional a p_atm / p_0)
    pressure_scale = P_ATM_PA / p_0_Pa
    D_F_m2_s = base["D_F_0"] * pressure_scale
    D_O_m2_s = base["D_O_0"] * pressure_scale
    alpha_m2_s = base["alpha_0"] * pressure_scale

    # Fracción de mezcla estequiométrica Z_st = 1 / (1 + (s * Y_F_in) / Y_O_inf)
    s_stoich = base["s"]
    Z_st = 1.0 / (1.0 + (s_stoich * Y_F_in) / max(Y_O_inf, 1.0e-12))

    # Producto difusivo efectivo (rho * D)_eff coherente con la referencia 1D de Burke-Schumann
    rho_D_eff = rho_kg_m3 * D_F_m2_s

    return {
        "fuel_type": fuel_type,
        "fuel_name": base["name"],
        "global_reaction": base["global_reaction"],
        "W_F": base["W_F"],
        "W_O2": base["W_O2"],
        "W_mean": W_mean_kg_mol,
        "rho": rho_kg_m3,
        "c_p": base["c_p"],
        "D_F": D_F_m2_s,
        "D_O": D_O_m2_s,
        "alpha": alpha_m2_s,
        "s": s_stoich,
        "delta_H_c": base["delta_H_c"],
        "delta_Hc": base["delta_H_c"],  # Alias de compatibilidad
        "A": base["A"],
        "E_a": base["E_a"],
        "R_u": R_U_J_MOL_K,
        "Z_st": Z_st,
        "rho_D_eff": rho_D_eff,
        "Le_F": alpha_m2_s / D_F_m2_s,
        "Le_O": alpha_m2_s / D_O_m2_s,
        "provenance": dict(base["provenance"]),
    }


def get_physical_properties(
    fuel_type: str, T_ref_K: float = 980.0, p_0_Pa: float = 98000.0
) -> Dict[str, Any]:
    """
    Alias de compatibilidad directa con la firma alternativa de proyecto_acme (1).pdf.
    """
    dummy_input = {
        "fuel_type": fuel_type,
        "pressure_Pa": p_0_Pa,
        "Y_F_burner": 1.0,
        "Y_O_ambient": 0.233,
    }
    props = get_physical_properties_si(dummy_input)
    if T_ref_K > 0.0:
        props["rho"] = (p_0_Pa * props["W_mean"]) / (R_U_J_MOL_K * T_ref_K)
        props["D_F"] = FUEL_DATABASE_SI[fuel_type]["D_F_0"] * (P_ATM_PA / p_0_Pa)
        props["D_O"] = FUEL_DATABASE_SI[fuel_type]["D_O_0"] * (P_ATM_PA / p_0_Pa)
        props["alpha"] = FUEL_DATABASE_SI[fuel_type]["alpha_0"] * (P_ATM_PA / p_0_Pa)
    return props


# =============================================================================
# 3. TÉRMINO FUENTE QUÍMICO 3D CON ESTEQUIOMETRÍA COHERENTE (Bloque 5 - A5.1)
# =============================================================================
def compute_chemical_sources_3d(
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    props_dict: Dict[str, Any],
    dt_s: Optional[float] = None,
    mask_burner: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula en todas las celdas de la malla 3D las tasas químicas de reacción
    usando una ley global de Arrhenius de 1 paso diferenciada por combustible:
      1) Recorta fracciones másicas a [0.0, 1.0].
      2) Convierte a concentraciones másicas: C_F = rho * Y_F, C_O = rho * Y_O [kg/m^3].
      3) Evalúa r_rxn = A * exp(-E_a / (R_u * T_3d)) * C_F * C_O [kg/(m^3 * s)].
      4) Calcula omega_F = r_rxn / rho [1/s].
      5) Aplica salvaguarda de positividad química si se entrega dt_s:
         omega_F <= 0.9 * min(Y_F / dt_s, Y_O / (s * dt_s)).
      6) Anula la reacción dentro del sólido poroso del quemador si se pasa mask_burner.
      7) Garantiza estequiometría coherente:
         omega_O = s * omega_F [1/s]
         q_chem  = rho * omega_F * delta_H_c [W/m^3]
    Devuelve la tupla (omega_F_3d, omega_O_3d, q_chem_3d).
    """
    rho = float(props_dict["rho"])
    A = float(props_dict["A"])
    E_a = float(props_dict["E_a"])
    s = float(props_dict["s"])
    delta_H_c = float(props_dict["delta_H_c"])

    # a) Recorte de seguridad de fracciones másicas a [0.0, 1.0]
    Y_F_clean = np.clip(Y_F_3d, 0.0, 1.0)
    Y_O_clean = np.clip(Y_O_3d, 0.0, 1.0)

    # b) Temperatura segura para el exponente de Arrhenius
    T_safe = np.maximum(T_3d, 200.0)

    # c) Concentraciones másicas [kg/m^3] (Sección 3.5 y 9.1)
    C_F = mass_fraction_to_concentration(rho, Y_F_clean)
    C_O = mass_fraction_to_concentration(rho, Y_O_clean)

    # d) Velocidad volumétrica de reacción de Arrhenius [kg/(m^3 * s)]
    exponent = np.clip(-E_a / (R_U_J_MOL_K * T_safe), -100.0, 0.0)
    r_rxn = A * np.exp(exponent) * C_F * C_O

    # Apagar reacción química dentro de la esfera sólida del quemador poroso
    if mask_burner is not None:
        r_rxn = np.where(mask_burner, 0.0, r_rxn)

    # e) Tasa de consumo de fracción másica de combustible [1/s]
    omega_F_3d = r_rxn / rho

    # f) Salvaguarda de positividad química por paso de tiempo dt_s
    if dt_s is not None and dt_s > 0.0:
        omega_F_max = 0.9 * np.minimum(
            Y_F_clean / dt_s,
            Y_O_clean / (s * dt_s),
        )
        omega_F_3d = np.minimum(omega_F_3d, omega_F_max)

    # g) Estequiometría coherente obligatoria (Sección 3.5)
    omega_O_3d = s * omega_F_3d
    q_chem_3d = rho * omega_F_3d * delta_H_c

    return omega_F_3d, omega_O_3d, q_chem_3d


# =============================================================================
# 4. BLOQUE DE PRUEBA DIRECTA EN TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=== PRUEBA DE TERMO-CINÉTICA 3D (ia/thermo_kinetics.py) ===")

    for fuel in ("C2H4", "CH4", "H2"):
        sim_in = SimulationInputSI(fuel_type=fuel, pressure_Pa=98000.0)
        props = get_physical_properties_si(sim_in)
        print(
            f"[OK] {props['fuel_name']}: s={props['s']:.3f} kgO2/kgF | "
            f"dHc={props['delta_H_c']:.3e} J/kg | D_F={props['D_F']:.3e} m^2/s | "
            f"rho={props['rho']:.3f} kg/m^3 | Z_st={props['Z_st']:.4f}"
        )

    # Prueba de reacción química 3D y conservación estequiométrica exacta
    sim_ref = SimulationInputSI(fuel_type="C2H4", pressure_Pa=98000.0)
    props_ref = get_physical_properties_si(sim_ref)

    T_test = np.full((10, 10, 10), 1500.0)
    YF_test = np.full((10, 10, 10), 0.06)
    YO_test = np.full((10, 10, 10), 0.20)

    wF, wO, q_chem = compute_chemical_sources_3d(
        T_test, YF_test, YO_test, props_ref, dt_s=1.0e-4
    )

    ratio_s = float(np.mean(wO / wF))
    ratio_q = float(np.mean(q_chem / (props_ref["rho"] * wF)))
    print(f"[OK] Verificación estequiométrica 3D:")
    print(f"     wO / wF = {ratio_s:.6f} (esperado s = {props_ref['s']:.6f})")
    print(f"     q_chem / (rho * wF) = {ratio_q:.4e} J/kg (esperado dHc = {props_ref['delta_H_c']:.4e} J/kg)")