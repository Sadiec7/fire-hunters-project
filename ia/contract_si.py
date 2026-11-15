"""
ia/contract_si.py
Contrato estricto del Sistema Internacional (SI) para el Gemelo Digital 3D s-Flame (PSI-23 / IGNIS-mu).
Actualizado con los Candados Epistémicos y de Calibración de la Etapa 2 (NUEVA_CHINGADERA.pdf - Punto 2, Tarea 2.A),
manteniendo 100% de compatibilidad hacia atrás con todos los módulos de la Etapa 1.
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
VALID_FUELS: Tuple[str, ...] = ("C2H4", "CH4", "H2", "H2_CH4_MIX")
VALID_DILUENTS: Tuple[str, ...] = ("N2", "HE")

# Etiquetas del Semáforo Epistémico (Etapa 2 - Punto 5)
VALID_EPISTEMIC_TAGS: Tuple[str, ...] = ("OBSERVED", "INFERRED", "UNVERIFIED")

# Niveles de verificación geométrica (Etapa 2 - Punto 1)
VALID_VERIFICATION_TIERS: Tuple[str, ...] = (
    "VERIFIED_DIMENSION",
    "GEOMETRIC_APPROXIMATION",
    "ILLUSTRATIVE_ONLY",
)

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
}

DEFAULT_UQ_PERTURBATIONS: Dict[str, Any] = {
    "A_preexp_factor": 1.0,
    "E_a_offset_J_mol": 0.0,
    "D_F_factor": 1.0,
    "D_O_factor": 1.0,
    "alpha_factor": 1.0,
    "c_p_factor": 1.0,
    "radiative_loss_fraction_Xr": 0.15,
    "residual_gravity_m_s2": 1.0e-4,
    "gravity_direction_unit": [0.0, 0.0, 1.0],
}


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
    solver_backend: str = "INTERNAL_3D_FDM"
    experiment_id: Optional[str] = None
    units_map: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_UNITS_MAP))
    uq_perturbations: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_UQ_PERTURBATIONS))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def enforce_calibration_lock(
    channel_data: Dict[str, Any],
    attempt_si_conversion: bool = False
) -> Dict[str, Any]:
    """
    ETAPA 2 - PUNTO 2 (Tarea 2.A en ia/contract_si.py):
    Guardián de calibración para canales MFC y sensores crudos del ensayo 20013D1:
      1. Si calibration_verified == False en MFC2/MFC3, bloquea cualquier intento de
         llamar a convert_mfc_instrumental_to_si() para transformar voltios [V] a [kg/s].
      2. Si los termopares (TCBurner, TCA, TCB, TCC), PMT3 o RadiometerCenter carecen
         de curva de calibración verificada en el registro, conserva la señal en su
         unidad instrumental cruda y prohíbe etiquetarla como temperatura física en
         Kelvin [K] o flujo radiativo absoluto [W/m^2].
    """
    if not isinstance(channel_data, dict):
        raise TypeError("channel_data debe ser un diccionario válido.")

    audited = dict(channel_data)
    ch_id = str(audited.get("channel_id", audited.get("sensor_id", "UNKNOWN"))).strip()
    unit_raw = str(audited.get("unit", audited.get("original_unit", "raw_signal"))).strip()

    cal_verified = bool(
        audited.get(
            "calibration_verified",
            audited.get(
                "calibration_to_kg_s_verified",
                audited.get("calibration_to_K_verified", False),
            ),
        )
    )

    is_mfc = ch_id.upper().startswith("MFC") or unit_raw.upper() == "V"
    is_tc = ch_id.upper().startswith("TC") or "MV" in unit_raw.upper()

    if not cal_verified:
        audited["calibration_verified"] = False
        audited["calibration_lock_active"] = True
        audited["allowed_display_unit"] = unit_raw
        audited["unit_verification_status"] = "PHYSICAL_CALIBRATION_PENDING"
        audited["raw_signal_status"] = "UNIT_VERIFIED_RAW_SIGNAL"
        audited["epistemic_tag"] = str(audited.get("epistemic_tag", "OBSERVED"))

        if is_mfc:
            audited["ui_lock_badge"] = "[CALIBRACIÓN V -> kg/s NO VERIFICADA]"
            audited["prohibited_si_unit"] = "kg/s"
        elif is_tc:
            audited["ui_lock_badge"] = "[CALIBRACIÓN mV/crudo -> K NO VERIFICADA]"
            audited["prohibited_si_unit"] = "K"
        else:
            audited["ui_lock_badge"] = "[CALIBRACIÓN FÍSICA A UNIDADES SI NO VERIFICADA]"
            audited["prohibited_si_unit"] = "W/m^2"

        if attempt_si_conversion:
            if is_mfc:
                convert_mfc_instrumental_to_si({"mfc_voltage_V": 1.0, "mfc_unit": "V", "calibration_verified": False})
            raise ValueError(
                f"Error Científico SI (Candado Etapa 2 en '{ch_id}'): Prohibido convertir señal cruda "
                f"en [{unit_raw}] a [{audited['prohibited_si_unit']}] porque calibration_verified es False."
            )
    else:
        audited["calibration_verified"] = True
        audited["calibration_lock_active"] = False
        audited["allowed_display_unit"] = unit_raw
        audited["unit_verification_status"] = "SI_CALIBRATION_VERIFIED"
        audited["ui_lock_badge"] = "[CALIBRACIÓN SI VERIFICADA]"

    return audited


def convert_mfc_instrumental_to_si(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte unidades instrumentales documentadas (psia, atm, bar, °C, mg/s, sccm) a SI.
    ETAPA 2 (Punto 2 - Tarea 2.A): Prohibido convertir Voltios [V] a [kg/s] o señales
    de termopares sin calibración verificada a Kelvin [K].
    """
    out = dict(raw_dict)

    # 1. Candado estricto sobre consignas MFC en Voltios [V] (Ensayo 20013D1 - 42 eventos)
    has_voltage_key = (
        "mfc_voltage_V" in out
        or "voltage_V" in out
        or "MFC2_setpoint_V" in out
        or "MFC3_setpoint_V" in out
        or str(out.get("mfc_unit", "")).upper() == "V"
        or (str(out.get("unit", "")).upper() == "V" and "mass_flow_kg_s" not in out)
    )
    mfc_cal_unverified = (
        out.get("calibration_verified") is False
        or out.get("voltage_to_mass_flow_calibrated") is False
        or out.get("mfc_voltage_to_massflow_verified") is False
    )

    if has_voltage_key or (mfc_cal_unverified and "mass_flow_kg_s" not in out):
        raise ValueError(
            "Error Científico SI: Prohibido convertir voltajes MFC [V] a caudal másico [kg/s] sin curva de calibración verificada."
        )

    # 2. Candado estricto sobre señales crudas de termopares sin calibración a Kelvin [K]
    if (
        "thermocouple_raw_mV" in out
        or "tc_raw_signal" in out
        or (out.get("thermocouple_to_kelvin_verified") is False and "T_initial_K" not in out)
    ):
        raise ValueError(
            "Error Científico SI: Prohibido interpretar señales crudas de termopares [mV/raw] como temperatura física en Kelvin [K] sin calibración verificada."
        )

    # 3. Conversiones físicas válidas y documentadas a SI
    if "pressure_psia" in out and "pressure_Pa" not in out:
        out["pressure_Pa"] = float(out["pressure_psia"]) * 6894.75729
    elif "pressure_atm" in out and "pressure_Pa" not in out:
        out["pressure_Pa"] = float(out["pressure_atm"]) * 101325.0
    elif "pressure_bar" in out and "pressure_Pa" not in out:
        out["pressure_Pa"] = float(out["pressure_bar"]) * 100000.0

    if "T_initial_C" in out and "T_initial_K" not in out:
        out["T_initial_K"] = float(out["T_initial_C"]) + 273.15
    elif "T_ambient_C" in out and "T_initial_K" not in out:
        out["T_initial_K"] = float(out["T_ambient_C"]) + 273.15

    if "T_burner_C" in out and "T_burner_K" not in out:
        out["T_burner_K"] = float(out["T_burner_C"]) + 273.15

    if "mass_flow_mg_s" in out and "mass_flow_kg_s" not in out:
        out["mass_flow_kg_s"] = float(out["mass_flow_mg_s"]) * 1e-6
    elif "flow_sccm" in out and "mass_flow_kg_s" not in out:
        rho_std = 1.25
        out["mass_flow_kg_s"] = float(out["flow_sccm"]) * (1e-6 / 60.0) * rho_std
    return out


def mass_fraction_to_concentration(rho: float, Y: np.ndarray) -> np.ndarray:
    return rho * np.asarray(Y, dtype=np.float64)


def validate_user_input_si(input_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(input_dict, dict):
        return (False, ["El parámetro de entrada debe ser un diccionario válido."])

    try:
        d = convert_mfc_instrumental_to_si(input_dict)
    except ValueError as exc:
        return (False, [str(exc)])

    # Candado Etapa 2: botella "66.7% H2 with CH4" con composition_basis_verified == False
    if d.get("composition_basis_verified") is False:
        errors.append(
            "Error Científico SI (Etapa 2 - 20013D1): 'composition_basis_verified' es False para la mezcla '66.7% H2 with CH4'. "
            "Prohibido ejecutar simulación física continua sin base composicional (molar vs másica) verificada."
        )

    fuel = str(d.get("fuel_type", d.get("fuel", "C2H4"))).upper()
    if fuel not in VALID_FUELS:
        errors.append(f"Combustible inválido '{fuel}'. Permitidos: {VALID_FUELS}.")

    Y_F = float(d.get("Y_F_burner", d.get("Y_F_inlet", 1.0)))
    if not (0.01 <= Y_F <= 1.0):
        errors.append("Error SI: Y_F_burner debe estar en [0.01, 1.0].")

    Y_O = float(d.get("Y_O_ambient", 0.233))
    if not (0.05 <= Y_O <= 1.0):
        errors.append("Error SI: Y_O_ambient debe estar en [0.05, 1.0].")

    T_init = float(d.get("T_initial_K", d.get("T_0_K", 298.15)))
    if not (200.0 <= T_init <= 3500.0):
        errors.append("Error SI: T_initial_K debe estar en Kelvin [K] dentro de [200, 3500].")

    p_Pa = float(d.get("pressure_Pa", d.get("p_0_Pa", 98000.0)))
    if not (10000.0 <= p_Pa <= 500000.0):
        errors.append("Error SI: pressure_Pa debe estar en Pascales [Pa] dentro de [10000, 500000].")

    mdot = float(d.get("mass_flow_kg_s", d.get("mdot_kg_s", 2.5e-6)))
    if not (1e-8 <= mdot <= 1e-3):
        errors.append("Error SI: mass_flow_kg_s debe estar en [kg/s] dentro de [1e-8, 1e-3].")

    r_b = float(d.get("burner_radius_m", d.get("r_b_m", 0.00318)))
    if not (0.0005 <= r_b <= 0.05):
        errors.append("Error SI: burner_radius_m debe estar en metros [m].")

    return (len(errors) == 0, errors)


def validate_input_si(input_dict: Dict[str, Any]) -> SimulationInputSI:
    if isinstance(input_dict, SimulationInputSI):
        return input_dict

    d = convert_mfc_instrumental_to_si(input_dict)
    is_valid, errors = validate_user_input_si(d)
    if not is_valid:
        raise ValueError(" | ".join(errors))

    Y_F = float(d.get("Y_F_burner", d.get("Y_F_inlet", 1.0)))
    Y_I = round(max(0.0, 1.0 - Y_F), 6)
    diluent = str(d.get("diluent_species", "N2")).upper()
    if diluent not in VALID_DILUENTS:
        diluent = "N2"

    uq_merged = dict(DEFAULT_UQ_PERTURBATIONS)
    if isinstance(d.get("uq_perturbations"), dict):
        uq_merged.update(d["uq_perturbations"])
    if isinstance(d.get("uq_perturbable_params"), dict):
        uq_merged.update(d["uq_perturbable_params"])

    return SimulationInputSI(
        fuel_type=str(d.get("fuel_type", d.get("fuel", "C2H4"))).upper(),
        diluent_species=diluent,
        Y_F_burner=Y_F,
        Y_I_burner=Y_I,
        Y_O_ambient=float(d.get("Y_O_ambient", 0.233)),
        T_initial_K=float(d.get("T_initial_K", d.get("T_0_K", 298.15))),
        T_burner_K=float(d.get("T_burner_K", 300.0)),
        pressure_Pa=float(d.get("pressure_Pa", d.get("p_0_Pa", 98000.0))),
        mass_flow_kg_s=float(d.get("mass_flow_kg_s", d.get("mdot_kg_s", 2.5e-6))),
        burner_radius_m=float(d.get("burner_radius_m", d.get("r_b_m", 0.00318))),
        domain_half_width_m=float(d.get("domain_half_width_m", 0.035)),
        grid_nodes_per_axis=int(d.get("grid_nodes_per_axis", 41)),
        total_time_s=float(d.get("total_time_s", 1.2)),
        solver_backend=str(d.get("solver_backend", "INTERNAL_3D_FDM")),
        experiment_id=d.get("experiment_id", None),
        units_map=dict(DEFAULT_UNITS_MAP),
        uq_perturbations=uq_merged,
    )


def assert_valid_3d_fields(T_3d: np.ndarray, Y_F_3d: np.ndarray, Y_O_3d: np.ndarray) -> bool:
    if not (T_3d.ndim == 3 and T_3d.shape == Y_F_3d.shape == Y_O_3d.shape):
        raise ValueError("Error 3D: T_3d, Y_F_3d y Y_O_3d deben tener la misma dimensión.")
    if not (np.all(np.isfinite(T_3d)) and np.all(np.isfinite(Y_F_3d)) and np.all(np.isfinite(Y_O_3d))):
        raise ValueError("Error numérico: NaN o Inf detectados.")
    return True


if __name__ == "__main__":
    print("=== PRUEBA DE CONTRACT_SI (ETAPA 1 + CANDADOS ETAPA 2 20013D1) ===")
    # 1. Prueba Etapa 1: Entrada SI válida
    sim_ok = validate_input_si({"fuel_type": "C2H4", "pressure_Pa": 98000.0, "mass_flow_kg_s": 2.5e-6})
    print(f"[OK] Etapa 1 (SimulationInputSI): fuel={sim_ok.fuel_type}, p={sim_ok.pressure_Pa} Pa, mdot={sim_ok.mass_flow_kg_s} kg/s")

    # 2. Prueba Etapa 2 (Punto 2 - Tarea 2.A): Candado enforce_calibration_lock en MFC2 [V] y TCA [mV]
    mfc2_locked = enforce_calibration_lock({"channel_id": "MFC2", "unit": "V", "calibration_verified": False})
    tca_locked = enforce_calibration_lock({"sensor_id": "TCA", "unit": "mV_raw", "calibration_verified": False})
    print(f"[OK] Etapa 2 (Candado MFC2): {mfc2_locked['ui_lock_badge']} | Lock={mfc2_locked['calibration_lock_active']}")
    print(f"[OK] Etapa 2 (Candado TCA) : {tca_locked['ui_lock_badge']} | Lock={tca_locked['calibration_lock_active']}")

    # 3. Verificar bloqueo al intentar convertir Voltios a kg/s
    try:
        enforce_calibration_lock(mfc2_locked, attempt_si_conversion=True)
    except ValueError as e:
        print(f"[OK] Etapa 2 (Bloqueo V -> kg/s activo): {e}")