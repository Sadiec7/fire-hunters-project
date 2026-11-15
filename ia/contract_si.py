"""
ia/contract_si.py
Contrato de Integración y Validador del Sistema Internacional (SI) - Bloque 2.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, List
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


@dataclass
class SimulationInputSI:
    fuel_type: str = "C2H4"
    Y_F_burner: float = 1.0
    Y_O_ambient: float = 0.233
    T_initial_K: float = 298.15
    T_burner_K: float = 300.0
    pressure_Pa: float = 98000.0
    mass_flow_kg_s: float = 2.5e-6
    burner_radius_m: float = 0.00318
    domain_half_width_m: float = 0.035
    grid_nodes_per_axis: int = 41
    total_time_s: float = 1.2

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def mass_fraction_to_concentration(rho: float, Y: np.ndarray) -> np.ndarray:
    """Convierte fracción másica adimensional Y [-] a concentración C [kg/m^3]."""
    return rho * np.asarray(Y, dtype=np.float64)


def validate_user_input_si(input_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida diccionario de entrada y devuelve (es_valido, lista_errores)."""
    errors: List[str] = []

    fuel = str(input_dict.get("fuel_type", input_dict.get("fuel", "C2H4"))).upper()
    if fuel not in VALID_FUELS:
        errors.append(f"Combustible inválido '{fuel}'. Permitidos: {VALID_FUELS}.")

    Y_F = float(input_dict.get("Y_F_burner", input_dict.get("Y_F_inlet", 1.0)))
    if not (0.01 <= Y_F <= 1.0):
        errors.append("Error SI: Y_F_burner debe ser fracción másica en [0.01, 1.0], no porcentaje.")

    Y_O = float(input_dict.get("Y_O_ambient", 0.233))
    if not (0.05 <= Y_O <= 1.0):
        errors.append("Error SI: Y_O_ambient debe ser fracción másica en [0.05, 1.0], no porcentaje.")

    T_init = float(input_dict.get("T_initial_K", input_dict.get("T_0_K", 298.15)))
    if T_init < 200.0 or T_init > 3500.0:
        errors.append("Error de unidades SI: T_initial_K debe estar en Kelvin [K] (ej. 298.15 K), no en °C.")

    T_burn = float(input_dict.get("T_burner_K", 300.0))
    if T_burn < 200.0 or T_burn > 3500.0:
        errors.append("Error de unidades SI: T_burner_K debe estar en Kelvin [K] (ej. 300.0 K).")

    p_Pa = float(input_dict.get("pressure_Pa", input_dict.get("p_0_Pa", 98000.0)))
    if p_Pa < 10000.0 or p_Pa > 500000.0:
        errors.append("Error de unidades SI: la presión debe estar en Pascales [Pa] (ej. 101325 Pa), no en atm o bar.")

    mdot = float(input_dict.get("mass_flow_kg_s", input_dict.get("mdot_kg_s", 2.5e-6)))
    if not (1e-8 <= mdot <= 1e-3):
        errors.append("Error de unidades SI: mass_flow_kg_s debe estar en [kg/s] (ej. 2.5e-6 kg/s), no en mg/s.")

    r_b = float(input_dict.get("burner_radius_m", input_dict.get("r_b_m", 0.00318)))
    if not (0.0005 <= r_b <= 0.05):
        errors.append("Error de unidades SI: burner_radius_m debe estar en metros [m] (ej. 0.00318 m), no en mm.")

    return (len(errors) == 0, errors)


def validate_input_si(input_dict: Dict[str, Any]) -> SimulationInputSI:
    """Valida el diccionario de entrada y devuelve una instancia SimulationInputSI."""
    is_valid, errors = validate_user_input_si(input_dict)
    if not is_valid:
        raise ValueError(" | ".join(errors))

    return SimulationInputSI(
        fuel_type=str(input_dict.get("fuel_type", input_dict.get("fuel", "C2H4"))).upper(),
        Y_F_burner=float(input_dict.get("Y_F_burner", input_dict.get("Y_F_inlet", 1.0))),
        Y_O_ambient=float(input_dict.get("Y_O_ambient", 0.233)),
        T_initial_K=float(input_dict.get("T_initial_K", input_dict.get("T_0_K", 298.15))),
        T_burner_K=float(input_dict.get("T_burner_K", 300.0)),
        pressure_Pa=float(input_dict.get("pressure_Pa", input_dict.get("p_0_Pa", 98000.0))),
        mass_flow_kg_s=float(input_dict.get("mass_flow_kg_s", input_dict.get("mdot_kg_s", 2.5e-6))),
        burner_radius_m=float(input_dict.get("burner_radius_m", input_dict.get("r_b_m", 0.00318))),
        domain_half_width_m=float(input_dict.get("domain_half_width_m", 0.035)),
        grid_nodes_per_axis=int(input_dict.get("grid_nodes_per_axis", 41)),
        total_time_s=float(input_dict.get("total_time_s", 1.2)),
    )


def assert_valid_3d_fields(T_3d: np.ndarray, Y_F_3d: np.ndarray, Y_O_3d: np.ndarray) -> bool:
    """Verifica forma 3D idéntica, ausencia de NaN/Inf y rango [0, 1] en fracciones másicas."""
    if not (T_3d.ndim == 3 and T_3d.shape == Y_F_3d.shape == Y_O_3d.shape):
        raise ValueError("Error 3D: T_3d, Y_F_3d y Y_O_3d deben tener la misma dimensión (Nx, Ny, Nz).")
    if not (np.all(np.isfinite(T_3d)) and np.all(np.isfinite(Y_F_3d)) and np.all(np.isfinite(Y_O_3d))):
        raise ValueError("Error numérico: Se detectaron valores NaN o Inf en los campos 3D.")
    if np.min(Y_F_3d) < -1e-6 or np.max(Y_F_3d) > 1.0 + 1e-6:
        raise ValueError("Error físico: Y_F_3d fuera del rango [0.0, 1.0].")
    if np.min(Y_O_3d) < -1e-6 or np.max(Y_O_3d) > 1.0 + 1e-6:
        raise ValueError("Error físico: Y_O_3d fuera del rango [0.0, 1.0].")
    return True


if __name__ == "__main__":
    sample = SimulationInputSI().to_dict()
    sim_in = validate_input_si(sample)
    print("Contrato SI validado correctamente:", sim_in)