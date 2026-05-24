"""
Módulo de servicio de orquestación agéntica avanzada para Dollarcity.

Este componente define la capa central de control agéntico del Módulo 3. Utiliza las
abstracciones modernas de LangChain (`init_chat_model` y `create_agent`) para construir
un orquestador conversacional reactivo basado en Function Calling estricto. El servicio
está diseñado para consumir prompts de configuración dinámicos y catálogos de herramientas
tipadas con Pydantic, garantizando un puente de ejecución unificado optimizado para canales
de mensajería empresariales (N8N, WhatsApp, Telegram). Integra la capa de persistencia 
relacional con PostgreSQL mediante PostgresSaver para gobernar la persistencia de estados por hilos.

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A (FastAPI + LangChain Backend Service Graph Orchestration)
"""

import time
import json
import traceback
from typing import Any

# Abstracciones modernas de inicialización y orquestación de LangChain
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

# Capa de persistencia avanzada para hilos y checkpoints de LangGraph
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# Componentes de motor, herramientas y prompts del proyecto
from src.engine.tools import get_agent_tools
from src.engine.agent_prompts import build_dynamic_prompt, AGENT_SYSTEM_PROMPT

# Configuración centralizada de variables de entorno v3
from src.config.settings import (
    AGENT_PROVIDER,
    AGENT_MODEL,
    AGENT_TEMPERATURE,
    AGENT_MAX_RETRIES,
    ENABLE_HITL,
    DATABASE_URL,
    CHECKPOINT_TABLE_PREFIX
)

# Variable global privada encargada de retener la instancia única del Singleton
_agent_service = None


class AgentService:
    """
    Clase de servicio empresarial encargada de gobernar el ciclo de vida del agente,
    la configuración del LLM subyacente y la ejecución de pipelines conversacionales.
    """

    def __init__(self) -> None:
        """
        Unifica las propiedades del servicio agéntico, compila el set de herramientas
        estructuradas, inicializa el checkpointer relacional PostgreSQL e instanciar 
        el motor cognitivo a través del factory de LangChain.
        """
        self.model_name = AGENT_MODEL
        self.provider = AGENT_PROVIDER
        self.tools = get_agent_tools()
        
        # Infraestructura de persistencia transaccional (Checkpointer de Estado)
        self.pool = None
        self.checkpointer = self._build_checkpointer()
        
        # Configuración del middleware de intervención humana
        self.middleware = self._build_middleware()
        
        # Construcción segura e incremental de los componentes del core agéntico
        self.llm = self._build_llm()
        self.agent = self._build_agent()
        
        # Registro mínimo de metadatos operativos para trazabilidad técnica
        self._meta = {
            "initialized_at": time.time(),
            "tools_count": len(self.tools),
            "hitl_enabled": ENABLE_HITL,
            "checkpointer_type": "PostgresSaver"
        }

    def _build_checkpointer(self) -> PostgresSaver:
        """
        Inicializa el ConnectionPool y configura el PostgresSaver para LangGraph.
        Asegura la creación automática de esquemas y tablas necesarias en la base de datos.

        Returns:
            PostgresSaver: Gestor de checkpoints de estado persistente listo para el grafo.

        Raises:
            RuntimeError: Ante fallos infraestructurales críticos en la conexión hacia PostgreSQL.
        """
        try:
            # Construcción del pool de conexiones compartidas con directivas de confirmación automática
            self.pool = ConnectionPool(
                conninfo=DATABASE_URL,
                kwargs={
                    "autocommit": True, 
                    "prepare_threshold": 0
                }
            )
            
            # Instanciación del checkpointer empresarial con prefijo de tabla corporativo
            checkpointer = PostgresSaver(self.pool)
            
            # Creación o verificación de tablas relacionales requeridas por LangGraph
            checkpointer.setup()
            return checkpointer
            
        except Exception as e:
            raise RuntimeError(
                f"Fallo crítico de infraestructura al inicializar la persistencia PostgresSaver: {str(e)}"
            )

    def _build_middleware(self) -> list[Any]:
        """
        Configura el middleware de intervención humana para herramientas sensibles.
        La activación depende de ENABLE_HITL para permitir pruebas controladas sin
        afectar el flujo operativo normal del agente.
        """
        if not ENABLE_HITL:
            return []

        return [
            HumanInTheLoopMiddleware(
                interrupt_on={"registrar_lead_interesado": True},
                description_prefix="La ejecución de esta herramienta requiere aprobación humana"
            )
        ]

    def _build_llm(self) -> Any:
        """
        Inicializa el modelo de lenguaje (LLM) de forma transparente y unificada.
        Aplica mapeos de proveedores y maneja fallbacks estructurados ante incompatibilidades de firmas.

        Returns:
            Any: Instancia de un ChatModel de LangChain configurada para Function Calling.
        """
        # Matriz unificada de homonimia para el parámetro 'model_provider' de LangChain
        provider_map = {
            "google": "google_genai",
            "ollama": "ollama"
        }
        mapped_provider = provider_map.get(self.provider, self.provider)

        try:
            # Intento Primario: Inicialización con proveedor explícito normalizado
            return init_chat_model(
                self.model_name,
                model_provider=mapped_provider,
                temperature=AGENT_TEMPERATURE
            )
        except Exception:
            try:
                # Fallback Secundario: Deducción automática del proveedor omitiendo la llave explícita
                return init_chat_model(
                    self.model_name,
                    temperature=AGENT_TEMPERATURE
                )
            except Exception:
                # Fallback Terciario: Inicialización cruda para contingencia de entornos académicos locales
                return init_chat_model(self.model_name)

    def _build_agent(self) -> Any:
        """
        Orquesta e integra la estructura del agente utilizando la abstracción create_agent.
        Inyecta la capa de persistencia PostgresSaver para soportar almacenamiento distribuido.

        Returns:
            Any: Estructura ejecutable del agente vinculada a sus herramientas, prompt y checkpointer.
        """
        try:
            # Compilación estática del prompt con variables contextuales mandatorias por defecto
            compiled_prompt = build_dynamic_prompt({
                "channel": "web",
                "enable_hitl": ENABLE_HITL
            })
            
            return create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=compiled_prompt,
                middleware=self.middleware,
                checkpointer=self.checkpointer
            )
        except Exception:
            # Fallback de mitigación terminal consumiendo la directriz base inmutable con persistencia activa
            return create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=AGENT_SYSTEM_PROMPT,
                middleware=self.middleware,
                checkpointer=self.checkpointer
            )

    def get_model_name(self) -> str:
        """
        Expone el identificador técnico del modelo de lenguaje configurado activamente.

        Returns:
            str: Nombre o ruta de nomenclatura del modelo de inferencia.
        """
        return self.model_name

    def _normalize_content_block(self, content: Any) -> str:
        """
        Desestructura y normaliza bloques de contenido multimodales o complejos devueltos por el LLM.
        Extrae exclusivamente las cadenas de texto legibles, omitiendo envolturas sintácticas de diccionarios,
        listas de partes, o metadatos internos del proveedor (como 'extras', 'signature', 'type').

        Args:
            content (Any): Objeto de contenido crudo o estructurado procedente del ciclo del agente.

        Returns:
            str: Cadena textual saneada y libre de marcas estructurales internas.
        """
        if content is None:
            return ""
            
        if isinstance(content, str):
            return content.strip()
            
        if isinstance(content, dict):
            if "text" in content:
                return str(content["text"]).strip()
            return str(content).strip()
            
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        parts.append(str(item["text"]))
                elif hasattr(item, "text"):
                    parts.append(str(item.text))
            return "".join(parts).strip()
            
        if hasattr(content, "text"):
            return str(content.text).strip()
            
        return str(content).strip()

    def _extract_final_content(self, agent_result: Any) -> str:
        """
        Normaliza las diversas variantes estructurales de respuesta devueltas por los runnables de LangChain.
        Inspecciona secuencialmente de forma reversa el historial de mensajes para extraer el último output textual válido.

        Args:
            agent_result (Any): Payload de salida crudo emitido por el agente.

        Returns:
            str: Cadena de texto limpia y formateada apta para consumo del canal.
        """
        if not agent_result:
            return ""
            
        if isinstance(agent_result, str):
            return self._normalize_content_block(agent_result)
            
        if isinstance(agent_result, dict):
            if "output" in agent_result:
                return self._normalize_content_block(agent_result["output"])
            if "content" in agent_result:
                return self._normalize_content_block(agent_result["content"])
            if "messages" in agent_result:
                messages_list = agent_result["messages"]
                
                # Búsqueda reversa orientada a omitir mensajes de herramientas y capturar la respuesta final al usuario
                for msg in reversed(messages_list):
                    content_val = None
                    if hasattr(msg, "content"):
                        content_val = msg.content
                    elif isinstance(msg, dict) and "content" in msg:
                        content_val = msg["content"]
                    
                    cleaned_content = self._normalize_content_block(content_val) if content_val is not None else ""
                    if cleaned_content:
                        is_tool = False
                        if hasattr(msg, "type") and msg.type in ("tool", "function"):
                            is_tool = True
                        if isinstance(msg, dict) and msg.get("role") in ("tool", "function", "tool_message"):
                            is_tool = True
                        
                        if not is_tool:
                            return cleaned_content

                # Fallback distributivo directo si no se resolvió texto en la búsqueda reversa filtrada
                if messages_list:
                    last_msg = messages_list[-1]
                    if hasattr(last_msg, "content"):
                        return self._normalize_content_block(last_msg.content)
                    if isinstance(last_msg, dict) and "content" in last_msg:
                        return self._normalize_content_block(last_msg["content"])
                    return self._normalize_content_block(last_msg)
                    
        if hasattr(agent_result, "content"):
            return self._normalize_content_block(agent_result.content)
            
        return self._normalize_content_block(agent_result)

    def _extract_tool_metadata(self, agent_result: Any) -> dict[str, Any]:
        """
        Inspecciona retrospectivamente los pasos de ejecución y mensajería intermedia del agente
        para auditar la invocación de herramientas corporativas y volumetría de ChromaDB.

        Args:
            agent_result (Any): Estado o payload del objeto resultante de la invocación.

        Returns:
            dict: Estructura estandarizada conteniendo la traza del set de herramientas.
        """
        metadata = {
            "tool_used": "agent",
            "source_type": "agent",
            "docs_count": None
        }
        
        try:
            if isinstance(agent_result, dict):
                # Caso A: Inspección de estructuras tradicionales basadas en intermediate_steps de LangChain
                if "intermediate_steps" in agent_result:
                    steps = agent_result["intermediate_steps"]
                    if steps:
                        last_action, last_output = steps[-1]
                        if hasattr(last_action, "tool"):
                            metadata["tool_used"] = str(last_action.tool)
                        
                        if isinstance(last_output, dict):
                            metadata["source_type"] = last_output.get("source_type", "agent")
                            metadata["docs_count"] = last_output.get("docs_count")
                            if "tool_used" in last_output:
                                metadata["tool_used"] = last_output["tool_used"]
                        elif isinstance(last_output, str) and "Error" in last_output:
                            metadata["source_type"] = "error"
                        return metadata

                # Caso B: Inspección de flujos basados en listas de mensajes (LangGraph / State Message State)
                if "messages" in agent_result:
                    messages_list = agent_result["messages"]
                    for msg in reversed(messages_list):
                        if hasattr(msg, "type") and msg.type == "tool":
                            metadata["tool_used"] = getattr(msg, "name", "tool")
                            if hasattr(msg, "artifact") and isinstance(msg.artifact, dict):
                                metadata["source_type"] = msg.artifact.get("source_type", "agent")
                                metadata["docs_count"] = msg.artifact.get("docs_count")
                            elif hasattr(msg, "content") and isinstance(msg.content, str):
                                try:
                                    content_dict = json.loads(msg.content)
                                    if isinstance(content_dict, dict):
                                        metadata["source_type"] = content_dict.get("source_type", "agent")
                                        metadata["docs_count"] = content_dict.get("docs_count")
                                except Exception:
                                    pass
                            break
                        if isinstance(msg, dict) and msg.get("role") == "tool":
                            metadata["tool_used"] = msg.get("name", "tool")
                            break
        except Exception:
            pass
            
        return metadata

    def _detect_interrupt(self, agent_result: Any) -> dict[str, Any] | None:
        """
        Detecta si la ejecución del grafo fue pausada por HumanInTheLoopMiddleware.
        """
        if isinstance(agent_result, dict) and "__interrupt__" in agent_result:
            return {
                "interrupted": True,
                "interrupt": agent_result["__interrupt__"]
            }
        return None

    def invoke(self, user_id: str, message: str, channel: str = "web", metadata: dict | None = None) -> dict[str, Any]:
        """
        Punto de entrada operativo unificado para procesar peticiones conversacionales omnicanal.
        Estructura el mapa de configuraciones persistentes, mitiga excepciones e instrumenta telemetría.

        Args:
            user_id (str): Identificador unificado de la sesión remota o cliente celular.
            message (str): Entrada textual limpia enviada por el webhook.
            channel (str): Identificador sintáctico de la interfaz originaria (whatsapp, telegram, web).
            metadata (dict | None): Carga útil abierta de metadatos exógenos de canalización.

        Returns:
            dict: Objeto corporativo unificado de respuesta alineado con los contratos v3.
        """
        start_time = time.perf_counter()
        
        # Estructuración del mapa conceptual de ejecución de LangChain/LangGraph con thread_id persistente
        config = {
            "configurable": {
                "thread_id": user_id,
                "user_id": user_id,
                "channel": channel,
                "enable_hitl": ENABLE_HITL
            }
        }

        try:
            # Formateo estricto del payload de entrada como lista de mensajes para prevenir ValueError de contenido
            agent_input = {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
            
            raw_result = self.agent.invoke(agent_input, config=config)
            
            # Verificación de interrupción por HITL
            interrupt_payload = self._detect_interrupt(raw_result)
            if interrupt_payload:
                execution_latency = (time.perf_counter() - start_time) * 1000.0
                return {
                    "content": (
                        "La solicitud requiere revisión humana antes de continuar. "
                        "Un administrador debe aprobar, editar o rechazar la acción propuesta."
                    ),
                    "status": "pending_human_review",
                    "model": self.get_model_name(),
                    "tool_used": "registrar_lead_interesado",
                    "source_type": "human_in_the_loop",
                    "docs_count": None,
                    "timing_ms": {"total": round(execution_latency, 2)},
                    "metadata": {
                        "channel_received": channel,
                        "session_thread": user_id,
                        "input_metadata_forwarded": metadata,
                        "checkpointer": "PostgresSaver",
                        "thread_id": user_id,
                        "hitl_enabled": ENABLE_HITL,
                        "interrupt": str(interrupt_payload.get("interrupt"))
                    }
                }

            # Desglose e instrumentación analítica de la ejecución
            content = self._extract_final_content(raw_result)
            tool_meta = self._extract_tool_metadata(raw_result)
            execution_latency = (time.perf_counter() - start_time) * 1000.0

            return {
                "content": content,
                "status": "success",
                "model": self.get_model_name(),
                "tool_used": tool_meta["tool_used"],
                "source_type": tool_meta["source_type"],
                "docs_count": tool_meta["docs_count"],
                "timing_ms": {"total": round(execution_latency, 2)},
                "metadata": {
                    "channel_received": channel,
                    "session_thread": user_id,
                    "input_metadata_forwarded": metadata,
                    "checkpointer": "PostgresSaver",
                    "thread_id": user_id,
                    "hitl_enabled": ENABLE_HITL
                }
            }

        except Exception as e:
            execution_latency = (time.perf_counter() - start_time) * 1000.0
            return {
                "content": (
                    "Lo sentimos, experimentamos una anomalía imprevista en el procesamiento interno "
                    "de tu solicitud corporativa. Por favor, reintenta en unos instantes."
                ),
                "status": "error",
                "model": self.get_model_name(),
                "tool_used": "error_handler",
                "source_type": "error",
                "docs_count": None,
                "timing_ms": {"total": round(execution_latency, 2)},
                "metadata": {
                    "exception_summary": str(e),
                    "stack_trace": traceback.format_exc()
                }
            }

    def diagnostics(self) -> dict[str, Any]:
        """
        Compila e instrumenta métricas volumétricas y de salud sobre los motores agénticos
        y la capa activa de checkpoints relacionales en PostgreSQL.

        Returns:
            dict: Objeto de diagnóstico con el estado de conectividad e infraestructura.
        """
        return {
            "model": self.model_name,
            "provider": self.provider,
            "tools_count": len(self.tools),
            "checkpointer": "PostgresSaver",
            "database_url_configured": bool(DATABASE_URL),
            "checkpoint_table_prefix": CHECKPOINT_TABLE_PREFIX,
            "hitl_enabled": ENABLE_HITL,
            "middleware_count": len(self.middleware),
            "hitl_interrupted_tools": ["registrar_lead_interesado"] if ENABLE_HITL else []
        }

    def close(self) -> None:
        """
        Libera de manera ordenada los recursos físicos de red y cierra el pool de conexiones.
        """
        if self.pool:
            try:
                self.pool.close()
            except Exception:
                pass


# =====================================================================
# SECCIÓN III: INTERFAZ SINGLETON DE CONVENIENCIA OPERACIONAL
# =====================================================================

def get_agent_service() -> AgentService:
    """
    Fábrica constructora bajo el patrón de diseño Singleton.
    Garantiza una única inicialización del grafo agéntico y de la persistencia de estados
    PostgresSaver en el ciclo de vida operativa del backend API REST.

    Returns:
        AgentService: Instancia global compartida del orquestador agéntico.
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


# Definición explícita de símbolos exportables del módulo
__all__ = [
    "AgentService",
    "get_agent_service"
]

# Bloque de ejecución e instrumentación remota para diagnóstico en consola local
if __name__ == "__main__":
    print("=====================================================================")
    print(" DIAGNÓSTICO EN CONSOLA AISLADA - AGENT_SERVICE CON POSTGRESSAVER")
    print("=====================================================================")
    service = get_agent_service()
    print("[DIAGNOSTICS]:", service.diagnostics())
    print("---------------------------------------------------------------------")
    test_response = service.invoke(
        user_id="local_isolated_test_run",
        channel="api",
        message="¿Cuál es el horario de Dollarcity?"
    )
    print("[TEST INVOCATION RESULT]:")
    print(test_response)
    print("=====================================================================")
    service.close()