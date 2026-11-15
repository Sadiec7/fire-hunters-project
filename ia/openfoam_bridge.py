"""
ia/openfoam_bridge.py
Wrapper Conector de OpenFOAM (reactingFoam / fireFoam) para IGNIS-mu (Entregable 6).
"""

import os
import sys
from typing import Dict, Any, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import SimulationInputSI, validate_input_si  # type: ignore
    from solver_3d import run_transient_simulation_3d, export_3d_state_for_ignis  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI, validate_input_si
    from ia.solver_3d import run_transient_simulation_3d, export_3d_state_for_ignis


FOAM_HEADER_TEMPLATE = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.com                      |
|    \\\\/     M anipulation  | Case:     NASA ACME s-Flame Digital Twin        |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {foam_class};
    location    "{location}";
    object      {obj_name};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""


def generate_openfoam_case_files(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    case_dir: str = "ia/openfoam_sflame_case"
) -> Dict[str, str]:
    """Escribe los diccionarios 0/T, 0/U, 0/p, 0/Ydefault, constant/combustionProperties y system/controlDict."""
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    diluent = getattr(sim_input, "diluent_species", "N2")

    dir_0 = os.path.join(case_dir, "0")
    dir_const = os.path.join(case_dir, "constant")
    dir_sys = os.path.join(case_dir, "system")
    os.makedirs(dir_0, exist_ok=True)
    os.makedirs(dir_const, exist_ok=True)
    os.makedirs(dir_sys, exist_ok=True)

    files_written: Dict[str, str] = {}

    # 1. 0/T
    path_T = os.path.join(dir_0, "T")
    with open(path_T, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="T"))
        f.write(f"\ndimensions      [0 0 0 1 0 0 0];\ninternalField   uniform {sim_input.T_initial_K};\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.T_burner_K};\n    }}\n")
        f.write("    ambient\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.T_initial_K};\n    }}\n}}\n")
    files_written["0/T"] = path_T

    # 2. 0/p
    path_p = os.path.join(dir_0, "p")
    with open(path_p, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="p"))
        f.write(f"\ndimensions      [1 -1 -2 0 0 0 0];\ninternalField   uniform {sim_input.pressure_Pa};\n")
        f.write("boundaryField\n{\n    burner { type zeroGradient; }\n")
        f.write(f"    ambient {{ type fixedValue; value uniform {sim_input.pressure_Pa}; }}\n}}\n")
    files_written["0/p"] = path_p

    # 3. 0/U
    path_U = os.path.join(dir_0, "U")
    with open(path_U, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volVectorField", location="0", obj_name="U"))
        f.write("\ndimensions      [0 1 -1 0 0 0 0];\ninternalField   uniform (0 0 0);\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            flowRateInletVelocity;\n")
        f.write(f"        massFlowRate    constant {sim_input.mass_flow_kg_s};\n    }}\n")
        f.write("    ambient { type pressureInletOutletVelocity; value uniform (0 0 0); }\n}\n")
    files_written["0/U"] = path_U

    # 4. 0/Ydefault
    path_Y = os.path.join(dir_0, "Ydefault")
    with open(path_Y, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="Ydefault"))
        f.write(f"\ndimensions      [0 0 0 0 0 0 0];\ninternalField   uniform {sim_input.Y_O_ambient};\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.Y_F_burner};\n    }}\n")
        f.write(f"    ambient {{ type fixedValue; value uniform {sim_input.Y_O_ambient}; }}\n}}\n")
    files_written["0/Ydefault"] = path_Y

    # 5. constant/combustionProperties
    path_comb = os.path.join(dir_const, "combustionProperties")
    with open(path_comb, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(
            foam_class="dictionary", location="constant", obj_name="combustionProperties"
        ))
        f.write("\ncombustionModel laminar;\nactive          true;\n")
        f.write(f"fuel            {sim_input.fuel_type};\ndiluent         {diluent};\n")
    files_written["constant/combustionProperties"] = path_comb

    # 6. system/controlDict
    path_ctrl = os.path.join(dir_sys, "controlDict")
    with open(path_ctrl, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(
            foam_class="dictionary", location="system", obj_name="controlDict"
        ))
        f.write("\napplication     reactingFoam;\nstartFrom       startTime;\nstartTime       0;\n")
        f.write(f"stopAt          endTime;\nendTime         {sim_input.total_time_s};\n")
        f.write("deltaT          1e-4;\nwriteControl    adjustableRunTime;\nwriteInterval   0.1;\n")
    files_written["system/controlDict"] = path_ctrl

    return files_written


def execute_or_fetch_openfoam_bridge(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    case_dir: str = "ia/openfoam_sflame_case",
    export_npz_path: str = "ia/output_fields_3d.npz"
) -> Dict[str, Any]:
    """Genera el caso OpenFOAM y retorna los campos 3D estandarizados para IGNIS-mu."""
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    written_files = generate_openfoam_case_files(sim_input, case_dir=case_dir)
    sim_res = run_transient_simulation_3d(sim_input)
    npz_out = export_3d_state_for_ignis(sim_res, npz_path=export_npz_path)

    return {
        "openfoam_case_directory": case_dir,
        "openfoam_dictionaries_written": list(written_files.keys()),
        "npz_exported_path": npz_out,
        "simulation_results": sim_res,
    }


if __name__ == "__main__":
    info = execute_or_fetch_openfoam_bridge(SimulationInputSI(grid_nodes_per_axis=25, total_time_s=0.2))
    print("openfoam_bridge.py OK | Diccionarios creados:", info["openfoam_dictionaries_written"])
