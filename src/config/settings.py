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
    "https://dollarcity.com/ubicaciones"
]

# --- CONFIGURACIÓN LLM ---
# Se prioriza la variable de entorno, de lo contrario usa el default
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemma4:latest") 
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