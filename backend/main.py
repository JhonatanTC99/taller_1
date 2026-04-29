import argparse
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importaciones de tu lógica interna
from src.scraper.collector import run_scraper
from src.processor.cleaner import build_dynamic_kb as run_semantic_curation
from src.engine.llm_service import LLMService, start_console_chat

# --- CONFIGURACIÓN DE LA API (Fuera de funciones para que Uvicorn la vea) ---
app = FastAPI(title="Dollarcity AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializamos el servicio (se cargará al importar el módulo)
service = LLMService()

class ChatQuery(BaseModel):
    question: str
    model: str | None = None


@app.get("/")
def home():
    return {"status": "Backend Dollarcity Online"}

@app.get("/api/summary")
def get_summary():
    return service.get_summary() 

@app.get("/api/faq")
def get_faq():
    return service.get_faq()

@app.post("/api/chat")
def chat(query: ChatQuery):
    try:
        q = query.question.lower().strip()

        if query.model:
            service.set_model(query.model)

        if q == "identity_check":
            return {
                "content": "ok",
                "model": service.get_model_name()
            }

        greetings = ["hola", "buenas", "hey", "hello"]

        if q in greetings:
            return {
                "content": "¡Hola! Somos Dollarcity Colombia. ¿En qué podemos ayudarte?",
                "model": service.get_model_name()
            }
        if q.isdigit():
            return {
                "content": "Lo sentimos, no contamos con esa información específica.",
                "model": service.get_model_name()
            }

        return service.get_chat_response(query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/debug")
def debug():
    return {
        "msg": "ESTOY EN MAIN.PY",
        "model": service.get_model_name()
    }

# --- LÓGICA DEL ORQUESTADOR (Consola) ---
def run_orchestrator():
    parser = argparse.ArgumentParser(description="Pipeline Dollarcity AI - Módulo 1")
    parser.add_argument("--scrape", action="store_true", help="Ejecutar scraping de URLs")
    parser.add_argument("--clean", action="store_true", help="Procesar y curar datos")
    parser.add_argument("--chat", action="store_true", help="Abrir chat interactivo en consola")
    parser.add_argument("--server", action="store_true", help="Solo levantar el servidor API")
    parser.add_argument("--full", action="store_true", help="Ejecutar todo el flujo + Servidor")

    args = parser.parse_args()

    # FASE 1: Ingesta
    if args.full or args.scrape:
        print("\n>>> FASE 1: INICIANDO SCRAPING...")
        asyncio.run(run_scraper())

    # FASE 2: Curación
    if args.full or args.clean:
        print("\n>>> FASE 2: INICIANDO CURACIÓN SEMÁNTICA...")
        run_semantic_curation()

    # FASE 3: Chat de Validación (Consola)
    if args.chat:
        print("\n>>> FASE 3: INICIANDO CHAT DE CONSOLA...")
        start_console_chat()

    # FASE FINAL: Servidor para React
    if args.full or args.server:
        print("\n>>> INICIANDO SERVIDOR API PARA REACT (Puerto 8000)...")
        # Esto lanza uvicorn programáticamente
        uvicorn.run(app, host="127.0.0.1", port=8000)

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    run_orchestrator()