import asyncio
from src.config.settings import TARGET_URLS, RAW_DATA_DIR, ensure_dirs
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def run_scraper():
    """
    Orquesta la extracción de contenido web convirtiendo URLs a Markdown.
    Fase 1 del pipeline: Ingesta de datos brutos.
    """
    print("\n[INFO] Iniciando Extractor de Datos (Crawl4AI) - Fase 1")
    ensure_dirs()
    
    # Configuración del crawler para optimizar la salida hacia LLMs
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, # Asegura datos frescos en cada ejecución
        word_count_threshold=10,     # Filtra fragmentos de texto irrelevantes
        wait_for="body"              # Espera a que el DOM básico esté cargado
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        for url in TARGET_URLS:
            print(f"[STEP] Procesando: {url}")
            
            try:
                # Ejecución del crawling con la configuración definida
                result = await crawler.arun(url=url, config=crawl_config)
                
                if result.success:
                    # Normalización del nombre de archivo (slug)
                    filename = url.split("dollarcity.com/")[-1].replace("/", "_").strip("_")
                    if not filename or filename == "co": 
                        filename = "home"
                    
                    output_path = RAW_DATA_DIR / f"{filename}.md"
                    
                    # Persistencia del contenido en Markdown limpio
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(result.markdown)
                    
                    print(f"   [OK] Guardado: {output_path.name}")
                else:
                    print(f"   [ERROR] Fallo en {url}: {result.error_message}")
            
            except Exception as e:
                print(f"   [CRITICAL] Error inesperado en {url}: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        print("\n[STOP] Proceso interrumpido por el usuario.")