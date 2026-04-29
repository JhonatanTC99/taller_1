import asyncio
import httpx
import fitz
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src.config.settings import TARGET_URLS, RAW_DATA_DIR, ensure_dirs
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def run_scraper():
    """
    Orquesta la extracción de contenido web convirtiendo URLs a Markdown.
    Fase 1 del pipeline: Ingesta de datos brutos.
    """
    print("\n[INFO] Iniciando Extractor de Datos (Crawl4AI) - Fase 1")
    ensure_dirs()

    # IDENTIFICAR TIPOS DE URL
    pdf_urls = [url for url in TARGET_URLS if url.lower().endswith(".pdf")]
    web_urls = [url for url in TARGET_URLS if not url.lower().endswith(".pdf")]

    # Procesamiento de PDFs
    if pdf_urls:
        print(f"[INFO] Procesando {len(pdf_urls)} archivos PDF...")
        async with httpx.AsyncClient(verify=False) as client:
            for url in pdf_urls:
                try:
                    print(f"[STEP] Procesando PDF: {url}")
                    response = await client.get(url, follow_redirects=True)
                    doc = fitz.open(stream=response.content, filetype="pdf")
                    text = "".join([page.get_text() for page in doc])
                    
                    filename = url.split("/")[-1].replace(".pdf", ".md")
                    output_path = RAW_DATA_DIR / filename
                    output_path.write_text(f"SOURCE_URL: {url}\n\n# PDF: {url}\n\n{text}", encoding="utf-8")
                    print(f"   [OK] PDF Guardado: {filename}")
                except Exception as e:
                    print(f"   [ERROR] PDF fallido {url}: {e}")

    # CONFIGURACIÓN DE FILTRADO

    tags_to_exclude = ['nav', 'footer', 'header', 'aside', 'script', 'style']

    md_generator = DefaultMarkdownGenerator(
        options={
            "ignore_links": True,    # No enlaces
            "ignore_images": True,   # No imágenes
            "body_width": 0,         # Sin saltos de línea forzados
            "skip_internal_links": True # No enlaces internos (ej: menú de navegación)
        }
    )

    # Configuración del NAVEGADOR
    browser_conf = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Configuración de RENDERIZADO
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, # Siempre renderiza para obtener contenido dinámico actualizado
        markdown_generator=md_generator, # Personalización del generador de Markdown
        excluded_tags=['nav', 'footer', 'header', 'aside', 'script', 'style', 'noscript', 'form'],
        css_selector="article, .article-body, .content-article, .entry-content, #main-content ,.content, main, .container, .product-item", # Selectores comunes para contenido principal
        remove_overlay_elements=True, # Quita pop-ups y banners de cookies
        wait_for="css:main, .container, .product-item",
        page_timeout=60000, # Aumenta el timeout para páginas pesadas o con mucho JS (60 segundos)
        process_iframes=False,
        js_code="window.scrollTo(0, document.body.scrollHeight);", # Simula scroll para cargar contenido dinámico
        simulate_user=True, 
        override_navigator=True
    )

    
    # Extracción masiva (Paralelismo) # PROCESAMIENTO WEB ASINCRÓNICO
    if web_urls:        
        async with AsyncWebCrawler(verbose=False, config=browser_conf) as crawler:
            print(f"[INFO] Procesando {len(web_urls)} páginas web en paralelo...")
            
            results = await crawler.arun_many(urls=web_urls, config=crawl_config)


            for result in results:
                if result.success:
                    url = result.url
                    html_to_process = result.cleaned_html if result.cleaned_html else result.html
                    soup = BeautifulSoup(html_to_process, 'html.parser')

                    # Lista maestra de "Basura Común" en la web
                    ruido_global = [
                        # Publicidad y banners
                        '.ads', '.ad-container', '.banner', '.publi', '.advertising',
                        # Redes sociales y compartir
                        '.social-share', '.share-bar', '.social-links', '.social-media',
                        # Navegación y elementos de página no deseados
                        'nav', 'footer', 'header', 'aside', '.menu', '.sidebar',
                        # Noticias relacionadas y recomendaciones (El ruido que viste antes)
                        '.related', '.recommended', '.suggested', '.trending', '.more-news',
                        '.tags', '.categories', '.topic-tags', '.related-posts',
                        # Información de autor y comentarios
                        '.author-box', '.author-bio', '.comments', '#comments', '.comment-list',
                        # Popups y modales
                        '.modal', '.popup', '.overlay', '.newsletter-signup'
                    ]

                    for selector in ruido_global:
                        for element in soup.select(selector):
                            element.decompose() # Lo elimina completamente del árbol HTML

                    content = soup.get_text(separator='\n\n', strip=True)

                    if len(content) < 200:
                        content = result.markdown
                    

                    if "dollarcity.com" in url.lower():
                        # Definir el nombre del archivo
                        path_parts = url.split("dollarcity.com/")[-1].strip("/").split("/")
                        filename_base = "_".join(path_parts) if (path_parts and path_parts[0]) else "home"
                        if filename_base == "co": filename_base = "home"
                        clean_name = f"dollarcity_{filename_base}"

                        # Lógica de contenido
                        content = result.markdown if len(result.markdown) > 200 else soup.get_text(separator='\n\n', strip=True)
                        if len(content) < 100:
                            content = "Error: El contenido no cargó a tiempo. Reintentar con mayor wait_for."

                    else:
                        # Lógica para otros sitios (dominio + path)
                        parsed = urlparse(url)
                        domain = parsed.netloc.replace(".", "_")
                        path = parsed.path.replace("/", "_").strip("_")
                        clean_name = f"{domain}_{path}" if path else domain

                    # Limitar longitud de nombre y guardar
                    output_path = RAW_DATA_DIR / f"{clean_name[:60]}.md"
    
                    try:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(f"SOURCE_URL: {url}\n\n")
                            f.write(content)
                        print(f"   [OK] Guardado: {output_path.name}")
                    except Exception as e:
                        print(f"   [ERROR] No se pudo escribir el archivo {output_path.name}: {e}")
                else:
                    print(f"   [ERROR] Fallo en {result.url}: {result.error_message}")

if __name__ == "__main__":
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        print("\n[STOP] Proceso interrumpido por el usuario.")

