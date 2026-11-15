from fastapi.testclient import TestClient
from ignis_core_api import app

client = TestClient(app)

def test_trazabilidad_psi23_exitosa():
    response = client.get("/api/v1/traceability/PSI-23")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "verificado"
    assert "experimento_maestro" in data
    assert isinstance(data["linaje_variables_y_transformaciones"], list)

def test_trazabilidad_experimento_inexistente():
    response = client.get("/api/v1/traceability/PSI-99999")
    assert response.status_code == 404

def test_registro_y_consulta_modelo_causal():
    payload = {
        "id_experimento": 2,
        "codigo_psi": "PSI-23",
        "nombre_modelo": "Test_SCM_Igniter",
        "version_modelo": "v0.1.0-test",
        "tipo_modelo": "SCM",
        "variable_tratamiento": "fuel_bottle",
        "variable_resultado": "flames_ignited",
        "estimacion_efecto": 0.415,
        "intervalo_confianza": {"inferior": 0.30, "superior": 0.53, "nivel": 0.95},
        "advertencias": ["Prueba automatizada de integración"],
        "payload_cientifico_raw": {"raw_score": 0.415, "converged": True}
    }
    post_res = client.post("/api/v1/causal-models/results", json=payload)
    assert post_res.status_code == 201
    assert post_res.json()["version_modelo"] == "v0.1.0-test"

    get_res = client.get("/api/v1/causal-models/PSI-23?version=v0.1.0-test")
    assert get_res.status_code == 200
    assert get_res.json()["resultados"][0]["estimacion_efecto"] == 0.415

def test_counterexample_engine_solo_datos_reales():
    payload = {
        "codigo_psi_referencia": "PSI-23",
        "conclusión_esperada_ignicion": True
    }
    response = client.post("/api/v1/counterexamples/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Excluidos" in data["filtro_integridad"]
    for item in data["contraejemplos"]:
        assert item["es_dato_real_verificado"] is True
def test_knowledge_graph_consulta():
    res = client.get("/api/v1/knowledge-graph/graph")
    assert res.status_code == 200
    data = res.json()
    assert data["estadisticas_grafo"]["total_nodos"] >= 5
    assert data["estadisticas_grafo"]["total_aristas"] >= 3

def test_evidence_card_generacion_y_bloqueo_sintetico():
    # 1. Debe bloquear fuentes sintéticas (Tarea 7)
    bad_payload = {
        "codigo_psi": "PSI-23",
        "titulo": "Prueba sintética",
        "observaciones": "Obs",
        "inferencias": "Inf",
        "incertidumbre": {"nivel": 0.95},
        "limitaciones": "Ninguna",
        "fuente_es_sintetica": True
    }
    res_block = client.post("/api/v1/evidence-cards/generate", json=bad_payload)
    assert res_block.status_code == 422

    # 2. Debe generar tarjeta válida con hash SHA-256 de 64 caracteres
    ok_payload = {**bad_payload, "fuente_es_sintetica": False}
    res_ok = client.post("/api/v1/evidence-cards/generate", json=ok_payload)
    assert res_ok.status_code == 201
    assert len(res_ok.json()["procedencia_verificable"]["sha256"]) == 64

def test_recomendacion_experimental():
    res = client.post("/api/v1/recommendations/next-experiments", json={"codigo_psi": "PSI-23", "umbral_minimo_muestras": 10})
    assert res.status_code == 200
    assert "experimentos_recomendados" in res.json()

def test_auditoria_sha256_integridad():
    res = client.post("/api/v1/audit/verify-integrity", json={
        "entidad_tipo": "Conclusion",
        "entidad_id": "TEST-001",
        "afirmacion": "El oxígeno favorece ignición en ACME",
        "referencia_experimental": "ACME",
        "es_sintetico": False,
        "payload_datos": {"x_o2": 0.21, "ignited": 1}
    })
    assert res.status_code == 200
    assert res.json()["aprobado"] is True
    assert len(res.json()["sha256_hash"]) == 64
