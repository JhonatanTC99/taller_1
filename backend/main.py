import argparse
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Lógica interna del motor
from src.scraper.collector import run_scraper
from src.processor.cleaner import build_dynamic_kb as run_semantic_curation
from src.engine.llm_service import LLMService, start_console_chat

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
    Implementación de Singleton con Lazy Loading.
    Evita inicializar ChromaDB durante la ejecución de comandos CLI de limpieza.
    """
    global _service
    if _service is None:
        _service = LLMService()
    return _service

class ChatQuery(BaseModel):
    question: str
    model: str | None = None

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Backend Dollarcity Online", "version": "2.2-StabilityFix"}

@app.get("/debug")
def debug():
    """Valida el estado del servidor y el modelo activo."""
    service = get_service()
    return {
        "msg": "ESTOY EN MAIN.PY",
        "model": service.get_model_name(),
        "session_id": service.session_id
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
    service = get_service()
    return service.get_summary() 

@app.get("/api/faq")
def get_faq():
    service = get_service()
    return service.get_faq()

@app.post("/api/chat")
def chat(query: ChatQuery):
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

@app.post("/api/rag-debug")
def rag_debug(query: ChatQuery):
    """
    Nuevo endpoint de trazabilidad.
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
        # Aquí no llamamos a get_service() para no borrar Chroma antes de usarlo
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