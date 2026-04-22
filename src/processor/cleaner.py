import re
import sys
from pathlib import Path

# Configuración de rutas
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import RAW_DATA_DIR, KB_DIR, KB_FILE_PATH

def deep_clean_markdown(text):
    """Elimina artefactos de markdown, links rotos e iconos."""
    # Eliminar imágenes y links de imágenes: ![alt](url) o [ ![alt](url) ](url)
    text = re.sub(r'\[?\s*!\[.*?\]\(.*?\)\s*\]?\(.*?\)?', '', text)
    # Eliminar links residuales quedando solo el texto: [Texto](url) -> Texto
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Eliminar carácteres de markdown huérfanos
    text = re.sub(r'[\[\]\(\)<>]', '', text)
    return text.strip()

def is_useful_faq(block):
    """Filtra bloques de FAQ irrelevantes o de otros países."""
    block_lower = block.lower()
    # Si el bloque niega algo que sabemos que en Colombia existe, lo descartamos
    blacklist = ["no contamos con factura electrónica para tu pais", "no tenemos disponible certificados o tarjetas de regalo"]
    if any(phrase in block_lower for phrase in blacklist):
        return False
    # Si menciona otros países y NO a Colombia, fuera
    countries = ["salvador", "guatemala", "peru", "mexico"]
    if any(c in block_lower for c in countries) and "colombia" not in block_lower:
        return False
    return True

def clean_source_content(content, filename):
    """Aplica lógica específica según la fuente."""
    # 1. Limpieza general de Markdown
    content = deep_clean_markdown(content)
    
    lines = content.split('\n')
    refined_lines = []
    
    # 2. Lógica por fuente
    if "quienes-somos" in filename:
        valid_headers = ["misión", "visión", "somos parte"]
        for line in lines:
            if any(h in line.lower() for h in valid_headers) or len(line.split()) > 10:
                refined_lines.append(line)
                
    elif "preguntas-frecuentes" in filename:
        # Deduplicación por bloques
        blocks = content.split('####')
        seen_questions = set()
        for b in blocks:
            if is_useful_faq(b):
                clean_b = b.strip()
                if clean_b[:50] not in seen_questions: # Deduplicar por inicio del texto
                    refined_lines.append("#### " + clean_b)
                    seen_questions.add(clean_b[:50])
                    
    elif "ubicaciones" in filename:
        for line in lines:
            # Solo conservar párrafos informativos, no de interfaz
            if "En Dollarcity" in line or "hogar" in line or "decoración" in line:
                refined_lines.append(line)

    return '\n'.join(refined_lines)

def run_semantic_curation():
    """Ejecuta la curación final estructurada."""
    print(f"\n[INFO] Iniciando Curación Semántica Final...")
    
    if not RAW_DATA_DIR.exists(): return
    KB_DIR.mkdir(parents=True, exist_ok=True)
    
    final_kb = ["# BASE DE CONOCIMIENTO CURADA - DOLLARCITY COLOMBIA\n"]
    
    # Procesar solo las fuentes core
    core_files = [f for f in RAW_DATA_DIR.glob("*.md") if any(x in f.name for x in ["quienes-somos", "preguntas-frecuentes", "ubicaciones"])]

    for file_path in core_files:
        print(f"[CURATING] {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        curated_text = clean_source_content(raw_content, file_path.name)
        
        if len(curated_text) > 50:
            final_kb.append(f"\n## SECCIÓN: {file_path.stem.split('_')[-1].upper()}")
            final_kb.append(curated_text)
            final_kb.append("\n" + "="*40)

    with open(KB_FILE_PATH, "w", encoding="utf-8") as f:
        f.write('\n'.join(final_kb))
    
    print(f"\n[SUCCESS] KB lista en: {KB_FILE_PATH}")

if __name__ == "__main__":
    run_semantic_curation()