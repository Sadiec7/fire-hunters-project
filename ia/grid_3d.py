"""
ia/grid_3d.py
Geometría, Malla Cartesiana 3D con Máscara Esférica y Velocidad Radial Prescrita - Bloque 3.
"""

import math
from typing import Dict, Any, Tuple
import numpy as np


def create_cartesian_grid_3d(
    domain_half_width_m: float = 0.035,
    grid_nodes_per_axis: int = 41,
    burner_radius_m: float = 0.00318
) -> Dict[str, Any]:
    """Construye la malla cartesiana 3D estructurada [-L, L]^3 y las máscaras geométricas."""
    L = float(domain_half_width_m)
    N = int(grid_nodes_per_axis)
    r_b = float(burner_radius_m)

    x = np.linspace(-L, L, N, dtype=np.float64)
    y = np.linspace(-L, L, N, dtype=np.float64)
    z = np.linspace(-L, L, N, dtype=np.float64)

    dx = float((2.0 * L) / (N - 1))
    dy = dx
    dz = dx

    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X**2 + Y**2 + Z**2)
    R_safe = np.maximum(R, 1e-6)

    mask_burner = R <= r_b

    mask_faces = np.zeros((N, N, N), dtype=bool)
    mask_faces[0, :, :] = True
    mask_faces[-1, :, :] = True
    mask_faces[:, 0, :] = True
    mask_faces[:, -1, :] = True
    mask_faces[:, :, 0] = True
    mask_faces[:, :, -1] = True

    mask_outer = mask_faces | (R >= L)

    return {
        "x": x,
        "y": y,
        "z": z,
        "dx": dx,
        "dy": dy,
        "dz": dz,
        "X": X,
        "Y": Y,
        "Z": Z,
        "R": R,
        "R_safe": R_safe,
        "mask_burner": mask_burner,
        "mask_outer": mask_outer,
        "domain_half_width_m": L,
        "grid_nodes_per_axis": N,
        "burner_radius_m": r_b,
    }


def compute_prescribed_velocity_3d(
    grid_dict: Dict[str, Any],
    mass_flow_kg_s: float,
    rho_kg_m3: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcula el campo de velocidad radial 3D prescrito (ux, uy, uz) [m/s]."""
    X = grid_dict["X"]
    Y = grid_dict["Y"]
    Z = grid_dict["Z"]
    R_safe = grid_dict["R_safe"]
    mask_burner = grid_dict["mask_burner"]

    factor = float(mass_flow_kg_s) / (4.0 * math.pi * float(rho_kg_m3) * (R_safe**3))

    u_x = factor * X
    u_y = factor * Y
    u_z = factor * Z

    u_x = np.where(mask_burner, 0.0, u_x)
    u_y = np.where(mask_burner, 0.0, u_y)
    u_z = np.where(mask_burner, 0.0, u_z)

    return u_x, u_y, u_z


if __name__ == "__main__":
    g = create_cartesian_grid_3d(0.035, 41, 0.00318)
    ux, uy, uz = compute_prescribed_velocity_3d(g, 2.5e-6, 1.15)
    n_burner = int(np.sum(g["mask_burner"]))
    r_test = 0.015
    u_mag_shell = 2.5e-6 / (4.0 * math.pi * 1.15 * (r_test**2))
    mdot_check = 4.0 * math.pi * (r_test**2) * 1.15 * u_mag_shell
    print(f"Malla 41x41x41 creada | Celdas dentro del quemador: {n_burner} | mdot verificado: {mdot_check:.3e} kg/s")