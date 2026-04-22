import os
import re
from pathlib import Path
import sys

# Agregar el directorio src al path para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import RAW_DATA_DIR, KB_DIR, KB_FILE_PATH

def clean_markdown_content(text):
    """
    Aplica reglas heurísticas para limpiar el ruido del Markdown extraído.
    """
    # 1. Eliminar líneas que son claramente menús o navegación (case-insensitive)
    nav_patterns = [
        r"^.*tiendas.*$", r"^.*productos.*$", r"^.*ver más.*$", 
        r"^.*buscar.*$", r"^.*carrito.*$", r"^.*mi cuenta.*$",
        r"^.*facebook.*$", r"^.*instagram.*$", r"^.*linkedin.*$",
        r"^.*síguenos.*$", r"^.*derechos reservados.*$", r"^.*política de cookies.*$"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # Ignorar líneas vacías o muy cortas (ruido de iconos/enlaces)
        if not stripped_line or len(stripped_line) < 3:
            continue
            
        # Validar si la línea coincide con patrones de navegación/ruido
        if any(re.search(pattern, stripped_line, re.IGNORECASE) for pattern in nav_patterns):
            continue
            
        cleaned_lines.append(stripped_line)

    # Unir y normalizar espacios en blanco
    content = '\n'.join(cleaned_lines)
    content = re.sub(r'\n{3,}', '\n\n', content) # Máximo dos saltos de línea
    
    return content

def consolidate_knowledge_base():
    """
    Lee todos los archivos de data/raw, los limpia y los une en un solo archivo maestro.
    """
    print(f"\n[INFO] Iniciando Fase 2: Limpieza y Consolidación")
    
    if not RAW_DATA_DIR.exists():
        print(f"[ERROR] No se encontró la carpeta de origen: {RAW_DATA_DIR}")
        return

    KB_DIR.mkdir(parents=True, exist_ok=True)
    
    master_content = []
    master_content.append("# BASE DE CONOCIMIENTO: DOLLARCITY COLOMBIA\n")
    master_content.append("Este documento contiene información oficial sobre Suramérica Comercial S.A.S. (Dollarcity).\n")

    files_processed = 0
    
    for md_file in RAW_DATA_DIR.glob("*.md"):
        print(f"[STEP] Limpiando: {md_file.name}")
        
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                raw_text = f.read()
            
            clean_text = clean_markdown_content(raw_text)
            
            # Crear sección con trazabilidad
            source_name = md_file.stem.replace("dollarcity.com_", "").replace("_", " ").title()
            master_content.append(f"\n## SECCIÓN: {source_name}")
            master_content.append(f"Fuente original: {md_file.name}")
            master_content.append("-" * 30)
            master_content.append(clean_text)
            master_content.append("\n" + "="*50 + "\n")
            
            files_processed += 1
            
        except Exception as e:
            print(f"[ERROR] Fallo al procesar {md_file.name}: {e}")

    # Guardar el archivo consolidado
    with open(KB_FILE_PATH, "w", encoding="utf-8") as f:
        f.write('\n'.join(master_content))
        
    print(f"\n[OK] Fase 2 completada.")
    print(f"[INFO] Archivos procesados: {files_processed}")
    print(f"[INFO] Archivo maestro generado en: {KB_FILE_PATH}")

if __name__ == "__main__":
    consolidate_knowledge_base()