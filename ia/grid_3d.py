"""
ia/grid_3d.py
Malla Cartesiana 3D pura en memoria (compatible con ray.put() Zero-Copy),
verificación de resolución del quemador, ejes (x_m, y_m, z_m) y campo de velocidad 3D
acoplado con microgravedad residual (g_res), ventilación ECLSS (U_ECLSS) y viento iónico (E_FIELD).
"""

import math
from typing import Dict, Any, Tuple, Optional, Sequence, Union
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
    gravity_direction_unit: Sequence[float] = (0.0, 0.0, 1.0),
    u_eclss_m_s: Union[float, Sequence[float]] = (0.0, 0.0, 0.0),
    e_field_v_m: Union[float, Sequence[float]] = 0.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcula velocidad radial 3D + deriva boyante (g_res) + ventilación (U_ECLSS) + viento iónico (E_FIELD)."""
    X = grid_dict["X"]
    Y = grid_dict["Y"]
    Z = grid_dict["Z"]
    R_safe = grid_dict["R_safe"]
    r_b = float(grid_dict["burner_radius_m"])
    mask_burner = grid_dict["mask_burner"]

    factor = float(mass_flow_kg_s) / (4.0 * math.pi * float(rho_kg_m3) * (R_safe**3))
    u_x = factor * X
    u_y = factor * Y
    u_z = factor * Z

    if T_3d is not None and abs(residual_gravity_m_s2) > 0.0:
        g_vec = np.asarray(gravity_direction_unit, dtype=np.float64)
        g_norm = float(np.linalg.norm(g_vec))
        g_vec = (g_vec / g_norm) if g_norm > 1e-12 else np.array([0.0, 0.0, 1.0], dtype=np.float64)

        T_safe = np.maximum(T_3d, T_ambient_K)
        buoyancy_factor = np.clip(1.0 - (T_ambient_K / T_safe), 0.0, 0.9)
        char_time_s = 0.25
        delta_u_g = char_time_s * buoyancy_factor * float(residual_gravity_m_s2)

        u_x = u_x + delta_u_g * g_vec[0]
        u_y = u_y + delta_u_g * g_vec[1]
        u_z = u_z + delta_u_g * g_vec[2]

    if isinstance(u_eclss_m_s, (int, float)):
        u_eclss_vec = np.array([float(u_eclss_m_s), 0.0, 0.0], dtype=np.float64)
    else:
        arr_u = np.asarray(u_eclss_m_s, dtype=np.float64).flatten()
        u_eclss_vec = arr_u[:3] if arr_u.size >= 3 else np.array([float(arr_u[0]) if arr_u.size > 0 else 0.0, 0.0, 0.0])

    if float(np.linalg.norm(u_eclss_vec)) > 1e-12:
        radial_damping = np.clip(1.0 - (r_b / R_safe) ** 2, 0.0, 1.0) * 0.02
        u_x = u_x + radial_damping * u_eclss_vec[0]
        u_y = u_y + radial_damping * u_eclss_vec[1]
        u_z = u_z + radial_damping * u_eclss_vec[2]

    if isinstance(e_field_v_m, (int, float)):
        e_vec = np.array([0.0, 0.0, float(e_field_v_m)], dtype=np.float64)
    else:
        arr_e = np.asarray(e_field_v_m, dtype=np.float64).flatten()
        e_vec = arr_e[:3] if arr_e.size >= 3 else np.array([0.0, 0.0, float(arr_e[0]) if arr_e.size > 0 else 0.0])

    e_mag = float(np.linalg.norm(e_vec))
    if T_3d is not None and e_mag > 1e-6:
        ion_zone = np.clip((T_3d - 950.0) / 800.0, 0.0, 1.0)
        u_ion_drift = 1.5e-6 * ion_zone
        u_x = u_x + u_ion_drift * e_vec[0]
        u_y = u_y + u_ion_drift * e_vec[1]
        u_z = u_z + u_ion_drift * e_vec[2]

    u_x = np.where(mask_burner, 0.0, u_x)
    u_y = np.where(mask_burner, 0.0, u_y)
    u_z = np.where(mask_burner, 0.0, u_z)

    return u_x, u_y, u_z


if __name__ == "__main__":
    g = create_cartesian_grid_3d(0.035, 41, 0.00318)
    ux, uy, uz = compute_prescribed_velocity_3d(g, 2.5e-6, 1.15)
    print(f"grid_3d.py OK | Nodos en diametro quemador: {g['nodes_across_burner_diameter']}")