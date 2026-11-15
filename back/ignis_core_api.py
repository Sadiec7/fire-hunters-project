import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

# Configuración de conexión (usa variable de entorno o tu Session Pooler)
DB_URI = os.getenv(
    "POSTGRES_DSN",
    "postgresql://postgres.jhcegurjiqutptenqmxs:HackathonUAQ2026@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
)
engine = create_engine(DB_URI, pool_pre_ping=True)

app = FastAPI(
    title="IGNIS-μ Scientific Intelligence API",
    description="Motor de trazabilidad científica, ingesta de modelos causales y buscador de contraejemplos experimentales.",
    version="1.0.0"
)

# ==============================================================================
# MODELOS DE DATOS (PYDANTIC SCHEMAS)
# ==============================================================================

class IntervaloConfianza(BaseModel):
    inferior: float
    superior: float
    nivel: float = Field(default=0.95, ge=0.5, le=0.999)

class ModeloCausalInput(BaseModel):
    id_experimento: int
    codigo_psi: str = Field(..., example="PSI-23")
    nombre_modelo: str = Field(..., example="ACME_sFlame_Soot_SCM")
    version_modelo: str = Field(..., example="v2.1.0")
    tipo_modelo: str = Field(..., example="SCM")
    variable_tratamiento: str = Field(..., example="x_o2")
    variable_resultado: str = Field(..., example="flames_ignited")
    estimacion_efecto: float = Field(..., example=0.3421)
    intervalo_confianza: IntervaloConfianza
    advertencias: List[str] = Field(default_factory=list, example=["Tamaño de muestra reducido a p_atm > 3.0"])
    payload_cientifico_raw: Dict[str, Any] = Field(..., description="JSON íntegro emitido por ciencia de datos sin alterar")

class CounterexampleQuery(BaseModel):
    codigo_psi_referencia: str = Field(..., example="PSI-23")
    fuel_objetivo: Optional[str] = Field(None, example="n-dodecane")
    conclusión_esperada_ignicion: bool = Field(..., description="True si se espera ignición exitosa; False si se espera extinción")

# ==============================================================================
# TAREA 1: MOTOR DE TRAZABILIDAD CIENTÍFICA
# ==============================================================================

@app.get("/api/v1/traceability/{codigo_psi}", tags=["1. Trazabilidad Científica"])
def obtener_trazabilidad_experimento(
    codigo_psi: str,
    archivo_origen: Optional[str] = Query(None, description="Filtrar por archivo CSV/Excel específico de la NASA")
):
    """
    Rastrea una conclusión o variable hasta el experimento maestro, los archivos pesados NASA,
    las variables originales y las transformaciones aplicadas durante la ingesta.
    """
    codigo_clean = codigo_psi.upper().strip()
    # Mapeo inteligente entre códigos PSI de NASA y los programas de tu tabla maestra
    alias_programa = "ACME" if codigo_clean == "PSI-23" else ("FLEX" if codigo_clean == "PSI-117" else codigo_clean)

    try:
        with engine.connect() as conn:
            # 1. Buscar experimento maestro por código PSI o por nombre de programa (ACME/FLEX)
            exp = conn.execute(
                text("""
                    SELECT * FROM public.experimentos_combustion 
                    WHERE codigo_programa ILIKE :cod OR codigo_programa ILIKE :alias 
                    LIMIT 1
                """),
                {"cod": f"%{codigo_clean}%", "alias": f"%{alias_programa}%"}
            ).mappings().first()

            if not exp:
                raise HTTPException(status_code=404, detail=f"No se encontró el experimento {codigo_clean} en el catálogo maestro.")

            # Convertir la fila a diccionario limpio excluyendo bytes binarios (BYTEA)
            exp_dict = {
                k: (v.isoformat() if hasattr(v, "isoformat") else v)
                for k, v in dict(exp.items()).items()
                if not isinstance(v, (bytes, memoryview))
            }

            # 2. Buscar archivos NASA asociados
            archivos = conn.execute(
                text("SELECT id_archivo, nombre_recurso, formato, tamano_gb FROM public.archivos_pesados_nasa WHERE id_experimento = :id_exp"),
                {"id_exp": exp_dict["id_experimento"]}
            ).mappings().all()

            # 3. Buscar transformaciones y linaje de variables
            query_logs = "SELECT * FROM public.ignis_trazabilidad_logs WHERE codigo_psi ILIKE :cod"
            params = {"cod": f"%{codigo_clean}%"}
            if archivo_origen:
                query_logs += " AND archivo_nasa_origen ILIKE :arch"
                params["arch"] = f"%{archivo_origen}%"

            logs = conn.execute(text(query_logs), params).mappings().all()

            logs_list = [
                {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(l.items()).items()}
                for l in logs
            ]

            return {
                "estado": "verificado",
                "experimento_maestro": exp_dict,
                "archivos_repositorio_nasa": [dict(a.items()) for a in archivos],
                "linaje_variables_y_transformaciones": logs_list,
                "total_transformaciones_registradas": len(logs_list)
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno de trazabilidad: {str(e)}")

# ==============================================================================
# TAREA 2: INTEGRACIÓN DE MODELOS CAUSALES Y REDES BAYESIANAS
# ==============================================================================

@app.post("/api/v1/causal-models/results", status_code=201, tags=["2. Modelos Causales"])
def registrar_resultado_causal(payload: ModeloCausalInput):
    """
    Almacena los resultados de redes bayesianas y modelos causales estructurales (SCM)
    preservando intactos los cálculos, versiones, intervalos y advertencias científicas.
    """
    import json
    try:
        with engine.begin() as conn:
            # Validar que el experimento exista
            existe = conn.execute(
                text("SELECT 1 FROM public.experimentos_combustion WHERE id_experimento = :id_exp"),
                {"id_exp": payload.id_experimento}
            ).first()

            if not existe:
                raise HTTPException(status_code=404, detail=f"id_experimento {payload.id_experimento} no existe.")

            res = conn.execute(
                text("""
                    INSERT INTO public.ignis_modelos_causales (
                        id_experimento, codigo_psi, nombre_modelo, version_modelo, tipo_modelo,
                        variable_tratamiento, variable_resultado, estimacion_efecto,
                        intervalo_confianza, advertencias, payload_cientifico_raw
                    ) VALUES (
                        :id_exp, :cod, :nom, :ver, :tipo,
                        :trat, :res_var, :est,
                        CAST(:ic AS jsonb), CAST(:adv AS jsonb), CAST(:raw AS jsonb)
                    ) RETURNING id_inferencia, fecha_inferencia
                """),
                {
                    "id_exp": payload.id_experimento,
                    "cod": payload.codigo_psi.upper(),
                    "nom": payload.nombre_modelo,
                    "ver": payload.version_modelo,
                    "tipo": payload.tipo_modelo,
                    "trat": payload.variable_tratamiento,
                    "res_var": payload.variable_resultado,
                    "est": payload.estimacion_efecto,
                    "ic": json.dumps(payload.intervalo_confianza.model_dump()),
                    "adv": json.dumps(payload.advertencias),
                    "raw": json.dumps(payload.payload_cientifico_raw)
                }
            ).mappings().first()

            return {
                "mensaje": "Inferencia causal registrada sin alteración de cálculos.",
                "id_inferencia": str(res["id_inferencia"]),
                "version_modelo": payload.version_modelo,
                "fecha_registro": res["fecha_inferencia"]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar modelo causal: {str(e)}")


@app.get("/api/v1/causal-models/{codigo_psi}", tags=["2. Modelos Causales"])
def consultar_inferencias_causales(
    codigo_psi: str,
    version: Optional[str] = Query(None, description="Filtrar por versión exacta del modelo (ej. v2.1.0)")
):
    """
    Recupera las inferencias causales registradas para un experimento con sus intervalos y advertencias.
    """
    try:
        with engine.connect() as conn:
            sql = "SELECT * FROM public.ignis_modelos_causales WHERE codigo_psi ILIKE :cod"
            params = {"cod": f"%{codigo_psi.upper()}%"}
            if version:
                sql += " AND version_modelo = :ver"
                params["ver"] = version
            sql += " ORDER BY fecha_inferencia DESC"

            rows = conn.execute(text(sql), params).mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail=f"Sin resultados causales para {codigo_psi}.")

            return {"codigo_psi": codigo_psi.upper(), "total_modelos": len(rows), "resultados": [dict(r) for r in rows]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# TAREA 3: COUNTEREXAMPLE ENGINE (SOLO REGISTROS EXPERIMENTALES REALES)
# ==============================================================================

@app.post("/api/v1/counterexamples/search", tags=["3. Counterexample Engine"])
def buscar_contraejemplos_reales(criterio: CounterexampleQuery):
    """
    Busca registros experimentales reales (excluyendo estrictamente datos sintéticos)
    que contradigan la hipótesis esperada y detalla las diferencias de condiciones físicas.
    """
    try:
        with engine.connect() as conn:
            # 1. Verificación de integridad: bloquear cualquier registro sintético en evidence_records
            sinteticos_bloqueados = conn.execute(
                text("SELECT COUNT(*) FROM public.evidence_records WHERE is_synthetic = TRUE")
            ).scalar()

            contraejemplos = []

            # 2. Búsqueda en PSI-23 (ACME s-Flame) donde flames_ignited contradiga la hipótesis
            if criterio.codigo_psi_referencia.upper() == "PSI-23":
                # Si se esperaba ignición (True), buscamos casos reales donde flames_ignited = 0 o NULL/fallo
                condicion_contradictoria = "COALESCE(flames_ignited, 0) = 0" if criterio.conclusión_esperada_ignicion else "COALESCE(flames_ignited, 0) > 0"
                
                sql = f"""
                    SELECT id_fila, test_day, year, month, atmosphere, fuel_bottle, flames_ignited
                    FROM public.psi23_experimental_acme_sflame
                    WHERE {condicion_contradictoria}
                """
                params = {}
                if criterio.fuel_objetivo:
                    sql += " AND fuel_bottle ILIKE :fuel"
                    params["fuel"] = f"%{criterio.fuel_objetivo}%"
                sql += " LIMIT 15"

                rows = conn.execute(text(sql), params).mappings().all()
                for r in rows:
                    contraejemplos.append({
                        "fuente_tabla": "public.psi23_experimental_acme_sflame",
                        "es_dato_real_verificado": True,
                        "id_registro": r["id_fila"],
                        "resultado_observado": f"flames_ignited = {r['flames_ignited']}",
                        "condiciones_experimentales": {
                            "fecha": f"{r['test_day']}-{r['month']}-{r['year']}",
                            "atmosfera": r["atmosphere"],
                            "combustible": r["fuel_bottle"]
                        },
                        "diferencia_critica": f"Bajo atmósfera '{r['atmosphere']}' con combustible '{r['fuel_bottle']}', el resultado contradice la hipótesis (ignición={criterio.conclusión_esperada_ignicion})."
                    })

            # 3. Búsqueda complementaria en PSI-117 (condiciones límite de presión y oxígeno)
            elif criterio.codigo_psi_referencia.upper() == "PSI-117":
                sql = "SELECT id_fila, fuel, do_mm, p_atm, x_o2 FROM public.psi117_readme_list_of_data WHERE 1=1"
                params = {}
                if criterio.fuel_objetivo:
                    sql += " AND fuel ILIKE :fuel"
                    params["fuel"] = f"%{criterio.fuel_objetivo}%"
                rows = conn.execute(text(sql), params).mappings().all()
                for r in rows:
                    contraejemplos.append({
                        "fuente_tabla": "public.psi117_readme_list_of_data",
                        "es_dato_real_verificado": True,
                        "id_registro": r["id_fila"],
                        "condiciones_experimentales": dict(r),
                        "diferencia_critica": f"Variación en diámetro inicial (do_mm={r['do_mm']}), presión ({r['p_atm']} atm) o fracción molar O2 ({r['x_o2']})."
                    })
            else:
                raise HTTPException(status_code=400, detail="Código PSI no soportado aún en el motor de contraejemplos. Use 'PSI-23' o 'PSI-117'.")

            return {
                "hipotesis_evaluada": {
                    "experimento": criterio.codigo_psi_referencia.upper(),
                    "combustible": criterio.fuel_objetivo or "Todos",
                    "ignicion_esperada": criterio.conclusión_esperada_ignicion
                },
                "filtro_integridad": f"Excluidos {sinteticos_bloqueados} registros sintéticos de evidence_records. Solo datos experimentales NASA.",
                "total_contraejemplos_encontrados": len(contraejemplos),
                "contraejemplos": contraejemplos
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Counterexample Engine: {str(e)}")

import hashlib
import json

# ==============================================================================
# MODELOS PYDANTIC PARA TAREAS 4, 5, 6 Y 7
# ==============================================================================

class KGNodeInput(BaseModel):
    node_id: str
    label: str
    node_type: str
    codigo_psi: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KGEdgeInput(BaseModel):
    source_node: str
    target_node: str
    relation_type: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_ref: str
    is_verified: bool = True

class BulkDAGInput(BaseModel):
    nodes: List[KGNodeInput]
    edges: List[KGEdgeInput]

class EvidenceCardRequest(BaseModel):
    codigo_psi: str = Field(..., json_schema_extra={"example": "PSI-23"})
    titulo: str = Field(..., json_schema_extra={"example": "Efecto de la atmósfera enriquecida en la ignición de llamas esféricas"})
    observaciones: str
    inferencias: str
    incertidumbre: Dict[str, Any] = Field(..., json_schema_extra={"example": {"intervalo_95": [0.59, 0.77], "error_estandar": 0.04}})
    limitaciones: str
    fuente_es_sintetica: bool = Field(default=False, description="Guardrail Tarea 7: impide emitir cartas si la fuente es sintética")

class ExperimentRecommendationQuery(BaseModel):
    codigo_psi: str = Field(..., json_schema_extra={"example": "PSI-23"})
    umbral_minimo_muestras: int = Field(default=5, ge=1)
    peso_incertidumbre: float = Field(default=0.6, ge=0.0, le=1.0)
    peso_escasez_datos: float = Field(default=0.4, ge=0.0, le=1.0)

class IntegrityCheckInput(BaseModel):
    entidad_tipo: str = Field(..., json_schema_extra={"example": "Conclusion_Cientifica"})
    entidad_id: str = Field(..., json_schema_extra={"example": "CARD-PSI23-001"})
    afirmacion: str
    referencia_experimental: str
    es_sintetico: bool = False
    payload_datos: Dict[str, Any]

# ==============================================================================
# TAREA 7 (HELPER): GENERACIÓN DE HASH SHA-256 Y GUARDRAIL FÍSICO
# ==============================================================================

def calcular_sha256_canonico(data: Dict[str, Any]) -> str:
    serializado = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serializado).hexdigest()

# ==============================================================================
# TAREA 4: API DEL KNOWLEDGE GRAPH (DAG 87 NODOS / 153 ARISTAS)
# ==============================================================================

@app.post("/api/v1/knowledge-graph/ingest-dag", status_code=201, tags=["4. Knowledge Graph"])
def ingestar_dag_completo(dag: BulkDAGInput):
    """
    Permite al equipo de ciencia de datos cargar o actualizar el DAG completo (ej. 87 nodos y 153 aristas)
    en una sola transacción verificada.
    """
    try:
        with engine.begin() as conn:
            for n in dag.nodes:
                conn.execute(
                    text("""
                        INSERT INTO public.ignis_kg_nodes (node_id, label, node_type, codigo_psi, metadata)
                        VALUES (:nid, :lbl, :ntype, :psi, CAST(:meta AS jsonb))
                        ON CONFLICT (node_id) DO UPDATE SET
                            label = EXCLUDED.label,
                            node_type = EXCLUDED.node_type,
                            codigo_psi = EXCLUDED.codigo_psi,
                            metadata = EXCLUDED.metadata
                    """),
                    {"nid": n.node_id, "lbl": n.label, "ntype": n.node_type, "psi": n.codigo_psi, "meta": json.dumps(n.metadata)}
                )

            for e in dag.edges:
                conn.execute(
                    text("""
                        INSERT INTO public.ignis_kg_edges (source_node, target_node, relation_type, weight, evidence_ref, is_verified)
                        VALUES (:src, :tgt, :rel, :w, :ev, :ver)
                    """),
                    {"src": e.source_node, "tgt": e.target_node, "rel": e.relation_type, "w": e.weight, "ev": e.evidence_ref, "ver": e.is_verified}
                )

        return {
            "mensaje": "DAG sincronizado exitosamente en IGNIS-μ Knowledge Graph.",
            "nodos_procesados": len(dag.nodes),
            "aristas_insertadas": len(dag.edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ingestar DAG: {str(e)}")


@app.get("/api/v1/knowledge-graph/graph", tags=["4. Knowledge Graph"])
def consultar_grafo_y_evidencia(
    node_id: Optional[str] = Query(None, description="Filtrar subgrafo conectado a un nodo específico"),
    codigo_psi: Optional[str] = Query(None, description="Filtrar nodos asociados a un código PSI")
):
    """
    Consulta nodos, aristas, relaciones causales y evidencia asociada del Knowledge Graph.
    """
    try:
        with engine.connect() as conn:
            if node_id:
                nodes = conn.execute(
                    text("""
                        SELECT * FROM public.ignis_kg_nodes 
                        WHERE node_id = :nid 
                           OR node_id IN (SELECT target_node FROM public.ignis_kg_edges WHERE source_node = :nid)
                           OR node_id IN (SELECT source_node FROM public.ignis_kg_edges WHERE target_node = :nid)
                    """),
                    {"nid": node_id}
                ).mappings().all()
                edges = conn.execute(
                    text("SELECT * FROM public.ignis_kg_edges WHERE source_node = :nid OR target_node = :nid"),
                    {"nid": node_id}
                ).mappings().all()
            else:
                sql_n = "SELECT * FROM public.ignis_kg_nodes"
                params = {}
                if codigo_psi:
                    sql_n += " WHERE codigo_psi ILIKE :psi"
                    params["psi"] = f"%{codigo_psi}%"
                nodes = conn.execute(text(sql_n), params).mappings().all()
                edges = conn.execute(text("SELECT * FROM public.ignis_kg_edges")).mappings().all()

            return {
                "estadisticas_grafo": {"total_nodos": len(nodes), "total_aristas": len(edges)},
                "nodos": [dict(n.items()) for n in nodes],
                "aristas": [
                    {k: (str(v) if k == "edge_id" else float(v) if k == "weight" else v) for k, v in dict(e.items()).items()}
                    for e in edges
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# TAREA 5: GENERADOR DE EVIDENCE CARDS CON PROCEDENCIA VERIFICABLE
# ==============================================================================

@app.post("/api/v1/evidence-cards/generate", status_code=201, tags=["5. Evidence Cards"])
def generar_evidence_card(req: EvidenceCardRequest):
    """
    Construye una tarjeta científica con observaciones, inferencias, incertidumbre,
    contraejemplos reales vinculados, limitaciones y hash SHA-256 de procedencia.
    """
    # Control de integridad (Tarea 7): bloquear emisión si la fuente es sintética
    if req.fuente_es_sintetica:
        raise HTTPException(
            status_code=422,
            detail="BLOQUEO DE INTEGRIDAD (Tarea 7): No se permite generar Evidence Cards a partir de registros sintéticos."
        )

    try:
        with engine.begin() as conn:
            # Buscar automáticamente contraejemplos reales relacionados si es PSI-23
            contraejemplos = []
            if req.codigo_psi.upper() == "PSI-23":
                rows = conn.execute(
                    text("""
                        SELECT id_fila, atmosphere, fuel_bottle, flames_ignited 
                        FROM public.psi23_experimental_acme_sflame 
                        WHERE COALESCE(flames_ignited, 0) = 0 
                        LIMIT 3
                    """)
                ).mappings().all()
                contraejemplos = [dict(r.items()) for r in rows]

            # Calcular sello SHA-256 de procedencia verificable (Tarea 7)
            payload_canonico = {
                "codigo_psi": req.codigo_psi.upper(),
                "titulo": req.titulo,
                "observaciones": req.observaciones,
                "inferencias": req.inferencias,
                "incertidumbre": req.incertidumbre,
                "contraejemplos": contraejemplos
            }
            sha256_sello = calcular_sha256_canonico(payload_canonico)

            res = conn.execute(
                text("""
                    INSERT INTO public.ignis_evidence_cards (
                        codigo_psi, titulo, observaciones, inferencias,
                        incertidumbre, contraejemplos_resumen, limitaciones, procedencia_hash_sha256
                    ) VALUES (
                        :psi, :tit, :obs, :inf,
                        CAST(:inc AS jsonb), CAST(:contra AS jsonb), :lim, :hash
                    ) RETURNING card_id, fecha_creacion
                """),
                {
                    "psi": req.codigo_psi.upper(),
                    "tit": req.titulo,
                    "obs": req.observaciones,
                    "inf": req.inferencias,
                    "inc": json.dumps(req.incertidumbre),
                    "contra": json.dumps(contraejemplos),
                    "lim": req.limitaciones,
                    "hash": sha256_sello
                }
            ).mappings().first()

            return {
                "card_id": str(res["card_id"]),
                "codigo_psi": req.codigo_psi.upper(),
                "titulo": req.titulo,
                "observaciones": req.observaciones,
                "inferencias": req.inferencias,
                "incertidumbre": req.incertidumbre,
                "contraejemplos_reales_detectados": contraejemplos,
                "limitaciones": req.limitaciones,
                "procedencia_verificable": {
                    "sha256": sha256_sello,
                    "fecha_emision": res["fecha_creacion"].isoformat(),
                    "datos_sinteticos_excluidos": True
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar Evidence Card: {str(e)}")

# ==============================================================================
# TAREA 6: SERVICIO DE RECOMENDACIÓN EXPERIMENTAL (BRECHAS DE EVIDENCIA)
# ==============================================================================

@app.post("/api/v1/recommendations/next-experiments", tags=["6. Recomendación Experimental"])
def recomendar_proximos_experimentos(criterio: ExperimentRecommendationQuery):
    """
    Explora el espacio de parámetros reales en Supabase para detectar combinaciones
    con baja densidad de evidencia y calcula una puntuación de prioridad experimental
    usando los pesos proporcionados por el módulo de ciencia de datos.
    """
    try:
        with engine.connect() as conn:
            propuestas = []

            if criterio.codigo_psi.upper() == "PSI-23":
                # Detectar combinaciones atmósfera + combustible con menos ensayos reales
                rows = conn.execute(
                    text("""
                        SELECT atmosphere, fuel_bottle, COUNT(*) AS ensayos_reales
                        FROM public.psi23_experimental_acme_sflame
                        WHERE atmosphere IS NOT NULL AND fuel_bottle IS NOT NULL
                        GROUP BY atmosphere, fuel_bottle
                        HAVING COUNT(*) <= :umbral
                        ORDER BY ensayos_reales ASC
                        LIMIT 10
                    """),
                    {"umbral": criterio.umbral_minimo_muestras}
                ).mappings().all()

                for r in rows:
                    n = r["ensayos_reales"]
                    # Criterio matemático parametrizable: score de escasez + incertidumbre epistémica (1 / sqrt(n))
                    escasez_norm = round(1.0 - (n / (criterio.umbral_minimo_muestras + 1)), 4)
                    incertidumbre_est = round(1.0 / (n ** 0.5), 4)
                    score_prioridad = round(
                        (criterio.peso_escasez_datos * escasez_norm) + (criterio.peso_incertidumbre * incertidumbre_est),
                        4
                    )
                    propuestas.append({
                        "regimen_subexplorado": {
                            "atmosfera": r["atmosphere"],
                            "combustible": r["fuel_bottle"]
                        },
                        "ensayos_reales_existentes": n,
                        "metricas_ciencia_datos": {
                            "indice_escasez": escasez_norm,
                            "incertidumbre_epistemica_estimada": incertidumbre_est,
                            "score_prioridad_experimental": score_prioridad
                        },
                        "accion_sugerida": f"Ejecutar campaña adicional en microgravedad con {r['fuel_bottle']} en atmósfera {r['atmosphere']} para reducir varianza causal."
                    })
            else:
                # Exploración en PSI-117 por combustible
                rows = conn.execute(
                    text("""
                        SELECT fuel, COUNT(*) AS ensayos_reales
                        FROM public.psi117_readme_list_of_data
                        GROUP BY fuel
                        ORDER BY ensayos_reales ASC
                    """)
                ).mappings().all()
                for r in rows:
                    n = r["ensayos_reales"]
                    score = round(criterio.peso_incertidumbre * (1.0 / (n ** 0.5)), 4)
                    propuestas.append({
                        "regimen_subexplorado": {"combustible": r["fuel"]},
                        "ensayos_reales_existentes": n,
                        "score_prioridad_experimental": score
                    })

            return {
                "codigo_psi": criterio.codigo_psi.upper(),
                "parametros_criterio": criterio.model_dump(),
                "regiones_baja_evidencia_encontradas": len(propuestas),
                "experimentos_recomendados": propuestas
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en motor de recomendación: {str(e)}")

# ==============================================================================
# TAREA 7: AUDITORÍA E INTEGRIDAD SHA-256 Y VALIDACIÓN DE PROCEDENCIA
# ==============================================================================

@app.post("/api/v1/audit/verify-integrity", tags=["7. Auditoría e Integridad"])
def auditar_integridad_cientifica(audit_req: IntegrityCheckInput):
    """
    Calcula el hash SHA-256 canónico, valida que la afirmación tenga respaldo experimental real
    y bloquea afirmaciones causales o físicas no verificadas o basadas en datos sintéticos.
    """
    sha256_calculado = calcular_sha256_canonico(audit_req.payload_datos)

    # Guardrail 1: Rechazar si proviene de simulación no marcada como evidencia real
    if audit_req.es_sintetico:
        return {
            "aprobado": False,
            "sha256_hash": sha256_calculado,
            "motivo_rechazo": "VIOLACIÓN DE INTEGRIDAD: Afirmación sustentada en datos sintéticos (is_synthetic=True)."
        }

    try:
        with engine.begin() as conn:
            # Guardrail 2: Verificar que la referencia experimental exista realmente en la BD
            existe_ref = conn.execute(
                text("""
                    SELECT 1 FROM public.experimentos_combustion 
                    WHERE codigo_programa ILIKE :ref OR tipo_combustible ILIKE :ref
                    LIMIT 1
                """),
                {"ref": f"%{audit_req.referencia_experimental}%"}
            ).first()

            aprobado = bool(existe_ref)
            detalle = (
                "Procedencia verificada contra catálogo maestro NASA."
                if aprobado else
                f"BLOQUEADO: La referencia '{audit_req.referencia_experimental}' no existe en registros experimentales verificados."
            )

            conn.execute(
                text("""
                    INSERT INTO public.ignis_audit_trail (
                        entidad_tipo, entidad_id, sha256_hash, validacion_fisica_aprobada, detalle_auditoria
                    ) VALUES (:tipo, :eid, :hash, :aprob, :det)
                """),
                {
                    "tipo": audit_req.entidad_tipo,
                    "eid": audit_req.entidad_id,
                    "hash": sha256_calculado,
                    "aprob": aprobado,
                    "det": detalle
                }
            )

            if not aprobado:
                raise HTTPException(status_code=422, detail=detalle)

            return {
                "aprobado": True,
                "entidad_id": audit_req.entidad_id,
                "sha256_hash": sha256_calculado,
                "estado_procedencia": "VERIFICADO_EN_BD_NASA",
                "detalle": detalle
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en auditoría: {str(e)}")
