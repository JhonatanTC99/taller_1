import argparse
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ingestión, procesamiento y lógica del motor síncrono preexistente
from src.scraper.collector import run_scraper
from src.processor.cleaner import build_dynamic_kb as run_semantic_curation
from src.engine.llm_service import LLMService, start_console_chat

# Orquestador agéntico avanzado del Módulo 3
from src.engine.agent_service import get_agent_service

# Contratos unificados de entrada/salida para producción (Módulo 3)
from src.schemas.chat import (
    ChannelChatRequest,
    ChannelChatResponse,
    LegacyChatRequest
)

# Conmutadores de arquitectura empresariales (Feature Flags)
from src.config.settings import (
    ENABLE_AGENT_V3,
    ENABLE_CONVERSATION_LOGGING,
    ENABLE_HITL
)

# --- CONFIGURACIÓN DE COLORES ANSI PARA OBSERVABILIDAD EN CONSOLA ---
ANSI_CYAN = "\033[96m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


# --- CONFIGURACIÓN DE LA APP ---
app = FastAPI(title="Dollarcity AI API - Taller 2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LAZY INITIALIZATION ---
_service = None

def get_service() -> LLMService:
    """
    Implementación de Singleton con Lazy Loading para el servicio síncrono.
    Evita inicializar ChromaDB durante la ejecución de comandos CLI de limpieza.
    """
    global _service
    if _service is None:
        _service = LLMService()
    return _service


# --- ENDPOINTS ---

@app.get("/")
def home():
    """Devuelve el estado operativo básico del API de backend e indica el estado del contrato."""
    return {"status": "Backend Dollarcity Online", "version": "3.0-channel-contract"}


@app.get("/debug")
def debug():
    """Valida el estado de la inicialización, modelo activo y estado de las variables de entorno v3."""
    service = get_service()
    return {
        "msg": "ESTOY EN MAIN.PY",
        "model": service.get_model_name(),
        "session_id": service.session_id,
        "enable_agent_v3": ENABLE_AGENT_V3,
        "enable_conversation_logging": ENABLE_CONVERSATION_LOGGING,
        "enable_hitl": ENABLE_HITL,
        "channel_endpoint_mode": "agent_v3" if ENABLE_AGENT_V3 else "legacy_bridge"
    }


@app.get("/api/llm-health")
def llm_health():
    """Verifica si la API de Google responde."""
    service = get_service()
    return service.test_llm_connection()


@app.get("/api/rag-diagnostics")
def rag_diagnostics():
    """Analiza la salud de la Vector DB (Chroma) y Contexto."""
    service = get_service()
    return service.get_rag_diagnostics()


@app.get("/api/summary")
def get_summary():
    """Recupera la síntesis corporativa de conocimiento pre-calculada."""
    service = get_service()
    return service.get_summary() 


@app.get("/api/faq")
def get_faq():
    """Recupera el listado estructurado de preguntas frecuentes."""
    service = get_service()
    return service.get_faq()


@app.post("/api/chat")
def chat(query: LegacyChatRequest):
    """
    Endpoint síncrono heredado del Módulo 2.
    Mantiene compatibilidad retrospectiva directa con el frontend de validación local.
    """
    try:
        service = get_service()
        q = query.question.lower().strip()

        # Validar y aplicar cambio de modelo si es válido
        if query.model:
            service.set_model(query.model)

        if q == "identity_check":
            return {"content": "ok", "model": service.get_model_name()}

        # Reglas básicas de negocio (Rule Engine previo al LLM)
        greetings = ["hola", "buenas", "hey", "hello"]
        if q in greetings:
            return {
                "content": "¡Hola! Somos Dollarcity Colombia. ¿En qué podemos ayudarte?",
                "model": service.get_model_name(),
                "tool_used": "rule_engine",
                "source_type": "rule",
                "status": "success"
            }

        if q.isdigit():
            return {
                "content": "Lo sentimos, no contamos con esa información específica. ¿Podrías darnos más detalle?",
                "model": service.get_model_name(),
                "tool_used": "rule_engine",
                "source_type": "rule",
                "status": "success"
            }

        return service.get_chat_response(query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/channel/chat", response_model=ChannelChatResponse)
def channel_chat(query: ChannelChatRequest):
    """
    Endpoint adaptativo de producción para orquestación multiproveedor (Módulo 3).

    Funciona bajo un mecanismo de conmutación de características (Feature Flag Routing). 
    Si ENABLE_AGENT_V3 es activo, despacha la solicitud directamente al motor agéntico 
    de LangChain/LangGraph (AgentService), preservando la traza intermedia y los metadatos. 
    Si es inactivo, conmuta de forma segura al puente adaptativo lineal síncrono preexistente 
    (LLMService) sin interrumpir los flujos webhooks externos de N8N, WhatsApp o Telegram.
    """
    try:
        # [Punto de Entrada]: Logging visual al recibir una petición externa
        print(f"\n{ANSI_CYAN}{ANSI_BOLD}[⚡ NUEVA PETICIÓN] Canal: {query.channel} | Usuario: {query.user_id} | Mensaje: \"{query.message}\"{ANSI_RESET}")

        if ENABLE_AGENT_V3:
            # [Indicador de Motor]: Agente V3 activo
            print(f"{ANSI_YELLOW}[⚙️ MOTOR]: Enrutando al Agente V3 (LangGraph)....{ANSI_RESET}")

            # Enrutamiento hacia la infraestructura agéntica avanzada del Módulo 3
            result = get_agent_service().invoke(
                user_id=query.user_id,
                message=query.message,
                channel=query.channel,
                metadata=query.metadata
            )
            
            # Recuperación estructurada para no destruir la telemetría generada en la tool o agente
            meta_dict = result.get("metadata", {})
            if not isinstance(meta_dict, dict):
                meta_dict = {"raw_agent_metadata": meta_dict}
            
            meta_dict["agent_v3"] = True
            meta_dict["legacy_bridge"] = False
            
        else:
            # [Indicador de Motor]: Flujo Legacy activo
            print(f"{ANSI_YELLOW}[⚙️ MOTOR]: Enrutando al Legacy Bridge....{ANSI_RESET}")

            # Enrutamiento retrospectivo hacia el motor síncrono del Módulo 2 (Legacy Bridge)
            service = get_service()
            if query.model:
                service.set_model(query.model)
                
            result = service.get_chat_response(query.message)
            
            # Compilación estructural de metadatos del adaptador temporal
            meta_dict = {
                "agent_v3": False,
                "legacy_bridge": True,
                "input_metadata": query.metadata
            }
        
        # Extracción y preparación de variables para el Punto de Salida
        tool = result.get("tool_used") or result.get("source_type") or "N/A"
        status = result.get("status", "success")
        raw_content = result.get("content", "")
        content_snippet = raw_content[:80] + "..." if len(raw_content) > 80 else raw_content

        # [Punto de Salida]: Impresión del resumen estructurado con colores antes del retorno
        print(f"{ANSI_GREEN}{ANSI_BOLD}[✅ RESPUESTA] Tool: {tool} | Status: {status} | 💬 \"{content_snippet}\"{ANSI_RESET}\n")

        # Mapeo y conformación estricta al esquema corporativo de salida v3
        return ChannelChatResponse(
            content=raw_content,
            status=status,
            model=result.get("model") or (get_agent_service().get_model_name() if ENABLE_AGENT_V3 else get_service().get_model_name()),
            session_id=query.user_id,
            channel=query.channel,
            tool_used=result.get("tool_used"),
            source_type=result.get("source_type"),
            docs_count=result.get("docs_count"),
            timing_ms=result.get("timing_ms"),
            metadata=meta_dict
        )
    except Exception as e:
        # Control estricto de excepciones para evitar la divulgación involuntaria de secretos del sistema
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag-debug")
def rag_debug(query: LegacyChatRequest):
    """
    Endpoint de trazabilidad técnica.
    Devuelve los fragmentos recuperados para una pregunta sin pasar por el LLM.
    """
    try:
        service = get_service()
        return service.debug_rag_query(query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ORQUESTADOR ---

def run_orchestrator():
    parser = argparse.ArgumentParser(description="Pipeline Dollarcity AI - Taller 2")
    parser.add_argument("--scrape", action="store_true", help="Ejecutar scraping")
    parser.add_argument("--clean", action="store_true", help="Curar datos e indexar Chroma")
    parser.add_argument("--chat", action="store_true", help="Chat en consola")
    parser.add_argument("--server", action="store_true", help="Levantar servidor FastAPI")
    parser.add_argument("--full", action="store_true", help="Flujo completo")

    args = parser.parse_args()

    if args.full or args.scrape:
        print("\n>>> FASE 1: INGESTIÓN...")
        asyncio.run(run_scraper())

    if args.full or args.clean:
        print("\n>>> FASE 2: CURACIÓN SEMÁNTICA E INDEXACIÓN...")
        run_semantic_curation()

    if args.chat:
        print("\n>>> FASE 3: CHAT DE VALIDACIÓN...")
        start_console_chat()

    if args.full or args.server:
        print("\n>>> SERVIDOR ACTIVO EN PUERTO 8000...")
        uvicorn.run(app, host="127.0.0.1", port=8000)

    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    run_orchestrator()