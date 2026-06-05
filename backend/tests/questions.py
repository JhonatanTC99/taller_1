"""
questions.py

Módulo de evaluación y validación del agente conversacional Dollarcity AI.

Este archivo ejecuta pruebas automatizadas sobre los principales componentes de la arquitectura del agente:

1. RAG (Retrieval-Augmented Generation)
    - Valida consultas respondidas desde la base vectorial ChromaDB.

2. Memory Engine
    - Verifica la persistencia y recuperación del historial conversacional.

3. Structured Tool
    - Evalúa respuestas exactas provenientes del JSON corporativo.

4. Routing Engine
    - Comprueba que el router híbrido seleccione correctamente
        la herramienta adecuada según la intención del usuario.

Resultados:
- Genera un archivo CSV con métricas de latencia,
    herramienta utilizada, tipo de fuente y respuesta generada.

Ejecución:
    python questions.py

Salida:
    data/evaluation_results.csv
"""
import argparse
import pandas as pd
from datetime import datetime
from src.engine.agent_service import get_agent_service
import time

TEST_QUESTIONS = [

    # =====================================================
    # 1. PRUEBAS RAG
    # =====================================================

    {
        "test_type": "RAG",
        "description": "Consulta corporativa respondida desde documentos vectoriales",
        "conversation_id": "rag_01",
        "step": 1,
        "question": "¿Cuál es la misión de Dollarcity?"
    },

    {
        "test_type": "RAG",
        "description": "Consulta histórica empresarial usando conocimiento documental",
        "conversation_id": "rag_02",
        "step": 1,
        "question": "¿Desde qué año opera Dollarcity y cuál es su visión de crecimiento?"
    },

    {
        "test_type": "RAG",
        "description": "Consulta sobre políticas y servicios",
        "conversation_id": "rag_03",
        "step": 1,
        "question": "¿Puedo comprar productos por internet o pedir domicilio?"
    },

    {
        "test_type": "RAG",
        "description": "Consulta sobre disponibilidad e inventario",
        "conversation_id": "rag_04",
        "step": 1,
        "question": "¿Cómo puedo consultar disponibilidad de productos?"
    },

    # =====================================================
    # 2. PRUEBAS DE MEMORIA
    # =====================================================

    {
        "test_type": "MEMORY",
        "description": "El agente debe recordar el nombre del usuario",
        "conversation_id": "memory_01",
        "step": 1,
        "question": "Mi nombre es Erica"
    },

    {
        "test_type": "MEMORY",
        "description": "Pregunta dependiente del historial",
        "conversation_id": "memory_01",
        "step": 2,
        "question": "¿Cómo me llamo?"
    },

    {
        "test_type": "MEMORY",
        "description": "Validar recuperación de historial reciente",
        "conversation_id": "memory_02",
        "step": 1,
        "question": "Recuerda que soy cliente frecuente"
    },

    {
        "test_type": "MEMORY",
        "description": "Seguimiento contextual",
        "conversation_id": "memory_02",
        "step": 2,
        "question": "¿Qué te dije anteriormente?"
    },

    # =====================================================
    # 3. PRUEBAS DE HERRAMIENTA ESTRUCTURADA
    # =====================================================

    {
        "test_type": "STRUCTURED_TOOL",
        "description": "Consulta exacta de horario",
        "conversation_id": "tool_01",
        "step": 1,
        "question": "¿Cuál es el horario?"
    },

    {
        "test_type": "STRUCTURED_TOOL",
        "description": "Consulta de NIT corporativo",
        "conversation_id": "tool_02",
        "step": 1,
        "question": "¿Cuál es el NIT de Dollarcity?"
    },

    {
        "test_type": "STRUCTURED_TOOL",
        "description": "Consulta de canales de empleo",
        "conversation_id": "tool_03",
        "step": 1,
        "question": "¿Cómo puedo aplicar a una vacante?"
    },

    {
        "test_type": "STRUCTURED_TOOL",
        "description": "Consulta de facturación",
        "conversation_id": "tool_04",
        "step": 1,
        "question": "¿Cómo obtengo mi factura electrónica?"
    },

    # =====================================================
    # 4. PRUEBAS DE ENRUTAMIENTO
    # =====================================================

    {
        "test_type": "ROUTING",
        "description": "El router debe seleccionar herramienta estructurada",
        "conversation_id": "routing_01",
        "step": 1,
        "question": "¿Cuál es el horario?"
    },

    {
        "test_type": "ROUTING",
        "description": "El router debe activar memoria",
        "conversation_id": "routing_01",
        "step": 2,
        "question": "Mi nombre es Erica"
    },

    {
        "test_type": "ROUTING",
        "description": "El router debe consultar memoria",
        "conversation_id": "routing_01",
        "step": 3,
        "question": "¿Cómo me llamo?"
    },

    {
        "test_type": "ROUTING",
        "description": "El router debe usar RAG",
        "conversation_id": "routing_01",
        "step": 4,
        "question": "¿Cuál es la misión de Dollarcity?"
    },

    {
        "test_type": "ROUTING",
        "description": "El router debe bloquear preguntas fuera de dominio",
        "conversation_id": "routing_01",
        "step": 5,
        "question": "¿Quién es el presidente de Colombia?"
    }
]

def run_evaluation(limit: int = None):

    print("\n[EVALUACIÓN] Validación oficial del agente IA")

    output_path = "data/evaluation_results.csv"

    results = []

    # Instanciación única del servicio del agente V3 (Patrón Singleton)
    agent = get_agent_service()

    questions_to_run = TEST_QUESTIONS[:limit] if limit else TEST_QUESTIONS

    for i, item in enumerate(questions_to_run):

        conversation_id = item["conversation_id"]

        print(f"\n[{i+1}/{len(questions_to_run)}]")
        print(f"Tipo : {item['test_type']}")
        print(f"Step : {item['step']}")
        print(f"Q    : {item['question']}")

        start_time = datetime.now()

        try:
            # Invocación al nuevo motor de AgentService usando conversation_id como user_id (thread_id)
            response = agent.invoke(user_id=conversation_id, message=item['question'], channel="test_script")
            time.sleep(5)  # Espera 5 segundos antes de procesar lo que sigue

            # Captura de latencia nativa desde los metadatos devueltos por el agente nuevo
            latency = response.get("timing_ms", {}).get("total", 0) / 1000.0

            result = {
                "ID": i + 1,
                "Test_Type": item["test_type"],
                "Description": item["description"],
                "Conversation_ID": conversation_id,
                "Step": item["step"],
                "Question": item["question"],
                "Tool_Used": response.get("tool_used"),
                "Source_Type": response.get("source_type"),
                "Docs_Count": response.get("docs_count"),
                "Model": response.get("model"),
                "Response": response.get("content"),
                "Latency_Sec": round(latency, 2),
                "Status": response.get("status")
            }

        except Exception as e:
            # Cálculo nativo de respaldo en caso de que ocurra algún fallo
            latency = (
                datetime.now() - start_time
            ).total_seconds()

            result = {
                "ID": i + 1,
                "Test_Type": item["test_type"],
                "Description": item["description"],
                "Conversation_ID": conversation_id,
                "Step": item["step"],
                "Question": item["question"],
                "Tool_Used": "ERROR",
                "Source_Type": "ERROR",
                "Docs_Count": 0,
                "Model": "unknown",
                "Response": str(e),
                "Latency_Sec": round(latency, 2),
                "Status": "ERROR"
            }

        results.append(result)

        # Lógica de pandas intacta para la preservación de la estructura del CSV
        pd.DataFrame(results).to_csv(
            output_path,
            index=False,
            encoding='utf-8'
        )

    print(f"\n[INFO] Resultados guardados en: {output_path}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Evaluación del agente Dollarcity AI"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Número de pruebas a ejecutar"
    )

    args = parser.parse_args()

    run_evaluation(limit=args.limit)