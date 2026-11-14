
"""
Archivo: ia/grid.py

Generación de malla radial esférica y cálculo del operador
de difusión mediante volúmenes finitos.
"""

import numpy as np


def crear_malla_esferica(
    r_b_m,
    r_inf_m,
    n_points=100,
    stretch_factor=1.04
):
    """
    Genera una malla radial no uniforme.

    Parámetros:
        r_b_m: radio del quemador [m].
        r_inf_m: radio exterior del dominio [m].
        n_points: número de nodos.
        stretch_factor: razón de crecimiento entre intervalos.

    Devuelve:
        Diccionario con nodos, caras, distancias y volúmenes.
    """

    if not np.isfinite(r_b_m) or not np.isfinite(r_inf_m):
        raise ValueError("Los radios deben ser finitos.")

    if r_b_m <= 0 or r_inf_m <= r_b_m:
        raise ValueError("Se requiere 0 < r_b_m < r_inf_m.")

    if not isinstance(n_points, (int, np.integer)) or n_points < 3:
        raise ValueError("n_points debe ser un entero >= 3.")

    if not np.isfinite(stretch_factor) or stretch_factor < 1:
        raise ValueError("stretch_factor debe ser >= 1.")

    n_intervalos = n_points - 1

    pasos = stretch_factor ** np.arange(n_intervalos)

    fraccion_acumulada = np.concatenate((
        [0.0],
        np.cumsum(pasos) / np.sum(pasos)
    ))

    r_m = r_b_m + (r_inf_m - r_b_m) * fraccion_acumulada

    # Distancia entre nodos consecutivos
    dr_m = np.diff(r_m)

    # Caras de los volúmenes de control
    r_caras_m = 0.5 * (r_m[:-1] + r_m[1:])

    # Volúmenes radiales divididos entre 4*pi
    # Las fronteras corresponden a nodos interiores.
    volumen_reducido_m3 = (
        r_caras_m[1:]**3 - r_caras_m[:-1]**3
    ) / 3.0

    return {
        "r_m": r_m,
        "dr_m": dr_m,
        "r_caras_m": r_caras_m,
        "volumen_reducido_m3": volumen_reducido_m3,
        "n_points": n_points
    }


def calcular_difusion_esferica(malla, psi, phi):
    """
    Calcula:

    L = (1/r²) * d/dr (r² * phi * d(psi)/dr)

    mediante volúmenes finitos.

    psi: variable transportada en cada nodo.
    phi: coeficiente de difusión/transporte en cada nodo.

    Las fronteras se devuelven como NaN porque sus valores
    deben establecerse mediante condiciones de frontera.
    """

    r_m = malla["r_m"]
    dr_m = malla["dr_m"]
    r_caras_m = malla["r_caras_m"]
    volumen = malla["volumen_reducido_m3"]
    n_points = malla["n_points"]

    psi = np.asarray(psi, dtype=float)
    phi = np.asarray(phi, dtype=float)

    if psi.shape != (n_points,):
        raise ValueError("psi debe tener un valor por nodo.")

    if phi.ndim == 0:
        phi = np.full(n_points, float(phi))

    if phi.shape != (n_points,):
        raise ValueError("phi debe ser escalar o tener un valor por nodo.")

    if not np.all(np.isfinite(psi)) or not np.all(np.isfinite(phi)):
        raise ValueError("psi y phi deben contener valores finitos.")

    # Interpolación del coeficiente a las caras
    phi_caras = 0.5 * (phi[:-1] + phi[1:])

    # Gradiente entre nodos
    gradiente_psi = np.diff(psi) / dr_m

    # Flujo radial por unidad de ángulo sólido
    flujo_caras = (
        r_caras_m**2
        * phi_caras
        * gradiente_psi
    )

    # Divergencia del flujo en cada volumen interior
    resultado = np.full(n_points, np.nan)

    resultado[1:-1] = np.diff(flujo_caras) / volumen

    return resultado


# --- PRUEBAS ---
if __name__ == "__main__":

    malla = crear_malla_esferica(
        r_b_m=0.00318,
        r_inf_m=0.25,
        n_points=100,
        stretch_factor=1.04
    )

    r = malla["r_m"]

    # Prueba 1: campo constante debe producir difusión nula
    psi_constante = np.ones_like(r)

    resultado_constante = calcular_difusion_esferica(
        malla, psi_constante, 1.0
    )

    error_constante = np.max(
        np.abs(resultado_constante[1:-1])
    )

    # Prueba 2: Laplaciano de 1/r debe aproximarse a cero
    psi_inverso = 1.0 / r

    resultado_inverso = calcular_difusion_esferica(
        malla, psi_inverso, 1.0
    )

    error_inverso = np.max(
        np.abs(resultado_inverso[1:-1])
    )

    print("=== VERIFICACIÓN DE MALLA ESFÉRICA ===")
    print("Radio inicial:", r[0], "m")
    print("Radio final:", r[-1], "m")
    print("Número de nodos:", len(r))
    print("Intervalo mínimo:", np.min(malla["dr_m"]), "m")
    print("Intervalo máximo:", np.max(malla["dr_m"]), "m")
    print("Error campo constante:", error_constante)
    print("Error de 1/r:", error_inverso)
