import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# --- RUTAS DEL PROYECTO (Absolutas para evitar errores de contexto) ---
# BASE_DIR apunta a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carpetas de datos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
KB_DIR = DATA_DIR / "knowledge_base"
KB_FILE_PATH = KB_DIR / "dollarcity_context.md"

# --- CONFIGURACIÓN DE SCRAPING ---
TARGET_URLS = [
    "https://dollarcity.com/co/",
    "https://dollarcity.com/nuestro-equipo/",
    "https://dollarcity.com/quienes-somos/",
    "https://dollarcity.com/oportunidades/",
    "https://dollarcity.com/programas-de-talento/",
    "https://dollarcity.com/preguntas-frecuentes/",
    "https://dollarcity.com/ubicaciones",
    "https://dollarcity.com/privacidad/",
    "https://co.computrabajo.com/dollarcityco",
    "https://co.computrabajo.com/dollarcityco/empleos",
    "https://www.lafm.com.co/economia/los-cinco-productos-de-dollarcity-que-no-pueden-faltar-322827",
    "https://www.las2orillas.co/los-10-productos-de-dollarcity-para-equipar-su-cocina-bano-sala-y-otros-espacios-del-hogar/",
    "https://dollarcity.com/wp-content/uploads/2023/09/tyc-col.pdf",
    "https://empresas.larepublica.co/colombia/valle-del-cauca/cali/suramerica-comercial-s-a-s-900943243",
    "https://www.las2orillas.co/la-genial-idea-de-dollarcity-que-enriquecio-un-par-de-salvadorenos/",
    "https://www.las2orillas.co/los-canadienses-duenos-de-dollarcity-que-la-pusieron-a-volar-con-colombia-como-eje-regional-del-negocio/",
    "https://www.eltiempo.com/economia/empresas/quienes-son-los-duenos-de-dollarcity-fundacion-y-secreto-de-su-exito-750212",
    "https://www.kienyke.com/marketing/dollarcity-cual-es-la-historia-detras-de-su-concepto",
    "https://redmas.com.co/tendencias/El-multimillonario-detras-del-exito-de-Dollarcity-en-Colombia-con-exitosa-estrategia-desafia-a-Tiendas-D1-y-Oxxo-20250422-0044.html",
    "https://es-us.finanzas.yahoo.com/noticias/dolar-exito-detras-dollarcity-millonaria-tienda-vende-todo-barato-115224476.html?guccounter=1&guce_referrer=aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8&guce_referrer_sig=AQAAAHjVsc0DmbKkc3QTCuxUVZBe9cy8_-WGoMDYT2ld9_sqSrZz0HKCDGObkoBy9_3xln4YL20SvxqdFu4yL-B52YgY2vC1N_bro15rnCxlaTmm50H4rviU4_c196-XMJ6VZhpECBtSM6p4aiiWI7eArMVcUR6p0Zoxx6MqmPfHAO8i",
    "https://www.portafolio.co/tendencias/la-historia-detras-de-dollarcity-y-quienes-son-sus-fundadores-579963",
    "https://www.grupomercadeo.com/tag/dollarcity/",
    "https://www.pulzo.com/empleo/como-hacer-hoja-vida-llamativa-para-conseguir-trabajo-PP5142763?utm_source=scroll_pulzo&utm_medium=pulzo_comercial&utm_campaign=scroll_pulzo",
    "https://colombiaretail.com/los-canadienses-duenos-de-dollarcity-que-la-pusieron-a-volar-con-colombia-como-eje-regional-del-negocio-las2orillas/",
    "https://elcomercio.pe/respuestas/colombia/como-se-fundo-y-quienes-son-los-duenos-de-dollarcity-retail-colombia-tdex-noticia/",
    "https://redmas.com.co/amp/tendencias/Dueno-de-Dollarcity-reconocido-supermercado-sorprende-con-decision-a-mas-de-10-mil-kilometros-de-Colombia-20250722-0041.html",
    "https://www.negociosyemprendimiento.org/2023/09/historia-dollarcity.html",
    "https://www.valoraanalitik.com/dollarama-duenos-de-dollarcity-hizo-inesperado-anuncio-con-tiendas-para-expandir-su-emporio/",
    "https://redmas.com.co/tendencias/Dueno-de-Dollarcity-toma-decision-determinante-para-la-cadena-de-supermercados-con-presencia-en-Colombia-Es-estrategia-20250722-0041.html",
    "https://www.eltiempo.com/economia/empresas/plan-de-expansion-de-dollarcity-en-colombia-383164",
    "https://www.halconesypalomas.com/2025/06/27/dollarcity-se-metera-entre-las-40-empresas-mas-grandes-de-colombia-en-2025-facturara-10-mas-que-el-ano-pasado-hasta-cerca-de-31-billones/",
    "https://directorio-empresas.einforma.co/informacion-empresa/suramerica-comercial-sas"
]

# --- CONFIGURACIÓN LLM ---
# Se prioriza la variable de entorno, de lo contrario usa el default
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemma3:1b") #"gemma4:latest") 
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def ensure_dirs():
    """Crea la estructura de directorios necesaria para el proyecto."""
    directories = [RAW_DATA_DIR, KB_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"[INFO] Inicializando entorno en: {BASE_DIR}")
    ensure_dirs()
    print("[SUCCESS] Directorios de datos verificados.")