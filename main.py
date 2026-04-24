import argparse
import asyncio
from src.scraper.collector import run_scraper
from src.processor.cleaner import run_semantic_curation
from src.engine.llm_service import start_console_chat  # Ahora esta función sí existe

def main():
    """
    Orquestador principal del taller. Permite ejecutar fases individuales o el pipeline completo.
    """
    parser = argparse.ArgumentParser(description="Pipeline Dollarcity AI - Módulo 1")
    parser.add_argument("--scrape", action="store_true", help="Ejecutar scraping de URLs")
    parser.add_argument("--clean", action="store_true", help="Procesar y curar datos")
    parser.add_argument("--chat", action="store_true", help="Abrir chat interactivo en consola")
    parser.add_argument("--full", action="store_true", help="Ejecutar todo el flujo")

    args = parser.parse_args()

    if args.full or args.scrape:
        print("\n>>> FASE 1: INICIANDO SCRAPING...")
        asyncio.run(run_scraper())

    if args.full or args.clean:
        print("\n>>> FASE 2: INICIANDO CURACIÓN SEMÁNTICA...")
        run_semantic_curation()

    if args.chat:
        print("\n>>> FASE 3: INICIANDO CHAT DE CONSOLA...")
        start_console_chat()

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()