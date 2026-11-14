
import numpy as np


def crear_malla_esferica(
    r_b_m,
    r_inf_m,
    n_points=100,
    relacion_total=10.0
):
    """
    Crea una malla radial esférica no uniforme.

    Parámetros:
        r_b_m: radio interior [m].
        r_inf_m: radio exterior [m].
        n_points: número total de nodos.
        relacion_total: relación entre intervalo máximo y mínimo.

    Retorna:
        Diccionario con nodos, intervalos, caras y volúmenes.
    """

    if r_b_m <= 0:
        raise ValueError("El radio inicial debe ser positivo.")

    if r_inf_m <= r_b_m:
        raise ValueError("El radio final debe ser mayor al inicial.")

    if n_points < 3:
        raise ValueError("Se necesitan al menos 3 nodos.")

    if relacion_total < 1:
        raise ValueError("La relación de intervalos debe ser >= 1.")

    n_intervalos = n_points - 1

    # Distribución geométrica de los intervalos
    factor = relacion_total ** (1 / (n_intervalos - 1))
    pasos = factor ** np.arange(n_intervalos)

    fraccion_acumulada = np.concatenate(
        ([0.0], np.cumsum(pasos) / np.sum(pasos))
    )

    # Coordenadas radiales
    r_m = r_b_m + (r_inf_m - r_b_m) * fraccion_acumulada

    # Distancias entre nodos
    dr_m = np.diff(r_m)

    # Caras entre nodos
    r_caras_m = 0.5 * (r_m[:-1] + r_m[1:])

    # Volúmenes de control reducidos (sin 4*pi)
    volumen_reducido_m3 = (
        r_caras_m[1:]**3 - r_caras_m[:-1]**3
    ) / 3.0

    return {
        "r_m": r_m,
        "dr_m": dr_m,
        "r_caras_m": r_caras_m,
        "volumen_reducido_m3": volumen_reducido_m3,
        "n_points": n_points,
        "r_b_m": r_b_m,
        "r_inf_m": r_inf_m,
        "relacion_total": relacion_total
    }


def calcular_difusion_esferica(malla, psi, phi):
    """
    Calcula el operador de difusión esférica:

        1/r² * d/dr (r² * phi * d(psi)/dr)

    Las fronteras se devuelven como NaN porque deben tratarse
    mediante las condiciones de frontera del solver.
    """

    r_m = malla["r_m"]
    dr_m = malla["dr_m"]
    r_caras_m = malla["r_caras_m"]
    volumen = malla["volumen_reducido_m3"]
    n_points = malla["n_points"]

    psi = np.asarray(psi, dtype=float)

    if psi.ndim != 1 or len(psi) != n_points:
        raise ValueError(
            "El campo psi debe tener un valor por cada nodo."
        )

    if not np.all(np.isfinite(psi)):
        raise ValueError("El campo psi contiene valores no finitos.")

    phi = np.asarray(phi, dtype=float)

    if phi.ndim == 0:
        phi = np.full(n_points, float(phi))

    if phi.ndim != 1 or len(phi) != n_points:
        raise ValueError(
            "El coeficiente phi debe ser escalar o tener "
            "un valor por cada nodo."
        )

    if not np.all(np.isfinite(phi)):
        raise ValueError("El coeficiente phi contiene valores no finitos.")

    if np.any(phi <= 0):
        raise ValueError("El coeficiente phi debe ser positivo.")

    # Interpolación del coeficiente a las caras
    phi_caras = 0.5 * (phi[:-1] + phi[1:])

    # Gradiente entre nodos
    gradiente_psi = np.diff(psi) / dr_m

    # Flujo difusivo
    flujo_caras = (
        r_caras_m**2
        * phi_caras
        * gradiente_psi
    )

    # Resultado del operador
    resultado = np.full(n_points, np.nan)

    resultado[1:-1] = (
        np.diff(flujo_caras) / volumen
    )

    return resultado


# ==========================================================
# PRUEBAS DEL MÓDULO
# ==========================================================

if __name__ == "__main__":

    # Parámetros de la malla
    r_b = 0.00318
    r_inf = 0.25
    n = 100
    relacion = 10.0

    malla = crear_malla_esferica(
        r_b,
        r_inf,
        n,
        relacion
    )

    r = malla["r_m"]

    print("=== VERIFICACIÓN DE MALLA ESFÉRICA ===")

    # ------------------------------------------------------
    # PRUEBA 1: CAMPO CONSTANTE
    # ------------------------------------------------------

    psi_constante = np.ones(n)

    resultado_constante = calcular_difusion_esferica(
        malla,
        psi_constante,
        1.0
    )

    error_constante = np.nanmax(
        np.abs(resultado_constante)
    )

    print("\n--- Prueba de campo constante ---")
    print("Error:", error_constante)

    # ------------------------------------------------------
    # PRUEBA 2: CAMPO 1/r
    # ------------------------------------------------------

    psi_inverso = 1.0 / r

    resultado_inverso = calcular_difusion_esferica(
        malla,
        psi_inverso,
        1.0
    )

    error_absoluto = np.nanmax(
        np.abs(resultado_inverso)
    )

    error_normalizado = np.nanmax(
        np.abs(resultado_inverso[1:-1]) * r[1:-1]**3
    )

    print("\n--- Prueba de 1/r ---")
    print("Error absoluto:", error_absoluto)
    print("Error normalizado:", error_normalizado)

    # ------------------------------------------------------
    # PRUEBA 3: CAMPO r²
    # ------------------------------------------------------

    psi_cuadrado = r**2

    resultado_cuadrado = calcular_difusion_esferica(
        malla,
        psi_cuadrado,
        1.0
    )

    valor_analitico = 6.0

    error_r2 = np.nanmax(
        np.abs(
            resultado_cuadrado[1:-1] - valor_analitico
        )
    )

    print("\n--- Prueba de r^2 ---")
    print("Valor analítico:", valor_analitico)
    print("Error máximo:", error_r2)

    # ------------------------------------------------------
    # PRUEBA 4: CONSERVACIÓN DEL FLUJO
    # ------------------------------------------------------

    psi_conservacion = r**2

    resultado_conservacion = calcular_difusion_esferica(
        malla,
        psi_conservacion,
        1.0
    )

    volumen = malla["volumen_reducido_m3"]

    flujo_caras = (
        malla["r_caras_m"]**2
        * (np.diff(psi_conservacion) / malla["dr_m"])
    )

    integral_operador = np.sum(
        resultado_conservacion[1:-1] * volumen
    )

    diferencia_flujos = (
        flujo_caras[-1] - flujo_caras[0]
    )

    error_conservacion = abs(
        integral_operador - diferencia_flujos
    )

    print("\n--- Prueba de conservación ---")
    print("Integral del operador:", integral_operador)
    print("Diferencia de flujos:", diferencia_flujos)
    print("Error de conservación:", error_conservacion)

    # ------------------------------------------------------
    # PRUEBA 5: CONVERGENCIA DE LA MALLA
    # ------------------------------------------------------

    print("\n--- Prueba de convergencia ---")

    resoluciones = [50, 100, 200, 400]

    for n_test in resoluciones:

        malla_test = crear_malla_esferica(
            r_b,
            r_inf,
            n_test,
            relacion
        )

        r_test = malla_test["r_m"]

        # Prueba de 1/r
        psi_test = 1.0 / r_test

        resultado_test = calcular_difusion_esferica(
            malla_test,
            psi_test,
            1.0
        )

        error_test = np.nanmax(
            np.abs(resultado_test[1:-1]) * r_test[1:-1]**3
        )

        # Prueba de r²
        psi_r2 = r_test**2

        resultado_r2 = calcular_difusion_esferica(
            malla_test,
            psi_r2,
            1.0
        )

        error_r2_test = np.nanmax(
            np.abs(resultado_r2[1:-1] - 6.0)
        )

        print(
            f"Nodos: {n_test:3d} | "
            f"Error 1/r: {error_test:.8e} | "
            f"Error r²: {error_r2_test:.8e}"
        )

    # ------------------------------------------------------
    # INFORMACIÓN GEOMÉTRICA
    # ------------------------------------------------------

    print("\n--- Información geométrica ---")

    print("Radio inicial:", r[0], "m")
    print("Radio final:", r[-1], "m")
    print("Número de nodos:", n)

    print(
        "Intervalo mínimo:",
        np.min(malla["dr_m"]),
        "m"
    )

    print(
        "Intervalo máximo:",
        np.max(malla["dr_m"]),
        "m"
    )

    print(
        "Relación de intervalos:",
        np.max(malla["dr_m"]) / np.min(malla["dr_m"])
    )
