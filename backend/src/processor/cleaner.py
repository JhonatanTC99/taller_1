import re
import hashlib
import shutil
import os
import time
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Configuración del proyecto
from src.config.settings import (
    RAW_DATA_DIR, KB_DIR, KB_FILE_PATH, 
    CHROMA_PATH, EMBEDDING_MODEL_NAME
)

RELEVANCE_KEYWORDS = ["dollarcity", "dólar city", "suramerica comercial", "dollarama", "baldocchi", "tiendas", "expansión", "colombia"]
ERROR_SIGNATURES = ["crawl4ai error", "invalid expression", "too many requests", "captcha", "blocked by"]

TRASH_HEADERS = [
    "últimas noticias", "en video", "enlaces patrocinados", "enlaces promovidos", 
    "también te puede interesar", "te puede gustar", "sigue leyendo", "más de economía", 
    "programas", "comentarios", "deja tu comentario", "artículos relacionados", 
    "sugerencias", "boletines", "newsletter", "lea también", "temas relacionados"
]

UI_NOISE = [
    "cerrar", "entiendo", "deshacer", "aceptar", "compartir", "leer más", "síguenos", 
    "suscríbete", "newsletter", "publicidad", "anuncio", "cookies", "derechos reservados",
    "regístrate", "iniciar sesión", "ver nota completa", "descarga la app"
]

def get_block_hash(text: str) -> str:
    clean_text = re.sub(r'\s+', '', text).lower()
    return hashlib.md5(clean_text.encode()).hexdigest()

def clean_noise(text: str, url: str, stats: dict) -> str:
    is_official = "dollarcity.com" in url.lower() or "pdf" in url.lower()
    is_computrabajo = "computrabajo.com" in url.lower()
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        l_original = line.strip()
        l_lower = l_original.lower()

        if any(trash in l_lower for trash in TRASH_HEADERS):
            stats["bloques_cortados"] += 1
            break

        if any(noise == l_lower for noise in UI_NOISE) or len(l_original) < 3:
            stats["lineas_eliminadas"] += 1
            continue

        if is_computrabajo:
            if any(k in l_lower for k in ["dgnet", "ver más ofertas", "filtros", "denunciar", "puntuación", "hace ", "contraseña"]):
                stats["lineas_eliminadas"] += 1
                continue

        if not is_official:
            if not any(k in l_lower for k in RELEVANCE_KEYWORDS):
                stats["lineas_eliminadas"] += 1
                continue

        cleaned_lines.append(l_original)
    return '\n'.join(cleaned_lines)

def get_semantic_section(url: str, content: str) -> str:
    u, t = url.lower(), content.lower()
    if "dollarcity.com" in u:
        if any(k in u for k in ["preguntas", "faq", "ubicaciones"]): return "PREGUNTAS FRECUENTES Y ATENCIÓN AL CLIENTE"
        if any(k in u for k in ["privacidad", "tyc", "legal"]): return "POLÍTICAS, PRIVACIDAD Y DATOS PERSONALES"
        if any(k in u for k in ["equipo", "oportunidades", "talento"]): return "TALENTO HUMANO Y EMPLEO"
        if any(k in u for k in ["quienes", "mision"]): return "IDENTIDAD CORPORATIVA"
        return "FUENTES OFICIALES"
    if any(k in t for k in ["historia", "fundó", "expansión"]): return "HISTORIA, EXPANSIÓN Y CONTEXTO EMPRESARIAL"
    return "PRODUCTOS Y SERVICIOS"

def build_vector_store():
    """Toma el Markdown curado e indexa en Chroma manejando bloqueos de Windows."""
    print(f"\n[VECTOR] 🚀 Iniciando indexación en Chroma...")
    
    if not KB_FILE_PATH.exists():
        print(f"[ERROR] No se encontró el archivo KB en {KB_FILE_PATH}")
        return

    # 1. Limpieza física de Chroma (Wipe) con manejo de errores de Windows
    if CHROMA_PATH.exists():
        print(f"[VECTOR] Intentando eliminar índice previo en {CHROMA_PATH}...")
        try:
            # Intento de borrado
            shutil.rmtree(CHROMA_PATH)
            time.sleep(1) # Pequeña pausa para que el OS libere el descriptor
        except PermissionError:
            print("\n" + "!"*60)
            print("[CRITICAL ERROR] Windows bloqueó el acceso a la base de datos.")
            print("ACCIONES REQUERIDAS:")
            print("1. Cierra la terminal donde esté corriendo el servidor FastAPI.")
            print("2. Ejecuta en PowerShell: Stop-Process -Name python -Force")
            print("3. Vuelve a ejecutar: uv run python main.py --clean")
            print("!"*60 + "\n")
            return # Detener la ejecución, no se puede indexar sobre una DB bloqueada

    # 2. Leer el conocimiento base
    content = KB_FILE_PATH.read_text(encoding="utf-8")
    
    # 3. Fragmentación
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n---", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_text(content)
    
    if not chunks:
        raise ValueError("[ERROR] No se generaron chunks. El archivo KB está vacío o mal formateado.")

    documents = [
        Document(
            page_content=chunk, 
            metadata={"source": "dollarcity_context.md", "chunk_index": i}
        ) for i, chunk in enumerate(chunks)
    ]

    # 4. Inicializar Embeddings e Indexar
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_PATH)
    )
    
    # 5. Validación de persistencia
    final_count = vector_db._collection.count()
    if final_count == 0:
         raise RuntimeError("[ERROR] La colección de Chroma se creó pero está vacía.")
         
    print(f"[SUCCESS] Chroma poblado con {final_count} fragmentos.")

def build_dynamic_kb():
    """Pipeline completo de curación e indexación."""
    print(f"\n[INFO] 🛠️ Iniciando Curación Estricta de KB...")
    if not RAW_DATA_DIR.exists(): 
        print("[ERROR] No existe RAW_DATA_DIR")
        return

    sections = {
        "IDENTIDAD CORPORATIVA": [],
        "PREGUNTAS FRECUENTES Y ATENCIÓN AL CLIENTE": [],
        "POLÍTICAS, PRIVACIDAD Y DATOS PERSONALES": [],
        "TALENTO HUMANO Y EMPLEO": [],
        "FUENTES OFICIALES": [],
        "PRODUCTOS Y SERVICIOS": [],
        "HISTORIA, EXPANSIÓN Y CONTEXTO EMPRESARIAL": []
    }
    
    stats = {"leidos": 0, "procesados": 0, "descartados": 0, "lineas_eliminadas": 0, "bloques_cortados": 0, "duplicados_bloque": 0, "fuentes_lens": {}}
    seen_blocks = set()
    talla_previa_est = 0

    all_files = sorted(RAW_DATA_DIR.glob("*.md"))
    
    for file_path in all_files:
        stats["leidos"] += 1
        raw_text = file_path.read_text(encoding="utf-8")
        talla_previa_est += len(raw_text)
        
        if any(sig in raw_text.lower() for sig in ERROR_SIGNATURES):
            stats["descartados"] += 1
            continue

        try:
            parts = raw_text.split('\n')
            url = parts[0].replace("SOURCE_URL: ", "").strip()
            body = clean_noise('\n'.join(parts[1:]), url, stats)
            
            content_blocks = []
            for block in body.split('\n\n'):
                block = block.strip()
                if not block: continue
                
                if len(block) > 200:
                    b_hash = get_block_hash(block)
                    if b_hash in seen_blocks:
                        stats["duplicados_bloque"] += 1
                        continue
                    seen_blocks.add(b_hash)
                content_blocks.append(block)

            final_content = '\n\n'.join(content_blocks)

            if len(final_content) > 150:
                sec_name = get_semantic_section(url, final_content)
                sections[sec_name].append(f"### FUENTE: {url}\n{final_content}\n")
                stats["procesados"] += 1
            else:
                stats["descartados"] += 1
        except:
            stats["descartados"] += 1

    # Construcción del Markdown
    final_md = ["# KB DOLLARCITY COLOMBIA\n", "> Contexto Curado v2.2 - Windows Locking Fix\n"]
    for name, entries in sections.items():
        if entries:
            final_md.append(f"## {name}")
            final_md.extend(entries)
            final_md.append("\n---\n")

    KB_DIR.mkdir(parents=True, exist_ok=True)
    KB_FILE_PATH.write_text("\n".join(final_md), encoding="utf-8")

    print(f"--- 📊 REPORTE DE CURACIÓN ---")
    print(f"📄 Archivos procesados: {stats['procesados']}")
    print(f"📉 Reducción: {talla_previa_est/1024:.1f}KB -> {KB_FILE_PATH.stat().st_size/1024:.1f}KB")

    # Disparar indexación
    build_vector_store()

if __name__ == "__main__":
    build_dynamic_kb()