import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import TARGET_URLS, RAW_DATA_DIR, ensure_dirs
from crawl4ai import AsyncWebCrawler

async def run_scraper():
    """
    Ejecuta el proceso de extracción de contenido utilizando Crawl4AI.
    """
    print("\n[INFO] Iniciando Extractor de Datos - Fase 1")
    ensure_dirs()
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in TARGET_URLS:
            print(f"\n[STEP] Procesando: {url}")
            
            try:
                # Ejecutar el crawling con renderizado básico de JS
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Generar nombre de archivo basado en la URL
                    filename = url.replace("https://", "").replace("/", "_").strip("_") + ".md"
                    output_path = RAW_DATA_DIR / filename
                    
                    # Guardar el contenido en Markdown
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(result.markdown)
                    
                    print(f"[OK] Guardado en: {output_path}")
                else:
                    print(f"[ERROR] No se pudo extraer {url}: {result.error_message}")
            
            except Exception as e:
                print(f"[CRITICAL] Error inesperado en {url}: {str(e)}")

if __name__ == "__main__":
    # Ejecución asíncrona compatible con Windows
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        print("\n[STOP] Proceso interrumpido por el usuario.")