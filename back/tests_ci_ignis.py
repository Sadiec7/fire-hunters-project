import hashlib
import pandas as pd
from motor_lojo_ignis import obtener_dataset_282_ensayos, algoritmo_cientifico_ignis
from pipeline_auditoria_nasa import auditar_experimento_nasa

def test_equivalencia_determinista_lojo():
    df = obtener_dataset_282_ensayos()
    assert len(df) == 282
    assert df["jornada_id"].nunique() == 18

    r1 = algoritmo_cientifico_ignis(df[df["jornada_id"] != 1], df[df["jornada_id"] == 1], 1, n_bootstrap=100)
    r2 = algoritmo_cientifico_ignis(df[df["jornada_id"] != 1], df[df["jornada_id"] == 1], 1, n_bootstrap=100)
    assert r1 == r2, "Fallo de determinismo numerico en LOJO"

def test_gate_temporal_no_inventa_tiempos():
    sample_rows = [{
        "c_archivo_origen": "20013D1_data.csv",
        "c_nombre_experimento": "PSI-23",
        "c_mfca1_gas:_1": "0.5",
        "c_thermocouple:_1": "1.56",
        "c_2020-06-08_160_23:41:56:378": "4.46"
    }]
    res = auditar_experimento_nasa(sample_rows)
    gate = res["gate_cientifico"]
    assert gate["mfc_timestamps_reconstructed"] is True
    assert gate["sensor_timestamps_verified"] is False
    assert gate["temporal_alignment_verified"] is False
    assert gate["ready_for_dynamic_scm"] is False
    assert res["reporte_calidad"]["auditoria_temporal"]["interpolacion_aplicada"] is False

if __name__ == "__main__":
    test_equivalencia_determinista_lojo()
    test_gate_temporal_no_inventa_tiempos()
    print("OK: Suite CI/CD de validacion cientifica e infraestructura superada.")