from pathlib import Path

# --- RUTAS DEL PROYECTO ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carpetas de datos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
KB_DIR = DATA_DIR / "knowledge_base"

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

# --- CONFIGURACIÓN LLM (Para fases futuras, declaradas aquí por estabilidad) ---
DEFAULT_MODEL = "gemma4:latest"
OLLAMA_BASE_URL = "http://localhost:11434"

def ensure_dirs():
    """Crea las carpetas necesarias si no existen."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    KB_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    # Test rápido de rutas
    print(f"Proyecto en: {BASE_DIR}")
    ensure_dirs()
    print("Estructura de carpetas verificada.")

KB_FILE_PATH = KB_DIR / "dollarcity_context.md"