"""
ia/openfoam_bridge.py
Wrapper generador de diccionarios para OpenFOAM (reactingFoam).
Corrige Hallazgo Alto 2: Verifica con shutil.which si 'reactingFoam' está instalado y reporta con
total transparencia cuando solo se generan los archivos de configuración sin ejecutar el binario C++.
"""

import os
import sys
import shutil
from typing import Dict, Any, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import SimulationInputSI, validate_input_si  # type: ignore
except ImportError:
    from ia.contract_si import SimulationInputSI, validate_input_si


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

    path_T = os.path.join(dir_0, "T")
    with open(path_T, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="T"))
        f.write(f"\ndimensions      [0 0 0 1 0 0 0];\ninternalField   uniform {sim_input.T_initial_K};\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.T_burner_K};\n    }}\n")
        f.write("    ambient\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.T_initial_K};\n    }}\n}}\n")
    files_written["0/T"] = path_T

    path_p = os.path.join(dir_0, "p")
    with open(path_p, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="p"))
        f.write(f"\ndimensions      [1 -1 -2 0 0 0 0];\ninternalField   uniform {sim_input.pressure_Pa};\n")
        f.write("boundaryField\n{\n    burner { type zeroGradient; }\n")
        f.write(f"    ambient {{ type fixedValue; value uniform {sim_input.pressure_Pa}; }}\n}}\n")
    files_written["0/p"] = path_p

    path_U = os.path.join(dir_0, "U")
    with open(path_U, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volVectorField", location="0", obj_name="U"))
        f.write("\ndimensions      [0 1 -1 0 0 0 0];\ninternalField   uniform (0 0 0);\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            flowRateInletVelocity;\n")
        f.write(f"        massFlowRate    constant {sim_input.mass_flow_kg_s};\n    }}\n")
        f.write("    ambient { type pressureInletOutletVelocity; value uniform (0 0 0); }\n}\n")
    files_written["0/U"] = path_U

    path_Y = os.path.join(dir_0, "Ydefault")
    with open(path_Y, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="volScalarField", location="0", obj_name="Ydefault"))
        f.write(f"\ndimensions      [0 0 0 0 0 0 0];\ninternalField   uniform {sim_input.Y_O_ambient};\n")
        f.write("boundaryField\n{\n    burner\n    {\n        type            fixedValue;\n")
        f.write(f"        value           uniform {sim_input.Y_F_burner};\n    }}\n")
        f.write(f"    ambient {{ type fixedValue; value uniform {sim_input.Y_O_ambient}; }}\n}}\n")
    files_written["0/Ydefault"] = path_Y

    path_comb = os.path.join(dir_const, "combustionProperties")
    with open(path_comb, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="dictionary", location="constant", obj_name="combustionProperties"))
        f.write("\ncombustionModel laminar;\nactive          true;\n")
        f.write(f"fuel            {sim_input.fuel_type};\ndiluent         {diluent};\n")
    files_written["constant/combustionProperties"] = path_comb

    path_ctrl = os.path.join(dir_sys, "controlDict")
    with open(path_ctrl, "w", encoding="utf-8") as f:
        f.write(FOAM_HEADER_TEMPLATE.format(foam_class="dictionary", location="system", obj_name="controlDict"))
        f.write("\napplication     reactingFoam;\nstartFrom       startTime;\nstartTime       0;\n")
        f.write(f"stopAt          endTime;\nendTime         {sim_input.total_time_s};\n")
        f.write("deltaT          1e-4;\nwriteControl    adjustableRunTime;\nwriteInterval   0.1;\n")
    files_written["system/controlDict"] = path_ctrl

    return files_written


def execute_or_fetch_openfoam_bridge(
    sim_input: Union[SimulationInputSI, Dict[str, Any]],
    case_dir: str = "ia/openfoam_sflame_case"
) -> Dict[str, Any]:
    """
    CORRECCIÓN HALLAZGO ALTO 2:
    No ejecuta el solver de NumPy haciéndolo pasar por OpenFOAM.
    Verifica honestamente si 'reactingFoam' existe en PATH y reporta su estado real.
    """
    if isinstance(sim_input, dict):
        sim_input = validate_input_si(sim_input)

    written_files = generate_openfoam_case_files(sim_input, case_dir=case_dir)
    foam_bin = shutil.which("reactingFoam")

    return {
        "openfoam_case_directory": case_dir,
        "openfoam_dictionaries_written": list(written_files.keys()),
        "openfoam_binary_found_in_path": foam_bin is not None,
        "openfoam_binary_executed": False,
        "bridge_status": (
            "READY_FOR_REACTINGFOAM_EXECUTION"
            if foam_bin is not None
            else "CASE_DICTIONARIES_GENERATED_ONLY_REACTINGFOAM_NOT_INSTALLED"
        ),
    }