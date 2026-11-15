"""
ia/run_gemelo_3d.py
Orquestador Maestro sin fallbacks silenciosos (Corrige Hallazgo Crítico 3 y Alertas 1-4 de Kay).
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SOLVER_VERSION = "1.5.0-IGNIS-STATIC-AND-RUNTIME-VERIFIED"

try:
    from contract_si import SimulationInputSI, validate_input_si  # type: ignore
    from solver_3d import run_transient_simulation_3d, export_3d_state_for_ignis  # type: ignore
    from thermo_kinetics import compute_conservation_audit_3d  # type: ignore
    from domain_query import load_sflame_catalog, classify_operating_domain, compute_bayesian_bridge_metrics  # type: ignore
    from validation_sflame import validate_against_sflame_reference  # type: ignore
    from visualizer_3d import (  # type: ignore
        extract_spherical_shell_profiles,
        generate_3d_isosurface_plotly,
        generate_2d_slices_and_time_plots,
    )
    from verify_numerical import run_all_numerical_verifications  # type: ignore
    from openfoam_bridge import execute_or_fetch_openfoam_bridge  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI, validate_input_si
    from ia.solver_3d import run_transient_simulation_3d, export_3d_state_for_ignis
    from ia.thermo_kinetics import compute_conservation_audit_3d
    from ia.domain_query import load_sflame_catalog, classify_operating_domain, compute_bayesian_bridge_metrics
    from ia.validation_sflame import validate_against_sflame_reference
    from ia.visualizer_3d import (
        extract_spherical_shell_profiles,
        generate_3d_isosurface_plotly,
        generate_2d_slices_and_time_plots,
    )
    from ia.verify_numerical import run_all_numerical_verifications
    from ia.openfoam_bridge import execute_or_fetch_openfoam_bridge


DEFAULT_KAY_RESTRICTIONS = [
    "No interpretar voltajes como caudales masicos.",
    "No interpretar sensores crudos como temperatura K.",
    "No asumir que el orden SQL es cronologico.",
    "No asumir que el tiempo MFC esta sincronizado con las muestras instrumentales.",
    "No asignar parametros fisicos sin documentacion.",
    "No presentar simulaciones exploratorias como resultados validados contra NASA.",
]


def audit_ignis_contract_20013d1(payload_in: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    missing_list = list(payload_in.get("missing_physical_inputs", []))
    mfc_obs = payload_in.get("mfc_observations", {}) or {}
    raw_cond = payload_in.get("experimental_conditions_raw", {}) or {}
    data_status = payload_in.get("data_status", {}) or {}
    in_si = payload_in.get("input_validated_si", payload_in)

    if mfc_obs.get("voltage_to_mass_flow_calibrated") is False or data_status.get("mfc_mass_flow_calibration_verified") is False:
        reasons.append(
            "RECHAZO CIENTIFICO (Restriccion 1): 'voltage_to_mass_flow_calibrated' es false. "
            "Los 42 eventos en 20013D1_mfcSetpoints.csv están en voltios [V] y no pueden interpretarse como [kg/s]."
        )

    if len(missing_list) > 0:
        reasons.append(f"RECHAZO POR ENTRADAS FALTANTES (Restriccion 5): Faltan {len(missing_list)} entradas: {missing_list}.")

    if raw_cond.get("composition_basis_verified") is False:
        reasons.append(
            f"RECHAZO TERMOQUIMICO (Alerta 2): 'composition_basis_verified' es false para '{raw_cond.get('fuel_bottle_text')}'."
        )

    required_keys = ("pressure_Pa", "T_initial_K", "T_burner_K", "mass_flow_kg_s", "Y_F_burner", "Y_O_ambient")
    missing_in_si = [k for k in required_keys if k not in in_si or in_si.get(k) is None]
    if len(missing_in_si) > 0 and len(missing_list) == 0:
        reasons.append(f"RECHAZO SI: Faltan variables físicas obligatorias en SI: {missing_in_si}.")

    return {
        "can_run_as_nasa_validated": len(reasons) == 0,
        "rejection_reasons": reasons,
        "missing_physical_inputs_detected": missing_list if missing_list else missing_in_si,
    }


def run_simulation_for_ignis(
    input_dict: Optional[Dict[str, Any]] = None,
    export_npz: bool = True,
    run_verifications: bool = False,
    allow_benchmark_fallback: bool = False
) -> Dict[str, Any]:
    if input_dict is None:
        raise ValueError("Error: input_dict no puede ser None.")

    is_explicit_benchmark = bool(input_dict.get("is_benchmark", False) or allow_benchmark_fallback)
    audit = audit_ignis_contract_20013d1(input_dict)

    if not audit["can_run_as_nasa_validated"] and not is_explicit_benchmark:
        exp_ctx_strict = {
            "investigation_id": "PSI-23",
            "dataset": "ACME_S_FLAME",
            "experimental_file_key": "20013D1",
            "official_experiment_id": None,
            "test_day_code": "20013",
            "mfc_config_id": "20013D1_mfcSetpoints.csv",
            "measurement_file_id": "20013D1_data.csv",
            "domain_classification": "REJECTED_UNVERIFIED_NASA_INPUTS",
            "solver_backend": "INTERNAL_3D_FDM",
            "nasa_provenance_verified": False,
        }
        if isinstance(input_dict.get("experiment_context"), dict):
            exp_ctx_strict.update(input_dict["experiment_context"])
            exp_ctx_strict["domain_classification"] = "REJECTED_UNVERIFIED_NASA_INPUTS"
            exp_ctx_strict["nasa_provenance_verified"] = False

        return {
            "schema_version": input_dict.get("schema_version", "0.1-propuesta"),
            "status": "REJECTED_AS_NASA_VALIDATED_CASE",
            "solver_version": SOLVER_VERSION,
            "experiment_context": exp_ctx_strict,
            "experimental_conditions_raw": input_dict.get("experimental_conditions_raw", {
                "atmosphere_text": "~21% O2 with N4",
                "fuel_bottle_text": "66.7% H2 with CH4",
                "metadata_scope": "jornada",
                "composition_basis_verified": False,
            }),
            "mfc_observations": input_dict.get("mfc_observations", {
                "source_file": "20013D1_mfcSetpoints.csv",
                "number_of_events": 42,
                "reconstruction_status": "RECONSTRUIDO",
                "timezone_verified": False,
                "voltage_to_mass_flow_calibrated": False,
            }),
            "input_validated_si": {},
            "missing_physical_inputs": audit["missing_physical_inputs_detected"],
            "uq_perturbable_params": {},
            "simulation_result": None,
            "convergence_and_residuals": None,
            "quality_manifest_enforcement": {
                "restrictions_respected": DEFAULT_KAY_RESTRICTIONS,
                "rejection_reasons": audit["rejection_reasons"],
            },
            "inference_status": {
                "physical_likelihood_ready": False,
                "physical_posterior_computed": False,
                "causal_effect_identified": False,
            },
        }

    raw_si = input_dict.get("input_validated_si") if isinstance(input_dict.get("input_validated_si"), dict) and len(input_dict.get("input_validated_si")) > 0 else input_dict
    has_user_si = any(k in raw_si for k in ("pressure_Pa", "mass_flow_kg_s", "Y_O_ambient", "Y_F_burner", "fuel_type"))
    sim_input = validate_input_si(raw_si if has_user_si else SimulationInputSI().to_dict())

    catalog = load_sflame_catalog()
    domain_res = classify_operating_domain(sim_input, catalog)

    sim_res = run_transient_simulation_3d(sim_input)
    shells = extract_spherical_shell_profiles(
        sim_res["grid_dict"],
        sim_res["T_3d"],
        sim_res["Y_F_3d"],
        sim_res["Y_O_3d"],
        sim_res["q_chem_3d"],
        sim_res["Y_P_3d"],
    )

    npz_path = None
    foam_bridge_info = None
    if export_npz:
        npz_path = export_3d_state_for_ignis(sim_res, npz_path="ia/output_fields_3d.npz")
        foam_bridge_info = execute_or_fetch_openfoam_bridge(sim_input, case_dir="ia/openfoam_sflame_case")

    verif_report = run_all_numerical_verifications() if run_verifications else {"status": "SKIPPED_FAST_CALL"}
    conservation_audit = compute_conservation_audit_3d(sim_res, sim_input)
    val_report = validate_against_sflame_reference(
        shells, sim_res["predicted_flame_radius_m"], sim_res["max_temperature_K"], mdot_kg_s=sim_input.mass_flow_kg_s
    )

    conv_block = dict(sim_res["convergence_and_residuals"])
    conv_block["conservation_audit"] = conservation_audit
    conv_block["numerical_verification_suite"] = verif_report
    conv_block["analytical_1d_comparison"] = val_report

    dV = sim_res["grid_dict"]["dx"] ** 3
    q_total_W = float(np.sum(sim_res["q_chem_3d"]) * dV)
    bayesian_bridge = compute_bayesian_bridge_metrics(sim_input, sim_res["max_temperature_K"], q_total_W)

    is_benchmark = not audit["can_run_as_nasa_validated"]
    exp_ctx_out = {
        "investigation_id": "PSI-23",
        "dataset": "ACME_S_FLAME",
        "scenario_id": "BENCHMARK_SFLAME_C2H4" if is_benchmark else domain_res["experiment_id"],
        "experimental_file_key": None if is_benchmark else input_dict.get("experimental_file_key"),
        "valid_for_20013D1_validation": False,
        "domain_classification": "INDEPENDENT_NUMERICAL_VERIFICATION_BENCHMARK" if is_benchmark else domain_res["domain_classification"],
        "solver_backend": "INTERNAL_3D_FDM",
        "solver_version": SOLVER_VERSION,
        "openfoam_bridge_status": foam_bridge_info["bridge_status"] if foam_bridge_info else "NOT_REQUESTED",
        "nasa_provenance_verified": bool(domain_res["domain_classification"] == "DOCUMENTED_EXPERIMENT" and not is_benchmark),
    }

    g = sim_res["grid_dict"]
    simulation_result_block = {
        "execution_classification": (
            "ESCENARIO_INDEPENDIENTE_DE_VERIFICACION_NUMERICA (C2H4 - No valido para validar 20013D1 H2/CH4)"
            if is_benchmark else "SIMULACION_FISICA_CON_ENTRADAS_SI_COMPLETAS"
        ),
        "npz_3d_fields_file": npz_path,
        "units_si": {
            "T_3d": "K",
            "Y_F_3d": "-",
            "Y_O_3d": "-",
            "Y_P_3d": "-",
            "rho_3d": "kg/m^3",
            "u_3d": "m/s",
            "q_chem_3d": "W/m^3",
            "spatial_coordinates": "m",
            "time": "s",
        },
        "max_temperature_K": sim_res["max_temperature_K"],
        "predicted_flame_radius_m": sim_res["predicted_flame_radius_m"],
        "heat_release_rate_W": bayesian_bridge["heat_release_rate_W"],
        "radiative_power_W": bayesian_bridge["radiative_power_W"],
        "damkohler_number": bayesian_bridge["damkohler_number"],
        "stoichiometric_Z_st": bayesian_bridge["stoichiometric_Z_st"],
        "thermal_margin_K": bayesian_bridge["thermal_margin_K"],
        "T_extinction_threshold_ref_K": bayesian_bridge["T_extinction_threshold_ref_K"],
        "spatial_references_m": {
            "x_m": [round(float(v), 5) for v in g["x_m"]],
            "y_m": [round(float(v), 5) for v in g["y_m"]],
            "z_m": [round(float(v), 5) for v in g["z_m"]],
            "r_shells_m": [round(float(v), 5) for v in shells["r_shells_m"]],
        },
        "time_reference_s": sim_res["time_history_s"],
        "T_max_history_K": sim_res["T_max_history_K"],
        "r_f_history_m": sim_res["r_f_history_m"],
        "radial_shell_profiles": {
            "r_m": [round(float(x), 5) for x in shells["r_shells_m"]],
            "T_mean_K": [round(float(x), 2) for x in shells["T_mean_K"]],
            "Y_F_mean": [round(float(x), 5) for x in shells["Y_F_mean"]],
            "Y_O_mean": [round(float(x), 5) for x in shells["Y_O_mean"]],
            "Y_P_mean": [round(float(x), 5) for x in shells["Y_P_mean"]],
            "q_chem_mean_W_m3": [round(float(x), 2) for x in shells["q_chem_mean_W_m3"]],
        },
    }

    return {
        "schema_version": input_dict.get("schema_version", "0.1-propuesta"),
        "status": "SUCCESS_INDEPENDENT_NUMERICAL_BENCHMARK" if is_benchmark else "SUCCESS_VALIDATED_SI_RUN",
        "solver_version": SOLVER_VERSION,
        "experiment_context": exp_ctx_out,
        "domain_query_result": domain_res,
        "input_validated_si": sim_input.to_dict(),
        "missing_physical_inputs": [],
        "uq_perturbable_params": sim_input.uq_perturbations,
        "simulation_result": simulation_result_block,
        "convergence_and_residuals": conv_block,
        "bayesian_network_bridge": bayesian_bridge,
        "inference_status": {
            "physical_likelihood_ready": True,
            "physical_posterior_computed": False,
            "causal_effect_identified": False,
        },
    }


def execute_gemelo_3d_pipeline(input_data: Dict[str, Any], allow_benchmark: bool = True) -> Dict[str, Any]:
    payload = run_simulation_for_ignis(
        input_data,
        export_npz=True,
        run_verifications=True,
        allow_benchmark_fallback=allow_benchmark,
    )
    if payload.get("simulation_result") is not None:
        sim_input = validate_input_si(payload["input_validated_si"])
        sim_res = run_transient_simulation_3d(sim_input)
        generate_3d_isosurface_plotly(sim_res["grid_dict"], sim_res["T_3d"], "ia/output_flame_3d.html")
        generate_2d_slices_and_time_plots(sim_res, "ia/output_summary_panels.png")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Gemelo Digital 3D s-Flame + IGNIS-mu")
    parser.add_argument("--input", type=str, default=None, help="Ruta a contrato_ignis_20013D1.json")
    parser.add_argument("--output", type=str, default="output_ignis_benchmark.json", help="Ruta JSON salida")
    parser.add_argument("--mode", type=str, choices=["strict", "benchmark"], default="benchmark")
    args = parser.parse_args()

    if args.input and os.path.exists(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            user_in = json.load(f)
    else:
        user_in = {"is_benchmark": (args.mode == "benchmark")}

    final_json = execute_gemelo_3d_pipeline(user_in, allow_benchmark=(args.mode == "benchmark"))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2, ensure_ascii=False)

    print(f"Ejecución completada [{final_json.get('status')}] -> {args.output}")