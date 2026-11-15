# -*- coding: utf-8 -*-
"""
ARCHIVO: ia/contract_si.py
RESPONSABLES: Ángel ("Lito" / "Perrita") & Rodolfo ("Tornolfo")
DESCRIPCIÓN: Contrato de Integración en Unidades del Sistema Internacional (SI)
             para acoplamiento con IGNIS-mu (PSI-23).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Tuple, List, Optional
import numpy as np

R_U_J_MOL_K: float = 8.314462618
R_U: float = R_U_J_MOL_K

SPECIES_ORDER: Tuple[str, ...] = ("F", "O2", "P", "N2")

VALID_PROVENANCE_TAGS: Tuple[str, ...] = (
    "MEDIDO_EXPERIMENTALMENTE",
    "CALCULADO_DE_DATOS_EXP",
    "ESTIMADO_FUENTE_CIENTIFICA",
    "SUPUESTO_SIMPLIFICACION",
    "NO_DISPONIBLE",
)
VALID_PROVENANCE = list(VALID_PROVENANCE_TAGS)

VALID_FUELS: Tuple[str, ...] = ("C2H4", "CH4", "H2")
VALID_DILUENTS: Tuple[str, ...] = ("N2", "He")

MOLECULAR_WEIGHTS_KG_MOL: Dict[str, float] = {
    "C2H4": 0.028053,
    "CH4": 0.016043,
    "H2": 0.002016,
    "O2": 0.031999,
    "N2": 0.0280134,
    "He": 0.0040026,
}

DEFAULT_UNITS_MAP: Dict[str, str] = {
    "pressure_Pa": "Pa",
    "T_initial_K": "K",
    "T_burner_K": "K",
    "mass_flow_kg_s": "kg/s",
    "burner_radius_m": "m",
    "domain_half_width_m": "m",
    "total_time_s": "s",
    "Y_F_burner": "-",
    "Y_I_burner": "-",
    "Y_O_ambient": "-",
    "grid_nodes_per_axis": "-",
}

DEFAULT_UQ_PERTURBATIONS: Dict[str, float] = {
    "A_preexp_factor": 1.0,
    "E_a_offset_J_mol": 0.0,
    "D_F_factor": 1.0,
    "D_O_factor": 1.0,
    "alpha_factor": 1.0,
    "c_p_factor": 1.0,
    "radiative_loss_fraction_Xr": 0.35,
    "residual_gravity_m_s2": 0.0,
}


def convert_mfc_instrumental_to_si(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    converted = dict(raw_dict)
    fuel = str(converted.get("fuel_type", converted.get("fuel", "C2H4"))).upper()
    diluent = str(converted.get("diluent_species", "N2")).upper()
    Y_F = float(converted.get("Y_F_burner", converted.get("Y_F_inlet", 1.0)))
    Y_I = max(0.0, 1.0 - Y_F)

    if "pressure_Pa" not in converted:
        if "pressure_psia" in converted:
            converted["pressure_Pa"] = float(converted["pressure_psia"]) * 6894.757293
        elif "pressure_atm" in converted:
            converted["pressure_Pa"] = float(converted["pressure_atm"]) * 101325.0

    if "T_initial_K" not in converted and "T_ambient_C" in converted:
        converted["T_initial_K"] = float(converted["T_ambient_C"]) + 273.15
    if "T_burner_K" not in converted and "T_burner_C" in converted:
        converted["T_burner_K"] = float(converted["T_burner_C"]) + 273.15

    if "mass_flow_kg_s" not in converted:
        if "mass_flow_mg_s" in converted:
            converted["mass_flow_kg_s"] = float(converted["mass_flow_mg_s"]) * 1.0e-6
        elif "flow_sccm" in converted:
            q_m3_s = float(converted["flow_sccm"]) * 1.0e-6 / 60.0
            W_fuel = MOLECULAR_WEIGHTS_KG_MOL.get(fuel, 0.028053)
            W_dil = MOLECULAR_WEIGHTS_KG_MOL.get(diluent, 0.0280134)
            W_mix = 1.0 / ((Y_F / W_fuel) + (Y_I / W_dil)) if Y_F < 1.0 else W_fuel
            rho_std = (101325.0 * W_mix) / (R_U_J_MOL_K * 273.15)
            converted["mass_flow_kg_s"] = q_m3_s * rho_std

    return converted


@dataclass
class SimulationInputSI:
    fuel_type: str = "C2H4"
    diluent_species: str = "N2"
    Y_F_burner: float = 1.0
    Y_I_burner: float = 0.0
    Y_O_ambient: float = 0.233
    T_initial_K: float = 298.15
    T_burner_K: float = 300.0
    pressure_Pa: float = 98000.0
    mass_flow_kg_s: float = 2.5e-6
    burner_radius_m: float = 0.00318
    domain_half_width_m: float = 0.035
    grid_nodes_per_axis: int = 41
    total_time_s: float = 1.2
    experiment_id: Optional[str] = None
    mfc_config_id: Optional[str] = None
    uq_perturbations: Dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_UQ_PERTURBATIONS)
    )
    units_map: Dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_UNITS_MAP)
    )

    def __post_init__(self) -> None:
        self.fuel_type = str(self.fuel_type).strip().upper()
        if self.diluent_species not in ("N2", "He"):
            if str(self.diluent_species).strip().upper() == "HE":
                self.diluent_species = "He"
            else:
                self.diluent_species = "N2"
        self.Y_I_burner = round(max(0.0, 1.0 - float(self.Y_F_burner)), 8)

        merged_uq = dict(DEFAULT_UQ_PERTURBATIONS)
        if isinstance(self.uq_perturbations, dict):
            for k, v in self.uq_perturbations.items():
                if v is not None:
                    merged_uq[k] = float(v)
        self.uq_perturbations = merged_uq

        merged_units = dict(DEFAULT_UNITS_MAP)
        if isinstance(self.units_map, dict):
            merged_units.update(self.units_map)
        self.units_map = merged_units

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def mass_fraction_to_concentration(rho_kg_m3: float, Y: Any) -> Any:
    return rho_kg_m3 * Y


def check_burner_grid_resolution(
    burner_radius_m: float = 0.00318,
    domain_half_width_m: float = 0.035,
    grid_nodes_per_axis: int = 41,
) -> Dict[str, Any]:
    dx_m = (2.0 * float(domain_half_width_m)) / max(int(grid_nodes_per_axis) - 1, 1)
    burner_diameter_m = 2.0 * float(burner_radius_m)
    nodes_across_diameter = burner_diameter_m / max(dx_m, 1.0e-12)
    meets_optimal_5_nodes = nodes_across_diameter >= 5.0
    recommended_N = int(np.ceil((2.0 * domain_half_width_m) / (burner_diameter_m / 5.0))) + 1
    if recommended_N % 2 == 0:
        recommended_N += 1

    return {
        "dx_m": round(float(dx_m), 6),
        "burner_diameter_m": round(float(burner_diameter_m), 6),
        "nodes_across_burner_diameter": round(float(nodes_across_diameter), 2),
        "meets_5_to_7_nodes_target": bool(meets_optimal_5_nodes),
        "recommended_grid_nodes_per_axis": int(recommended_N),
    }


def validate_user_input_si(input_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if not isinstance(input_dict, dict):
        return False, ["El parámetro de entrada debe ser un diccionario JSON válido."]

    data = convert_mfc_instrumental_to_si(input_dict)

    fuel = str(data.get("fuel_type", data.get("fuel", "C2H4"))).strip().upper()
    if fuel not in VALID_FUELS:
        errors.append(f"Combustible inválido '{fuel}'. Solo acepta: {VALID_FUELS}.")

    diluent = str(data.get("diluent_species", "N2")).strip()
    if diluent.upper() == "HE":
        diluent = "He"
    elif diluent.upper() == "N2":
        diluent = "N2"
    if diluent not in VALID_DILUENTS:
        errors.append(f"Especie diluyente inválida '{diluent}'. Solo acepta: {VALID_DILUENTS}.")

    Y_F = data.get("Y_F_burner", data.get("Y_F_inlet", 1.0))
    try:
        Y_F = float(Y_F)
        if Y_F > 1.0:
            errors.append(f"Error de unidades SI en Y_F_burner ({Y_F}): debe estar en [0.0, 1.0].")
        elif Y_F < 0.01:
            errors.append(f"Fuera de rango en Y_F_burner ({Y_F}): debe estar en [0.01, 1.0].")
    except (ValueError, TypeError):
        errors.append("Y_F_burner debe ser un número flotante válido.")

    Y_O = data.get("Y_O_ambient", 0.233)
    try:
        Y_O = float(Y_O)
        if Y_O > 1.0:
            errors.append(f"Error de unidades SI en Y_O_ambient ({Y_O}): debe estar en [0.0, 1.0].")
        elif Y_O < 0.05:
            errors.append(f"Fuera de rango en Y_O_ambient ({Y_O}): debe estar en [0.05, 1.0].")
    except (ValueError, TypeError):
        errors.append("Y_O_ambient debe ser un número flotante válido.")

    T_init = data.get("T_initial_K", data.get("T_ambient_K", 298.15))
    T_burn = data.get("T_burner_K", 300.0)
    for name, val in [("T_initial_K", T_init), ("T_burner_K", T_burn)]:
        try:
            val_f = float(val)
            if val_f < 150.0:
                errors.append(f"Error de unidades SI en {name} ({val_f}): debe estar en Kelvin [K].")
            elif not (250.0 <= val_f <= 1000.0):
                errors.append(f"Fuera de rango en {name} ({val_f} K): debe estar entre 250 K y 1000 K.")
        except (ValueError, TypeError):
            errors.append(f"{name} debe ser un número flotante válido en Kelvin [K].")

    p_Pa = data.get("pressure_Pa", data.get("p_initial_Pa", 98000.0))
    try:
        p_Pa = float(p_Pa)
        if p_Pa < 500.0:
            errors.append(f"Error de unidades SI en pressure_Pa ({p_Pa}): debe estar en Pascales [Pa].")
        elif not (10000.0 <= p_Pa <= 300000.0):
            errors.append(f"Fuera de rango en pressure_Pa ({p_Pa} Pa): debe estar entre 10,000 y 300,000 Pa.")
    except (ValueError, TypeError):
        errors.append("pressure_Pa debe ser un número flotante válido en Pascales [Pa].")

    mdot = data.get("mass_flow_kg_s", 2.5e-6)
    try:
        mdot = float(mdot)
        if mdot >= 0.01:
            errors.append(f"Error de unidades SI en mass_flow_kg_s ({mdot}): debe estar en [kg/s].")
        elif not (1.0e-8 <= mdot <= 1.0e-3):
            errors.append(f"Fuera de rango en mass_flow_kg_s ({mdot} kg/s): debe estar en [1e-8, 1e-3] kg/s.")
    except (ValueError, TypeError):
        errors.append("mass_flow_kg_s debe ser un número flotante válido en [kg/s].")

    r_b = data.get("burner_radius_m", 0.00318)
    try:
        r_b = float(r_b)
        if r_b >= 0.1:
            errors.append(f"Error de unidades SI en burner_radius_m ({r_b}): debe estar en metros [m].")
        elif not (0.0005 <= r_b <= 0.02):
            errors.append(f"Fuera de rango en burner_radius_m ({r_b} m): debe estar entre 0.0005 y 0.02 m.")
    except (ValueError, TypeError):
        errors.append("burner_radius_m debe ser un número flotante válido en metros [m].")

    L_dom = data.get("domain_half_width_m", 0.035)
    try:
        L_dom = float(L_dom)
        if not (0.01 <= L_dom <= 0.25):
            errors.append(f"Fuera de rango en domain_half_width_m ({L_dom} m): debe estar entre 0.01 y 0.25 m.")
        if isinstance(r_b, float) and L_dom <= 3.0 * r_b:
            errors.append("Incoherencia geométrica: domain_half_width_m debe ser >= 3 * burner_radius_m.")
    except (ValueError, TypeError):
        errors.append("domain_half_width_m debe ser un número flotante válido en metros [m].")

    N_nodes = data.get("grid_nodes_per_axis", 41)
    try:
        N_nodes = int(N_nodes)
        if not (15 <= N_nodes <= 121):
            errors.append(f"Fuera de rango en grid_nodes_per_axis ({N_nodes}): debe estar entre 15 y 121.")
    except (ValueError, TypeError):
        errors.append("grid_nodes_per_axis debe ser un número entero válido.")

    t_tot = data.get("total_time_s", 1.2)
    try:
        t_tot = float(t_tot)
        if not (0.001 <= t_tot <= 30.0):
            errors.append(f"Fuera de rango en total_time_s ({t_tot} s): debe estar entre 0.001 y 30.0 s.")
    except (ValueError, TypeError):
        errors.append("total_time_s debe ser un número flotante válido en segundos [s].")

    uq_dict = data.get("uq_perturbations", {})
    if uq_dict is not None:
        if not isinstance(uq_dict, dict):
            errors.append("uq_perturbations debe ser un diccionario.")
        else:
            xr = float(uq_dict.get("radiative_loss_fraction_Xr", 0.35))
            if not (0.0 <= xr <= 0.85):
                errors.append(f"radiative_loss_fraction_Xr ({xr}) fuera de rango [0.0, 0.85].")

    return (len(errors) == 0), errors


def validate_input_si(input_dict: Dict[str, Any]) -> SimulationInputSI:
    if isinstance(input_dict, SimulationInputSI):
        return input_dict

    converted_dict = convert_mfc_instrumental_to_si(input_dict)
    is_valid, error_messages = validate_user_input_si(converted_dict)
    if not is_valid:
        joined_errors = "\n  - ".join(error_messages)
        raise ValueError(f"Se detectaron errores en la validación SI de entrada:\n  - {joined_errors}")

    dil_raw = str(converted_dict.get("diluent_species", "N2")).strip()
    dil_clean = "He" if dil_raw.upper() == "HE" else "N2"
    Y_F_val = float(converted_dict.get("Y_F_burner", converted_dict.get("Y_F_inlet", 1.0)))

    return SimulationInputSI(
        fuel_type=str(converted_dict.get("fuel_type", converted_dict.get("fuel", "C2H4"))).upper(),
        diluent_species=dil_clean,
        Y_F_burner=Y_F_val,
        Y_I_burner=round(max(0.0, 1.0 - Y_F_val), 8),
        Y_O_ambient=float(converted_dict.get("Y_O_ambient", 0.233)),
        T_initial_K=float(converted_dict.get("T_initial_K", converted_dict.get("T_ambient_K", 298.15))),
        T_burner_K=float(converted_dict.get("T_burner_K", 300.0)),
        pressure_Pa=float(converted_dict.get("pressure_Pa", converted_dict.get("p_initial_Pa", 98000.0))),
        mass_flow_kg_s=float(converted_dict.get("mass_flow_kg_s", 2.5e-6)),
        burner_radius_m=float(converted_dict.get("burner_radius_m", 0.00318)),
        domain_half_width_m=float(converted_dict.get("domain_half_width_m", 0.035)),
        grid_nodes_per_axis=int(converted_dict.get("grid_nodes_per_axis", 41)),
        total_time_s=float(converted_dict.get("total_time_s", 1.2)),
        experiment_id=converted_dict.get("experiment_id", None),
        mfc_config_id=converted_dict.get("mfc_config_id", None),
        uq_perturbations=dict(converted_dict.get("uq_perturbations", DEFAULT_UQ_PERTURBATIONS)),
    )


def assert_valid_3d_fields(
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    tol: float = 1.0e-6
) -> bool:
    for name, arr in [("T_3d", T_3d), ("Y_F_3d", Y_F_3d), ("Y_O_3d", Y_O_3d)]:
        if not isinstance(arr, np.ndarray):
            raise TypeError(f"El campo {name} debe ser un arreglo numpy.ndarray.")
        if arr.ndim != 3:
            raise ValueError(f"El campo {name} debe ser tridimensional (ndim=3).")
        if not np.all(np.isfinite(arr)):
            raise FloatingPointError(f"El campo {name} contiene NaN o Inf.")

    if not (T_3d.shape == Y_F_3d.shape == Y_O_3d.shape):
        raise ValueError("Incompatibilidad de dimensiones entre T_3d, Y_F_3d y Y_O_3d.")

    if np.min(T_3d) < 150.0 or np.max(T_3d) > 5000.0:
        raise ValueError("Temperatura 3D fuera de límites físicos [150, 5000] K.")

    for name, arr in [("Y_F_3d", Y_F_3d), ("Y_O_3d", Y_O_3d)]:
        if float(np.min(arr)) < -tol or float(np.max(arr)) > 1.0 + tol:
            raise ValueError(f"Fracción másica {name} fuera de [0.0, 1.0].")

    return True


if __name__ == "__main__":
    print("=== PRUEBA ENTREGABLES 2 Y 5 (ia/contract_si.py) ===")
    mfc_raw = {
        "fuel_type": "C2H4",
        "diluent_species": "He",
        "Y_F_burner": 0.60,
        "Y_O_ambient": 0.233,
        "pressure_psia": 14.7,
        "T_ambient_C": 25.0,
        "T_burner_C": 26.85,
        "flow_sccm": 120.0,
        "uq_perturbations": {
            "A_preexp_factor": 1.10,
            "radiative_loss_fraction_Xr": 0.40,
        },
    }
    sim_si = validate_input_si(mfc_raw)
    print(f"[OK] Conversión MFC -> SI: p = {sim_si.pressure_Pa:.1f} Pa | T_0 = {sim_si.T_initial_K:.2f} K | mdot = {sim_si.mass_flow_kg_s:.3e} kg/s")
    print(f"[OK] Diluyente: {sim_si.diluent_species} con Y_I_burner = {sim_si.Y_I_burner:.2f}")
    print(f"[OK] units_map: {sim_si.units_map}")
    print(f"[OK] uq_perturbations: {sim_si.uq_perturbations}")