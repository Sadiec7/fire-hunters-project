# -*- coding: utf-8 -*-
"""
ia/contract_si.py
Contrato de Integración en Unidades del Sistema Internacional (SI).
Proyecto NASA Space Apps: Flame in Freefall (ACME / s-Flame).
Autores: Ángel ("Lito" / "Perrita") & Rodolfo ("Tornolfo")
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, List
import numpy as np

# =============================================================================
# 1. CONSTANTES FÍSICAS UNIVERSALES Y CATÁLOGOS OFICIALES EN SI
# =============================================================================
R_U_J_MOL_K: float = 8.314462618  # Constante universal de los gases [J/(mol*K)]
R_U: float = R_U_J_MOL_K          # Alias de compatibilidad

# Orden inamovible de especies químicas: Combustible, Oxidante, Productos, Inerte
SPECIES_ORDER: Tuple[str, ...] = ("F", "O2", "P", "N2")

# Etiquetas obligatorias de procedencia de datos (Sección 2.2 / Regla de Oro 4)
VALID_PROVENANCE_TAGS: Tuple[str, ...] = (
    "MEDIDO_EXPERIMENTALMENTE",
    "CALCULADO_DE_DATOS_EXP",
    "ESTIMADO_FUENTE_CIENTIFICA",
    "SUPUESTO_SIMPLIFICACION",
    "NO_DISPONIBLE",
)
VALID_PROVENANCE = list(VALID_PROVENANCE_TAGS)

# Combustibles gaseosos permitidos exclusivamente para el solver 3D de s-Flame
VALID_FUELS: Tuple[str, ...] = ("C2H4", "CH4", "H2")


# =============================================================================
# 2. ESTRUCTURA DE ENTRADA DEL USUARIO EN UNIDADES SI
# =============================================================================
@dataclass
class SimulationInputSI:
    """
    Almacena y estructura las condiciones iniciales de operación validadas
    estrictamente en unidades del Sistema Internacional (SI).
    """
    fuel_type: str = "C2H4"               # Combustible: "C2H4", "CH4" o "H2" [-]
    Y_F_burner: float = 1.0               # Fracción másica de combustible en el quemador [-] (0.01 a 1.0)
    Y_O_ambient: float = 0.233            # Fracción másica de O2 en el ambiente [-] (0.05 a 1.0)
    T_initial_K: float = 298.15           # Temperatura inicial de la cámara [K] (250.0 a 1000.0)
    T_burner_K: float = 300.0             # Temperatura en la superficie del quemador [K] (250.0 a 1000.0)
    pressure_Pa: float = 98000.0          # Presión de operación de la cámara [Pa] (10000.0 a 300000.0)
    mass_flow_kg_s: float = 2.5e-6        # Flujo másico inyectado [kg/s] (1e-8 a 1e-3)
    burner_radius_m: float = 0.00318      # Radio de la esfera porosa s-Flame [m]
    domain_half_width_m: float = 0.035    # Semiancho del cubo de simulación 3D [m]
    grid_nodes_per_axis: int = 41         # Nodos por eje (Nx = Ny = Nz) [-]
    total_time_s: float = 1.2             # Tiempo físico total a simular [s]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia a un diccionario estándarizable a JSON."""
        return asdict(self)


# =============================================================================
# 3. FUNCIONES DE CONVERSIÓN Y VALIDACIÓN DE ENTRADAS SI
# =============================================================================
def mass_fraction_to_concentration(rho_kg_m3: float, Y: Any) -> Any:
    """
    Convierte la fracción másica adimensional Y [-] a concentración másica C [kg/m^3].
    Fórmula oficial (Sección 6 y 9.1): C_k = rho * Y_k
    Acepta tanto escalares float como arreglos 3D de NumPy.
    """
    return rho_kg_m3 * Y


def validate_user_input_si(input_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Revisa un diccionario de entrada y devuelve (es_valido, lista_de_errores_en_espanol).
    Detecta errores típicos de unidades (atmósferas en vez de Pascales, Celsius en vez
    de Kelvin, porcentajes en vez de fracciones másicas, miligramos en vez de kilogramos).
    """
    errors: List[str] = []

    if not isinstance(input_dict, dict):
        return False, ["El parámetro de entrada debe ser un diccionario JSON válido."]

    # Llaves obligatorias mínimas (con soporte de alias si vienen de distintas vistas)
    fuel = input_dict.get("fuel_type", input_dict.get("fuel", "C2H4"))
    if fuel not in VALID_FUELS:
        errors.append(
            f"Combustible inválido '{fuel}'. El solver 3D de s-Flame solo acepta: {VALID_FUELS}."
        )

    # Validación de Fracción Másica de Combustible (Y_F_burner)
    Y_F = input_dict.get("Y_F_burner", input_dict.get("Y_F_inlet", 1.0))
    try:
        Y_F = float(Y_F)
        if Y_F > 1.0:
            errors.append(
                f"Error de unidades SI en Y_F_burner ({Y_F}): las fracciones másicas van de 0.0 a 1.0 [-], "
                "no en porcentaje (ej. usa 1.0 en lugar de 100%)."
            )
        elif Y_F < 0.01:
            errors.append(
                f"Fuera de rango físico en Y_F_burner ({Y_F}): debe estar en el rango [0.01, 1.0]."
            )
    except (ValueError, TypeError):
        errors.append("Y_F_burner debe ser un número flotante válido.")

    # Validación de Fracción Másica de Oxidante (Y_O_ambient)
    Y_O = input_dict.get("Y_O_ambient", 0.233)
    try:
        Y_O = float(Y_O)
        if Y_O > 1.0:
            errors.append(
                f"Error de unidades SI en Y_O_ambient ({Y_O}): las fracciones másicas van de 0.0 a 1.0 [-], "
                "no en porcentaje (ej. para 21% O2 molar en aire usa 0.233)."
            )
        elif Y_O < 0.05:
            errors.append(
                f"Fuera de rango físico en Y_O_ambient ({Y_O}): debe estar en el rango [0.05, 1.0]."
            )
    except (ValueError, TypeError):
        errors.append("Y_O_ambient debe ser un número flotante válido.")

    # Validación de Temperaturas en Kelvin (T_initial_K y T_burner_K)
    T_init = input_dict.get("T_initial_K", input_dict.get("T_ambient_K", 298.15))
    T_burn = input_dict.get("T_burner_K", 300.0)
    for name, val in [("T_initial_K", T_init), ("T_burner_K", T_burn)]:
        try:
            val_f = float(val)
            if val_f < 150.0:
                errors.append(
                    f"Error de unidades SI en {name} ({val_f}): la temperatura debe estar en Kelvin [K] "
                    "(ej. 298.15 K), no en grados Celsius (°C)."
                )
            elif not (250.0 <= val_f <= 1000.0):
                errors.append(
                    f"Fuera de rango en {name} ({val_f} K): las temperaturas iniciales/quemador deben "
                    "estar entre 250.0 K y 1000.0 K."
                )
        except (ValueError, TypeError):
            errors.append(f"{name} debe ser un número flotante válido en Kelvin [K].")

    # Validación de Presión en Pascales (pressure_Pa)
    p_Pa = input_dict.get("pressure_Pa", input_dict.get("p_initial_Pa", 98000.0))
    try:
        p_Pa = float(p_Pa)
        if p_Pa < 500.0:
            errors.append(
                f"Error de unidades SI en pressure_Pa ({p_Pa}): la presión debe estar en Pascales [Pa] "
                "(ej. 101325 Pa), no en atmósferas o bar."
            )
        elif not (10000.0 <= p_Pa <= 300000.0):
            errors.append(
                f"Fuera de rango en pressure_Pa ({p_Pa} Pa): debe estar entre 10,000 Pa (0.1 atm) "
                "y 300,000 Pa (3.0 atm) para la cámara CIR."
            )
    except (ValueError, TypeError):
        errors.append("pressure_Pa debe ser un número flotante válido en Pascales [Pa].")

    # Validación de Flujo Másico en kg/s (mass_flow_kg_s)
    mdot = input_dict.get("mass_flow_kg_s", 2.5e-6)
    try:
        mdot = float(mdot)
        if mdot >= 0.01:
            errors.append(
                f"Error de unidades SI en mass_flow_kg_s ({mdot}): el flujo másico debe estar en [kg/s] "
                "(ej. 2.5e-6 kg/s), no en mg/s ni g/s."
            )
        elif not (1.0e-8 <= mdot <= 1.0e-3):
            errors.append(
                f"Fuera de rango en mass_flow_kg_s ({mdot} kg/s): debe estar en el rango [1e-8, 1e-3] kg/s."
            )
    except (ValueError, TypeError):
        errors.append("mass_flow_kg_s debe ser un número flotante válido en [kg/s].")

    # Validación de Radio del Quemador en metros (burner_radius_m)
    r_b = input_dict.get("burner_radius_m", 0.00318)
    try:
        r_b = float(r_b)
        if r_b >= 0.1:
            errors.append(
                f"Error de unidades SI en burner_radius_m ({r_b}): el radio del quemador debe estar en metros [m] "
                "(ej. 0.00318 m), no en milímetros ni centímetros."
            )
        elif not (0.0005 <= r_b <= 0.02):
            errors.append(
                f"Fuera de rango en burner_radius_m ({r_b} m): debe estar entre 0.0005 m y 0.02 m."
            )
    except (ValueError, TypeError):
        errors.append("burner_radius_m debe ser un número flotante válido en metros [m].")

    # Validación de Semiancho de Dominio 3D (domain_half_width_m) y Nodos (grid_nodes_per_axis)
    L_dom = input_dict.get("domain_half_width_m", 0.035)
    try:
        L_dom = float(L_dom)
        if not (0.01 <= L_dom <= 0.25):
            errors.append(
                f"Fuera de rango en domain_half_width_m ({L_dom} m): debe estar entre 0.01 m y 0.25 m."
            )
        if isinstance(r_b, float) and L_dom <= 3.0 * r_b:
            errors.append(
                f"Incoherencia geométrica: domain_half_width_m ({L_dom} m) debe ser al menos 3 veces "
                f"mayor que burner_radius_m ({r_b} m)."
            )
    except (ValueError, TypeError):
        errors.append("domain_half_width_m debe ser un número flotante válido en metros [m].")

    N_nodes = input_dict.get("grid_nodes_per_axis", 41)
    try:
        N_nodes = int(N_nodes)
        if not (15 <= N_nodes <= 101):
            errors.append(
                f"Fuera de rango en grid_nodes_per_axis ({N_nodes}): debe ser un entero entre 15 y 101."
            )
    except (ValueError, TypeError):
        errors.append("grid_nodes_per_axis debe ser un número entero válido.")

    t_tot = input_dict.get("total_time_s", 1.2)
    try:
        t_tot = float(t_tot)
        if not (0.001 <= t_tot <= 30.0):
            errors.append(
                f"Fuera de rango en total_time_s ({t_tot} s): el tiempo a simular debe estar entre 0.001 s y 30.0 s."
            )
    except (ValueError, TypeError):
        errors.append("total_time_s debe ser un número flotante válido en segundos [s].")

    return (len(errors) == 0), errors


def validate_input_si(input_dict: Dict[str, Any]) -> SimulationInputSI:
    """
    Valida un diccionario JSON de entrada y devuelve un objeto SimulationInputSI
    completamente tipado y verificado en unidades SI.
    Si detecta cualquier violación de unidades o rangos, lanza ValueError con mensaje en español.
    """
    is_valid, error_messages = validate_user_input_si(input_dict)
    if not is_valid:
        joined_errors = "\n  - ".join(error_messages)
        raise ValueError(f"Se detectaron errores en la validación SI de entrada:\n  - {joined_errors}")

    return SimulationInputSI(
        fuel_type=str(input_dict.get("fuel_type", input_dict.get("fuel", "C2H4"))),
        Y_F_burner=float(input_dict.get("Y_F_burner", input_dict.get("Y_F_inlet", 1.0))),
        Y_O_ambient=float(input_dict.get("Y_O_ambient", 0.233)),
        T_initial_K=float(input_dict.get("T_initial_K", input_dict.get("T_ambient_K", 298.15))),
        T_burner_K=float(input_dict.get("T_burner_K", 300.0)),
        pressure_Pa=float(input_dict.get("pressure_Pa", input_dict.get("p_initial_Pa", 98000.0))),
        mass_flow_kg_s=float(input_dict.get("mass_flow_kg_s", 2.5e-6)),
        burner_radius_m=float(input_dict.get("burner_radius_m", 0.00318)),
        domain_half_width_m=float(input_dict.get("domain_half_width_m", 0.035)),
        grid_nodes_per_axis=int(input_dict.get("grid_nodes_per_axis", 41)),
        total_time_s=float(input_dict.get("total_time_s", 1.2)),
    )


# =============================================================================
# 4. VALIDADOR DE TENSORES TRIDIMENSIONALES (CUBOS 3D)
# =============================================================================
def assert_valid_3d_fields(
    T_3d: np.ndarray,
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    tol: float = 1.0e-6
) -> bool:
    """
    Comprueba que los tres cubos tridimensionales T_3d, Y_F_3d y Y_O_3d:
      1. Sean arreglos 3D de NumPy (ndim == 3) con exactamente la misma forma (Nx, Ny, Nz).
      2. No contengan valores infinitos (inf) ni indeterminados (NaN).
      3. Mantengan las fracciones másicas acotadas en [0.0, 1.0] (dentro de la tolerancia tol)
         y la temperatura en valores físicos positivos (T >= 150 K).
    """
    for name, arr in [("T_3d", T_3d), ("Y_F_3d", Y_F_3d), ("Y_O_3d", Y_O_3d)]:
        if not isinstance(arr, np.ndarray):
            raise TypeError(f"El campo {name} debe ser un arreglo numpy.ndarray.")
        if arr.ndim != 3:
            raise ValueError(f"El campo {name} debe ser tridimensional (ndim=3), pero tiene forma {arr.shape}.")
        if not np.all(np.isfinite(arr)):
            raise FloatingPointError(f"Inestabilidad numérica detectada: el campo {name} contiene NaN o Inf.")

    if not (T_3d.shape == Y_F_3d.shape == Y_O_3d.shape):
        raise ValueError(
            f"Incompatibilidad de tamaño 3D: T_3d{T_3d.shape}, Y_F_3d{Y_F_3d.shape}, Y_O_3d{Y_O_3d.shape}."
        )

    if np.min(T_3d) < 150.0 or np.max(T_3d) > 5000.0:
        raise ValueError(
            f"Temperatura 3D fuera de límites físicos razonables: min={np.min(T_3d):.2f} K, max={np.max(T_3d):.2f} K."
        )

    for name, arr in [("Y_F_3d", Y_F_3d), ("Y_O_3d", Y_O_3d)]:
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        if min_val < -tol or max_val > 1.0 + tol:
            raise ValueError(
                f"Fracción másica {name} fuera de [0.0, 1.0]: min={min_val:.6f}, max={max_val:.6f}."
            )

    return True


# =============================================================================
# 5. BLOQUE DE PRUEBA DIRECTA EN TERMINAL
# =============================================================================
if __name__ == "__main__":
    print("=== PRUEBA DE CONTRATO SI (ia/contract_si.py) ===")

    # 1. Prueba con el caso de referencia válido de s-Flame
    caso_maestro = {
        "fuel_type": "C2H4",
        "Y_F_burner": 1.0,
        "Y_O_ambient": 0.233,
        "T_initial_K": 298.15,
        "T_burner_K": 300.0,
        "pressure_Pa": 98000.0,
        "mass_flow_kg_s": 2.5e-6,
        "burner_radius_m": 0.00318,
        "domain_half_width_m": 0.035,
        "grid_nodes_per_axis": 41,
        "total_time_s": 1.2,
    }
    sim_input = validate_input_si(caso_maestro)
    print("[OK] Caso de referencia validado correctamente:")
    print("    ", sim_input)

    # 2. Prueba intencional de error de unidades (presión en atm y temp en °C)
    caso_erroneo = dict(caso_maestro, pressure_Pa=1.0, T_initial_K=25.0)
    es_valido, errores = validate_user_input_si(caso_erroneo)
    print(f"[OK] Detección de errores de unidades funcionando (es_valido={es_valido}):")
    for err in errores:
        print("    ->", err)

    # 3. Prueba de tensores 3D
    cubo_T = np.full((15, 15, 15), 300.0)
    cubo_YF = np.zeros((15, 15, 15))
    cubo_YO = np.full((15, 15, 15), 0.233)
    assert_valid_3d_fields(cubo_T, cubo_YF, cubo_YO)
    print("[OK] Validación de tensores 3D (assert_valid_3d_fields) superada con éxito.")