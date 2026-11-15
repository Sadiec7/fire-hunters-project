"""
ia/operators_3d.py
Operadores Diferenciales 3D Vectorizados (Difusión y Advección Upwind) - Bloque 4.
"""

from typing import Tuple, Dict, Any
import numpy as np


def laplacian_3d(phi: np.ndarray, dx: float, dy: float, dz: float) -> np.ndarray:
    """Calcula el Laplaciano 3D por diferencias finitas centradas de 2do orden vectorizadas."""
    lap = np.zeros_like(phi, dtype=np.float64)

    d2x = (phi[2:, 1:-1, 1:-1] - 2.0 * phi[1:-1, 1:-1, 1:-1] + phi[:-2, 1:-1, 1:-1]) / (dx * dx)
    d2y = (phi[1:-1, 2:, 1:-1] - 2.0 * phi[1:-1, 1:-1, 1:-1] + phi[1:-1, :-2, 1:-1]) / (dy * dy)
    d2z = (phi[1:-1, 1:-1, 2:] - 2.0 * phi[1:-1, 1:-1, 1:-1] + phi[1:-1, 1:-1, :-2]) / (dz * dz)

    lap[1:-1, 1:-1, 1:-1] = d2x + d2y + d2z
    return lap


def advection_upwind_3d(
    phi: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray,
    dx: float,
    dy: float,
    dz: float
) -> np.ndarray:
    """Calcula el término convectivo u · grad(phi) usando esquema Upwind 3D vectorizado."""
    adv = np.zeros_like(phi, dtype=np.float64)

    ux_in = u_x[1:-1, 1:-1, 1:-1]
    uy_in = u_y[1:-1, 1:-1, 1:-1]
    uz_in = u_z[1:-1, 1:-1, 1:-1]

    dphi_dx_bwd = (phi[1:-1, 1:-1, 1:-1] - phi[:-2, 1:-1, 1:-1]) / dx
    dphi_dx_fwd = (phi[2:, 1:-1, 1:-1] - phi[1:-1, 1:-1, 1:-1]) / dx
    adv_x = np.where(ux_in >= 0.0, ux_in * dphi_dx_bwd, ux_in * dphi_dx_fwd)

    dphi_dy_bwd = (phi[1:-1, 1:-1, 1:-1] - phi[1:-1, :-2, 1:-1]) / dy
    dphi_dy_fwd = (phi[1:-1, 2:, 1:-1] - phi[1:-1, 1:-1, 1:-1]) / dy
    adv_y = np.where(uy_in >= 0.0, uy_in * dphi_dy_bwd, uy_in * dphi_dy_fwd)

    dphi_dz_bwd = (phi[1:-1, 1:-1, 1:-1] - phi[1:-1, 1:-1, :-2]) / dz
    dphi_dz_fwd = (phi[1:-1, 1:-1, 2:] - phi[1:-1, 1:-1, 1:-1]) / dz
    adv_z = np.where(uz_in >= 0.0, uz_in * dphi_dz_bwd, uz_in * dphi_dz_fwd)

    adv[1:-1, 1:-1, 1:-1] = adv_x + adv_y + adv_z
    return adv


def step_species_transport_only(
    Y_F_3d: np.ndarray,
    Y_O_3d: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    u_z: np.ndarray,
    grid_dict: Dict[str, Any],
    D_F: float,
    D_O: float,
    dt: float,
    Y_F_burner: float = 1.0,
    Y_O_ambient: float = 0.233
) -> Tuple[np.ndarray, np.ndarray]:
    """Avanza un paso dt de transporte puro de especies sin reacción química (Sync Point 3)."""
    dx, dy, dz = grid_dict["dx"], grid_dict["dy"], grid_dict["dz"]

    lap_F = laplacian_3d(Y_F_3d, dx, dy, dz)
    adv_F = advection_upwind_3d(Y_F_3d, u_x, u_y, u_z, dx, dy, dz)
    Y_F_next = Y_F_3d + dt * (D_F * lap_F - adv_F)

    lap_O = laplacian_3d(Y_O_3d, dx, dy, dz)
    adv_O = advection_upwind_3d(Y_O_3d, u_x, u_y, u_z, dx, dy, dz)
    Y_O_next = Y_O_3d + dt * (D_O * lap_O - adv_O)

    Y_F_next = np.clip(Y_F_next, 0.0, 1.0)
    Y_O_next = np.clip(Y_O_next, 0.0, 1.0)

    mask_b = grid_dict["mask_burner"]
    mask_o = grid_dict["mask_outer"]
    Y_F_next[mask_b] = Y_F_burner
    Y_O_next[mask_b] = 0.0
    Y_F_next[mask_o] = 0.0
    Y_O_next[mask_o] = Y_O_ambient

    return Y_F_next, Y_O_next


if __name__ == "__main__":
    test_cube = np.ones((21, 21, 21), dtype=np.float64) * 300.0
    lap_res = laplacian_3d(test_cube, 0.001, 0.001, 0.001)
    print(f"Operadores 3D listos | Max Laplaciano campo constante: {np.max(np.abs(lap_res)):.2e}")