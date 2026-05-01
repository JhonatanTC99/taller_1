import asyncio
import httpx
import fitz
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src.config.settings import TARGET_URLS, RAW_DATA_DIR, ensure_dirs
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# --- CONFIGURACIÓN DE CALIDAD ---
MIN_CONTENT_LENGTH = 300
FORBIDDEN_SIGNATURES = [
    "Crawl4AI Error", "Invalid expression", "This page is not fully supported",
    "Too Many Requests", "Blocked by anti-bot", "Error: El contenido no cargó",
    "Cloudflare", "Access Denied", "403 Forbidden"
]

def is_valid_content(text: str) -> bool:
    """Verifica si el texto no contiene firmas de error técnico."""
    if not text or len(text) <= 5: return False
    return not any(sig in text for sig in FORBIDDEN_SIGNATURES)

async def run_scraper():
    print("\n[INFO] 🚀 Iniciando Fase 1: Extracción Flexible y Validación")
    ensure_dirs()

    pdf_urls = [url for url in TARGET_URLS if url.lower().endswith(".pdf")]
    web_urls = [url for url in TARGET_URLS if not url.lower().endswith(".pdf")]

    # 1. PROCESAMIENTO DE PDFs (Se mantiene igual)
    if pdf_urls:
        async with httpx.AsyncClient(verify=False) as client:
            for url in pdf_urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    doc = fitz.open(stream=response.content, filetype="pdf")
                    text = "".join([page.get_text() for page in doc])
                    decision = "GUARDADO" if len(text) >= MIN_CONTENT_LENGTH else "DESCARTADO"
                    if decision == "GUARDADO":
                        filename = url.split("/")[-1].replace(".pdf", ".md")
                        (RAW_DATA_DIR / filename).write_text(f"SOURCE_URL: {url}\n\n# PDF: {filename}\n\n{text}", encoding="utf-8")
                    print(f"[PDF] {url} | Len: {len(text)} | Decisión: {decision}")
                except Exception as e:
                    print(f"[ERROR PDF] {url}: {e}")

    # 2. CONFIGURACIÓN CRAWL4AI (Tolerante y potente)
    # Eliminamos el css_selector restrictivo para capturar todo el body
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True, "ignore_images": True, "body_width": 0}),
        excluded_tags=['nav', 'footer', 'header', 'aside', 'script', 'style', 'form', 'noscript'],
        wait_for="body", 
        page_timeout=80000, # Más tiempo para carga de JS
        simulate_user=True,
        # Scroll dinámico para despertar contenido Lazy Load
        js_code="window.scrollTo(0, document.body.scrollHeight);", 
        word_count_threshold=10
    )

    # 3. EXTRACCIÓN WEB CON RESCATE
    if web_urls:        
        async with AsyncWebCrawler(verbose=False) as crawler:
            print(f"[WEB] 🌐 Procesando {len(web_urls)} URLs...")
            results = await crawler.arun_many(urls=web_urls, config=crawl_config)

            for result in results:
                method = "none"
                content = ""
                
                # INTENTO 1: Markdown (Si es válido y largo suficiente)
                if result.success and is_valid_content(result.markdown):
                    if len(result.markdown) >= MIN_CONTENT_LENGTH:
                        content = result.markdown
                        method = "markdown"

                # INTENTO 2: Rescate vía BeautifulSoup (Si el Markdown falló o es muy corto)
                if not content:
                    html_source = result.cleaned_html if result.cleaned_html else result.html
                    if html_source:
                        soup = BeautifulSoup(html_source, 'html.parser')
                        # Eliminamos tags de ruido manualmente antes de extraer texto
                        for tag in soup(['nav', 'footer', 'header', 'style', 'script']):
                            tag.decompose()
                        extracted = soup.get_text(separator='\n', strip=True)
                        
                        if is_valid_content(extracted) and len(extracted) >= MIN_CONTENT_LENGTH:
                            content = extracted
                            method = "html_soup_rescue"

                # VALIDACIÓN FINAL Y GUARDADO
                decision = "DESCARTADO"
                if content and len(content) >= MIN_CONTENT_LENGTH:
                    decision = "GUARDADO"
                    parsed = urlparse(result.url)
                    # Nombre de archivo basado en el path de la URL
                    path_name = parsed.path.replace("/", "_").strip("_")
                    if not path_name or path_name == "co": path_name = "home"
                    filename = f"dollarcity_{path_name}.md" if "dollarcity" in result.url else f"ext_{path_name[:30]}.md"
                    
                    (RAW_DATA_DIR / filename).write_text(f"SOURCE_URL: {result.url}\n\n{content}", encoding="utf-8")
                
                print(f"[WEB] {result.url[:50]}... | Len: {len(content)} | Método: {method} | Decisión: {decision}")

if __name__ == "__main__":
    asyncio.run(run_scraper())