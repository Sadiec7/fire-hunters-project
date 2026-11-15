"""
ia/grid_3d.py
Malla Cartesiana 3D con verificación de resolución del quemador, ejes (x_m, y_m, z_m)
y deriva boyante por microgravedad residual (g_res) para IGNIS-mu.
"""

import math
from typing import Dict, Any, Tuple, Optional, Sequence
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

    x_m = np.linspace(-L, L, N, dtype=np.float64)
    y_m = np.linspace(-L, L, N, dtype=np.float64)
    z_m = np.linspace(-L, L, N, dtype=np.float64)

    dx = float((2.0 * L) / (N - 1))
    dy = dx
    dz = dx

    # Verificación de nodos dentro del diámetro del quemador poroso (2 * r_b)
    nodes_across_burner = (2.0 * r_b) / dx
    burner_resolution_ok = bool(nodes_across_burner >= 3.5)

    X, Y, Z = np.meshgrid(x_m, y_m, z_m, indexing="ij")
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
        "x": x_m,
        "y": y_m,
        "z": z_m,
        "x_m": x_m,
        "y_m": y_m,
        "z_m": z_m,
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
        "nodes_across_burner_diameter": round(float(nodes_across_burner), 2),
        "burner_resolution_ok": burner_resolution_ok,
    }


def compute_prescribed_velocity_3d(
    grid_dict: Dict[str, Any],
    mass_flow_kg_s: float,
    rho_kg_m3: float,
    T_3d: Optional[np.ndarray] = None,
    T_ambient_K: float = 298.15,
    residual_gravity_m_s2: float = 0.0,
    gravity_direction_unit: Sequence[float] = (0.0, 0.0, 1.0)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcula velocidad radial 3D + deriva boyante de 1er orden por microgravedad residual."""
    X = grid_dict["X"]
    Y = grid_dict["Y"]
    Z = grid_dict["Z"]
    R_safe = grid_dict["R_safe"]
    mask_burner = grid_dict["mask_burner"]

    factor = float(mass_flow_kg_s) / (4.0 * math.pi * float(rho_kg_m3) * (R_safe**3))
    u_x = factor * X
    u_y = factor * Y
    u_z = factor * Z

    if T_3d is not None and abs(residual_gravity_m_s2) > 0.0:
        g_vec = np.asarray(gravity_direction_unit, dtype=np.float64)
        g_norm = float(np.linalg.norm(g_vec))
        if g_norm > 1e-12:
            g_vec = g_vec / g_norm
        else:
            g_vec = np.array([0.0, 0.0, 1.0], dtype=np.float64)

        T_safe = np.maximum(T_3d, T_ambient_K)
        buoyancy_factor = np.clip(1.0 - (T_ambient_K / T_safe), 0.0, 0.9)
        char_time_s = 0.25
        delta_u_g = char_time_s * buoyancy_factor * float(residual_gravity_m_s2)

        u_x = u_x + delta_u_g * g_vec[0]
        u_y = u_y + delta_u_g * g_vec[1]
        u_z = u_z + delta_u_g * g_vec[2]

    u_x = np.where(mask_burner, 0.0, u_x)
    u_y = np.where(mask_burner, 0.0, u_y)
    u_z = np.where(mask_burner, 0.0, u_z)

    return u_x, u_y, u_z


if __name__ == "__main__":
    g = create_cartesian_grid_3d(0.035, 41, 0.00318)
    ux, uy, uz = compute_prescribed_velocity_3d(g, 2.5e-6, 1.15)
    print(f"grid_3d.py OK | Nodos en diámetro quemador: {g['nodes_across_burner_diameter']}")
