"""
Archivo: ia/grid.py
Explicación: Crea los puntos del radio (malla) desde el quemador hasta afuera
y calcula cómo se mueven el calor y los gases entre capa y capa de la esfera.
"""

import numpy as np


def crear_malla_esferica(r_b_m, r_inf_m, n_points=100, stretch_factor=1.04):
    """
    Crea un diccionario con todos los datos geométricos de los radios.
    - r_b_m: radio del quemador poroso en metros (ej. 0.00318 m)
    - r_inf_m: radio final del dominio en metros (ej. 0.25 m)
    - n_points: cuántos puntos (nodos) queremos en total (ej. 100)
    - stretch_factor: cuánto crece cada paso (1.04 = cada paso es 4% más grande)
    """
    n_intervalos = n_points - 1
    pasos = stretch_factor ** np.arange(n_intervalos)
    fraccion_acumulada = np.concatenate(([0.0], np.cumsum(pasos) / np.sum(pasos)))
    r_m = r_b_m + (r_inf_m - r_b_m) * fraccion_acumulada

    dr_m = r_m[1:] - r_m[:-1]
    r_caras_m = 0.5 * (r_m[:-1] + r_m[1:])
    factor_volumen_m3 = (r_caras_m[1:] ** 3 - r_caras_m[:-1] ** 3) / 3.0

    return {
        "r_m": r_m,
        "dr_m": dr_m,
        "r_caras_m": r_caras_m,
        "factor_volumen_m3": factor_volumen_m3,
        "n_points": n_points
    }


def calcular_difusion_esferica(malla, psi, phi):
    """
    Calcula la fórmula de difusión en esfera: (1/r^2) * d/dr [ r^2 * phi * d(psi)/dr ]
    """
    r_m = malla["r_m"]
    dr_m = malla["dr_m"]
    factor_volumen_m3 = malla["factor_volumen_m3"]
    n_points = malla["n_points"]

    phi_en_caras = 0.5 * (phi[:-1] + phi[1:])
    derivada_psi = (psi[1:] - psi[:-1]) / dr_m
    r_cuadrado_caras = r_m[:-1] * r_m[1:]
    flujo_caras = r_cuadrado_caras * phi_en_caras * derivada_psi

    resultado = np.zeros(n_points)
    resultado[1:-1] = (flujo_caras[1:] - flujo_caras[:-1]) / factor_volumen_m3

    return resultado


# --- PRUEBA RÁPIDA (Se ejecuta al correr este archivo) ---
if __name__ == "__main__":
    mi_malla = crear_malla_esferica(r_b_m=0.00318, r_inf_m=0.25, n_points=100)
    psi_prueba = 1.0 / mi_malla["r_m"]
    phi_prueba = np.ones(100)

    laplaciano = calcular_difusion_esferica(mi_malla, psi_prueba, phi_prueba)
    error_maximo = np.max(np.abs(laplaciano[1:-1]))

    print("=== VERIFICACIÓN DE MALLA ESFÉRICA ===")
    print("Radio inicial (quemador):", mi_malla["r_m"][0], "m")
    print("Radio final (ambiente)  :", mi_malla["r_m"][-1], "m")
    print("Error máximo (debe ser ~0):", error_maximo)
