import re
import hashlib
from pathlib import Path
from src.config.settings import RAW_DATA_DIR, KB_DIR, KB_FILE_PATH

# --- CONFIGURACIÓN DE CURACIÓN ---
RELEVANCE_KEYWORDS = ["dollarcity", "dólar city", "suramerica comercial", "dollarama", "baldocchi", "tiendas", "expansión", "colombia"]
ERROR_SIGNATURES = ["crawl4ai error", "invalid expression", "too many requests", "captcha", "blocked by"]

# Encabezados que marcan el FIN del contenido útil en prensa
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
    """Genera un hash único para un bloque de texto para detectar duplicados."""
    clean_text = re.sub(r'\s+', '', text).lower()
    return hashlib.md5(clean_text.encode()).hexdigest()

def clean_noise(text: str, url: str, stats: dict) -> str:
    """Limpia ruido, corta bloques basura y filtra por relevancia."""
    is_official = "dollarcity.com" in url.lower() or "pdf" in url.lower()
    is_computrabajo = "computrabajo.com" in url.lower()
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        l_original = line.strip()
        l_lower = l_original.lower()

        # 1. STOP & CUT: Si llegamos a un encabezado de basura, terminamos esta fuente
        if any(trash in l_lower for trash in TRASH_HEADERS):
            stats["bloques_cortados"] += 1
            break

        # 2. Filtro UI Noise
        if any(noise == l_lower for noise in UI_NOISE) or len(l_original) < 3:
            stats["lineas_eliminadas"] += 1
            continue

        # 3. Limpieza específica Computrabajo
        if is_computrabajo:
            # Eliminar basura legal de la plataforma DGNET y formularios
            if any(k in l_lower for k in ["dgnet", "ver más ofertas", "filtros", "denunciar", "puntuación", "hace ", "contraseña"]):
                stats["lineas_eliminadas"] += 1
                continue

        # 4. Filtro de relevancia para fuentes externas
        if not is_official:
            # Solo guardamos párrafos que mencionen palabras clave
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

def build_dynamic_kb():
    print(f"\n[INFO] 🛠️ Iniciando Curación Estricta de KB...")
    if not RAW_DATA_DIR.exists(): return

    sections = {
        "FUENTES OFICIALES": [], "IDENTIDAD CORPORATIVA": [], "PRODUCTOS Y SERVICIOS": [],
        "PREGUNTAS FRECUENTES Y ATENCIÓN AL CLIENTE": [], "TALENTO HUMANO Y EMPLEO": [],
        "POLÍTICAS, PRIVACIDAD Y DATOS PERSONALES": [], "HISTORIA, EXPANSIÓN Y CONTEXTO EMPRESARIAL": []
    }
    
    stats = {
        "leidos": 0, "procesados": 0, "descartados": 0, 
        "lineas_eliminadas": 0, "bloques_cortados": 0, "duplicados_bloque": 0,
        "fuentes_lens": {}
    }
    
    seen_blocks = set() # Deduplicación global de bloques grandes
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
            
            # Deduplicación por bloques (>300 chars)
            content_blocks = []
            for block in body.split('\n\n'):
                block = block.strip()
                if not block: continue
                
                if len(block) > 300:
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
                stats["fuentes_lens"][url] = len(final_content)
            else:
                stats["descartados"] += 1

        except:
            stats["descartados"] += 1

    # Construcción final
    final_md = ["# KB DOLLARCITY COLOMBIA\n", "> Contexto Curado v2 - Optimizado para gemma3:1b\n"]
    for name, entries in sections.items():
        if entries:
            final_md.append(f"## {name}")
            final_md.extend(entries)
            final_md.append("\n---\n")

    KB_DIR.mkdir(parents=True, exist_ok=True)
    KB_FILE_PATH.write_text("\n".join(final_md), encoding="utf-8")

    # REPORTE FINAL
    print(f"\n--- 📊 REPORTE DE OPTIMIZACIÓN ---")
    print(f"📄 Archivos (leídos/procesados): {stats['leidos']} / {stats['procesados']}")
    print(f"❌ Archivos descartados:        {stats['descartados']}")
    print(f"🧹 Líneas eliminadas:           {stats['lineas_eliminadas']}")
    print(f"✂️  Fuentes cortadas (Trash):     {stats['bloques_cortados']}")
    print(f"👯 Bloques duplicados borrados: {stats['duplicados_bloque']}")
    print(f"📉 Reducción de tamaño:         {talla_previa_est/1024:.1f}KB -> {KB_FILE_PATH.stat().st_size/1024:.1f}KB")
    
    print(f"\n🔝 TOP FUENTES:")
    for url, size in sorted(stats["fuentes_lens"].items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"   - {size} chars | {url[:50]}...")

if __name__ == "__main__":
    build_dynamic_kb()