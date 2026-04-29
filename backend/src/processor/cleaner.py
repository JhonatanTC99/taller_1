import re
from pathlib import Path
from src.config.settings import RAW_DATA_DIR, KB_DIR, KB_FILE_PATH

def clean_text(text: str) -> str:
    """Limpia ruido y quita la línea SOURCE_URL para que no ensucie el contenido."""
    
    # Eliminar la URL de origen al inicio
    text = re.sub(r'^SOURCE_URL: .*?\n', '', text)

    # Eliminar basura de Markdown (Imágenes y Links)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text) # Imágenes con link
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Links
    text = re.sub(r'!?\[.*?\]', '', text)       # Restos de etiquetas [ ]

    # Eliminar líneas de navegación (Breadcrumbs)
    text = re.sub(r'.* \> .* \> .*', '', text)

    # Lista de ruido agresiva (Elimina la línea completa donde aparezca el término)
    ruido_patterns = [
        r'(?i)(te puede interesar|lea también|artículos relacionados|relacionado:).*',
        r'(?i)(descargue la app|síguenos en redes|todos los derechos reservados|copyright|©).*',
        r'(?i)(aviso legal|política de cookies|aviso de privacidad|términos y condiciones).*',
        r'(?i)(publicidad|anuncio|newsletter|suscríbete).*',
        r'(?i)(derechos reservados|aviso de seguridad|aviso de datos).*'
    ]
    for pattern in ruido_patterns:
        text = re.sub(pattern, '', text)
    
    #Normalización final para eliminar espacios y saltos de línea excesivos
    # Quitar múltiples saltos de línea (convertir 3 o más en solo 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Quitar espacios en blanco al inicio/final de cada línea
    text = '\n'.join([line.strip() for line in text.split('\n')])
    # Quitar espacios horizontales duplicados
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def build_dynamic_kb():
    print(f"\n[INFO] Iniciando Curación Dinámica...")
    
    if not RAW_DATA_DIR.exists():
        print("[ERROR] No hay datos raw.")
        return

    oficial_content = []
    prensa_content = []
    otros_content = []

    for file_path in RAW_DATA_DIR.glob("*.md"):
        try:
            raw_text = file_path.read_text(encoding="utf-8")
            
            # EXTRAEMOS LA URL REAL de la primera línea
            first_line = raw_text.split('\n')[0]
            if "SOURCE_URL: " in first_line:
                actual_url = first_line.replace("SOURCE_URL: ", "").strip()
            else:
                actual_url = file_path.name # Fallback al nombre de archivo

            content = clean_text(raw_text)
            
            # CLASIFICACIÓN
            if "dollarcity.com" in actual_url:
                header = f"### [FUENTE OFICIAL: DOLLARCITY]\n- URL: {actual_url}"
                oficial_content.append(f"{header}\n{content}\n")
            
            elif any(d in actual_url for d in ["eltiempo", "larepublica", "portafolio", "las2orillas", "valoraanalitik", "pulzo", "redmas"]):
                header = f"### [PRENSA Y ECONOMÍA]\n- URL: {actual_url}"
                prensa_content.append(f"{header}\n{content}\n")
            
            else:
                header = f"### [INFORMACIÓN COMPLEMENTARIA]\n- URL: {actual_url}"
                otros_content.append(f"{header}\n{content}\n")

        except Exception as e:
            print(f"   [SKIP] Error en {file_path.name}: {e}")

    # CONSTRUCCIÓN DE LA KB (Con instrucciones de peso para Gemma 3)
    final_kb = [
        "# BASE DE CONOCIMIENTO UNIFICADA - DOLLARCITY COLOMBIA",
        "\n" + "="*40 + "\n",
        "## SECCIÓN I: FUENTES OFICIALES (POLÍTICAS Y T&C)",
        "\n".join(oficial_content) if oficial_content else "No hay datos oficiales disponibles.",
        "\n" + "="*40 + "\n",
        "## SECCIÓN II: PRENSA, NOTICIAS Y ANÁLISIS EXTERNO",
        "\n".join(prensa_content) if prensa_content else "No hay datos de prensa disponibles.",
        "\n" + "="*40 + "\n",
        "## SECCIÓN III: OTROS DATOS",
        "\n".join(otros_content) if otros_content else "No hay datos complementarios."
    ]

    KB_DIR.mkdir(parents=True, exist_ok=True)
    KB_FILE_PATH.write_text("\n".join(final_kb), encoding="utf-8")
    print(f"[SUCCESS] KB generada en: {KB_FILE_PATH}")

if __name__ == "__main__":
    build_dynamic_kb()