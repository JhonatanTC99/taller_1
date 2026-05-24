"""
Módulo de configuración centralizado para el sistema conversacional de Dollarcity.

Este componente gestiona las variables de entorno, la inicialización de rutas 
absolutas del proyecto y la parametrización de las arquitecturas de ejecución.
Mantiene compatibilidad retrospectiva con los componentes de extracción y procesamiento
del Módulo 2 (Legacy) y define la infraestructura de configuración requerida para la
orquestación agéntica, persistencia distribuida y observabilidad avanzadas del Módulo 3.

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A (Arquitectura Tradicional Enterprise)
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Carga de variables de entorno globales desde el archivo de configuración .env
load_dotenv()


def get_bool_env(name: str, default: bool = False) -> bool:
    """
    Evalúa de forma estricta variables de entorno para su conversión a tipos booleanos.

    Args:
        name (str): Nombre de la variable de entorno a evaluar.
        default (bool): Valor de retorno por defecto en caso de ausencia o indeterminación.

    Returns:
        bool: Representación booleana interpretada del valor de entorno.
    """
    value = os.getenv(name)
    if value is None:
        return default
    
    clean_value = value.strip().lower()
    if clean_value in ("true", "1", "yes", "y", "on"):
        return True
    if clean_value in ("false", "0", "no", "n", "off"):
        return False
        
    return default


def mask_database_url(url: str) -> str:
    """
    Ofusca las credenciales explícitas dentro de una cadena de conexión (URI) de base de datos.
    Previene la fuga de información sensible en los flujos de diagnóstico del backend.

    Args:
        url (str): URI completa de conexión a la base de datos.

    Returns:
        str: Cadena de conexión modificada con la contraseña enmascarada.
    """
    if not url:
        return ""
    # Patrón estándar para capturar esquemas tipo dialecto://usuario:contraseña@host
    pattern = r"^(?P<protocol>[^:]+://)(?P<user>[^:]+):(?P<password>[^@]+)(?P<rest>@.+)$"
    match = re.match(pattern, url)
    if match:
        return f"{match.group('protocol')}{match.group('user')}:******{match.group('rest')}"
    return url


# =====================================================================
# SECCIÓN I: ARQUITECTURA DE RUTAS DEL PROYECTO (Rutas Absolutas)
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Directorios de datos y almacenamiento persistente local
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
KB_DIR = DATA_DIR / "knowledge_base"
KB_FILE_PATH = KB_DIR / "dollarcity_context.md"
CHROMA_PATH = DATA_DIR / "chroma_db"
HISTORY_DIR = DATA_DIR / "history"
SPECIFIC_QUESTION_DIR = DATA_DIR / "specific_questions"
SPECIFIC_QUESTION_PATH = SPECIFIC_QUESTION_DIR / "data_corporativa.json"

# Nuevos directorios de producción para el Módulo 3
LOG_DIR = DATA_DIR / "logs"
CONVERSATION_LOG_PATH = LOG_DIR / "conversation_logs.jsonl"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
REPORTS_DIR = BASE_DIR / "reports"


# =====================================================================
# SECCIÓN II: INFRAESTRUCTURA LLM LEGACY (Módulo 2 / Componentes Base)
# =====================================================================
# Identificador del proveedor de inferencia: 'google' o 'ollama'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google").lower()

# Configuración del entorno Google Gen AI (API de Gemini)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-3.1-flash-lite")

# Configuración de servicios locales mediante Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")

# Selección determinista del modelo por defecto para componentes síncronos lineales
if LLM_PROVIDER == "google":
    DEFAULT_MODEL = GOOGLE_MODEL
else:
    DEFAULT_MODEL = OLLAMA_MODEL

# Modelo de representación vectorial de texto (Embeddings locales)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# =====================================================================
# SECCIÓN III: MOTOR DE AGENTES MÓDULO 3 (LangChain / LangGraph)
# =====================================================================
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", LLM_PROVIDER).lower()
AGENT_MODEL = os.getenv("AGENT_MODEL", DEFAULT_MODEL)
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.1"))
AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "2"))


# =====================================================================
# SECCIÓN IV: CAPA DE PERSISTENCIA DISTRIBUIDA (PostgreSQL / Checkpointing)
# =====================================================================
# Cadena de conexión requerida por la clase PostgresSaver para persistencia de grafos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/dollarcity_agent"
)
# Prefijo estructural para las tablas de checkpoints gestionadas por LangGraph
CHECKPOINT_TABLE_PREFIX = os.getenv("CHECKPOINT_TABLE_PREFIX", "dollarcity_agent")


# =====================================================================
# SECCIÓN V: INTERFACES Y CANALES DE INTEGRACIÓN EXTERNA
# =====================================================================
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://127.0.0.1:8000")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")


# =====================================================================
# SECCIÓN VI: CONMUTADORES DE ARQUITECTURA (Feature Flags)
# =====================================================================
ENABLE_AGENT_V3 = get_bool_env("ENABLE_AGENT_V3", False)
ENABLE_CONVERSATION_LOGGING = get_bool_env("ENABLE_CONVERSATION_LOGGING", True)
ENABLE_HITL = get_bool_env("ENABLE_HITL", False)
ENABLE_LEGACY_CHAT = get_bool_env("ENABLE_LEGACY_CHAT", True)
ENABLE_RAG_DEBUG = get_bool_env("ENABLE_RAG_DEBUG", True)


# =====================================================================
# SECCIÓN VII: OBSERVABILIDAD Y TRAZABILIDAD EMPRESARIAL
# =====================================================================
LANGSMITH_TRACING = get_bool_env("LANGSMITH_TRACING", False)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# =====================================================================
# SECCIÓN VIII: FUENTES DE DATOS PARA SCRAPING (Backward Compatibility)
# =====================================================================
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


def ensure_dirs():
    """
    Garantiza la existencia física de la estructura de directorios del proyecto.
    Crea las rutas necesarias de forma segura si no se encuentran en el sistema de archivos.
    """
    directories = [
        RAW_DATA_DIR, 
        KB_DIR, 
        CHROMA_PATH, 
        HISTORY_DIR, 
        SPECIFIC_QUESTION_DIR,
        LOG_DIR,
        NOTEBOOKS_DIR,
        REPORTS_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Inicialización automatizada del entorno de directorios durante el proceso de importación
ensure_dirs()

# =====================================================================
# SECCIÓN IX: VERIFICACIÓN Y DIAGNÓSTICO DE CONFIGURACIÓN
# =====================================================================
if __name__ == "__main__":
    print("=====================================================================")
    print(" DIAGNÓSTICO SISTEMA CONVERSACIONAL DOLLARCITY - CONFIGURACIÓN V3")
    print("=====================================================================")
    print(f"BASE_DIR:                    {BASE_DIR}")
    print(f"DATA_DIR:                    {DATA_DIR}")
    print(f"CHROMA_PATH:                 {CHROMA_PATH}")
    print(f"KB_FILE_PATH:                {KB_FILE_PATH}")
    print(f"LLM_PROVIDER (Legacy):       {LLM_PROVIDER}")
    print(f"DEFAULT_MODEL (Legacy):      {DEFAULT_MODEL}")
    print(f"AGENT_PROVIDER (V3):         {AGENT_PROVIDER}")
    print(f"AGENT_MODEL (V3):            {AGENT_MODEL}")
    print(f"ENABLE_AGENT_V3:             {ENABLE_AGENT_V3}")
    print(f"ENABLE_CONVERSATION_LOGGING: {ENABLE_CONVERSATION_LOGGING}")
    print(f"ENABLE_HITL:                 {ENABLE_HITL}")
    print(f"DATABASE_URL (Persistencia): {mask_database_url(DATABASE_URL)}")
    print("=====================================================================")
    print("[SUCCESS] Archivo settings.py importable y validado correctamente.")