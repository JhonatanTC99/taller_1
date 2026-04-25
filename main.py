import os
import argparse
import asyncio
from src.scraper.collector import run_scraper
from src.processor.cleaner import run_semantic_curation
from src.engine.llm_service import start_console_chat 

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

    # FASE 1: Ingesta
    if args.full or args.scrape:
        print("\n>>> FASE 1: INICIANDO SCRAPING...")
        asyncio.run(run_scraper())

    # FASE 2: Curación
    if args.full or args.clean:
        print("\n>>> FASE 2: INICIANDO CURACIÓN SEMÁNTICA...")
        run_semantic_curation()

    # FASE 3: Prueba de Concepto (Consola)
    # Se ajusta para que el modo FULL también pase por el chat de validación
    if args.full or args.chat:
        print("\n>>> FASE 3: INICIANDO CHAT DE CONSOLA (Validación)...")
        start_console_chat()

    # FASE FINAL: Interfaz Gráfica
    # Solo se dispara en modo FULL después de cerrar el chat de consola
    if args.full:
        print("\n>>> FASE FINAL: ABRIENDO APLICACIÓN WEB (STREAMLIT)...")
        # Ejecuta el comando de sistema para levantar la UI
        os.system("streamlit run src/ui/app.py")

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()