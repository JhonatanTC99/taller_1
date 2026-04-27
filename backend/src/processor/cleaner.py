import re
from pathlib import Path
from src.config.settings import RAW_DATA_DIR, KB_DIR, KB_FILE_PATH

# 1. ARCHIVOS FUENTE
ALLOWED_FILES = {
    "quienes-somos.md",
    "preguntas-frecuentes.md",
    "ubicaciones.md",
    "nuestro-equipo.md",
    "oportunidades.md",
    "programas-de-talento.md",
}

def extract_signals() -> set[str]:
    """Recorre el raw buscando palabras clave (señales) para activar hechos."""
    signals = set()
    if not RAW_DATA_DIR.exists(): return signals

    for file_path in RAW_DATA_DIR.glob("*.md"):
        if file_path.name not in ALLOWED_FILES: continue
        
        content = file_path.read_text(encoding="utf-8").lower()
        
        # Diccionario de detección de señales (Pattern Matching)
        patterns = {
            "has_mission": ["misión", "vision", "experiencia de compra"],
            "has_nequi": ["nequi"],
            "has_gift_card": ["tarjeta de regalo", "gift card"],
            "has_returns": ["cambio", "devolución", "48 horas", "ticket"],
            "has_einvoice": ["factura electrónica"],
            "has_pets": ["mascota", "pet friendly"],
            "has_employment": ["vacante", "trabaja con nosotros", "linkedin"],
            "has_recruitment_fraud": ["no solicita pago", "cobro por proceso"],
            "has_online_sales": ["venta en línea", "domicilio", "compra por internet"],
            "has_inventory": ["sujeto al flujo", "disponibilidad de tienda"],
            "has_products": ["hogar", "cocina", "decoración", "temporada"],
            "has_franchise": ["franquicia"],
            "has_locations": ["ubicaciones", "horarios", "encuéntranos"]
        }

        for signal, keywords in patterns.items():
            if any(kw in content for kw in keywords):
                # Filtro geográfico estricto para señales de empleo/países
                if signal == "has_employment" and ("tecoloco" in content and "colombia" not in content):
                    continue
                signals.add(signal)
                
    return signals

def build_facts(signals: set[str]) -> dict[str, list[str]]:
    """Construye los hechos canónicos basados en las señales detectadas."""
    facts_db = {
        "HISTORIA Y VALORES": [],
        "PRODUCTOS Y SERVICIOS": [],
        "CAMBIOS Y GARANTÍAS": [],
        "PAGOS Y FACTURACIÓN": [],
        "EMPLEO Y TALENTO": [],
        "POLÍTICAS": []
    }

    # Inyección de Hechos Canónicos (Evidencia -> Hecho)
    if "has_mission" in signals:
        facts_db["HISTORIA Y VALORES"].append("Misión: Agregar valor a los clientes ofreciendo una experiencia de compra única con productos de calidad a excelentes precios.")
        facts_db["HISTORIA Y VALORES"].append("Dollarcity nació en 2009 y busca expandirse por toda Latinoamérica con un equipo comprometido.")

    if "has_products" in signals:
        facts_db["PRODUCTOS Y SERVICIOS"].append("Categorías disponibles: Hogar, artículos de primera necesidad, decoración, cocina, oficina, mascotas, jardinería y temporada.")
    
    if "has_online_sales" in signals:
        facts_db["PRODUCTOS Y SERVICIOS"].append("Dollarcity no cuenta con venta en línea ni servicio de domicilio.")
        
    if "has_inventory" in signals:
        facts_db["PRODUCTOS Y SERVICIOS"].append("El inventario y disponibilidad de productos están sujetos al flujo de venta de cada tienda física.")

    if "has_returns" in signals:
        facts_db["CAMBIOS Y GARANTÍAS"].append("Cambios y devoluciones: Deben gestionarse en un máximo de 48 horas tras la compra.")
        facts_db["CAMBIOS Y GARANTÍAS"].append("Requisito obligatorio: Presentar el ticket o factura original de compra.")
        facts_db["CAMBIOS Y GARANTÍAS"].append("Lugar: Los cambios se realizan exclusivamente en la sucursal donde se efectuó la compra.")

    if "has_nequi" in signals:
        facts_db["PAGOS Y FACTURACIÓN"].append("Se acepta Nequi únicamente mediante tarjeta débito física; no se aceptan pagos por código QR.")

    if "has_gift_card" in signals:
        facts_db["PAGOS Y FACTURACIÓN"].append("Tarjetas de regalo: Disponibles para compra en tiendas físicas.")
        facts_db["PAGOS Y FACTURACIÓN"].append("Condiciones de Tarjeta Regalo: No tienen fecha de caducidad y permiten pagos parciales.")
        facts_db["PAGOS Y FACTURACIÓN"].append("Seguridad: El saldo se consulta en tienda; en caso de pérdida o robo, los fondos no son recuperables.")
        facts_db["PAGOS Y FACTURACIÓN"].append("Restricción: La compra de una tarjeta de regalo no genera factura electrónica (esta se emite al comprar mercancía con ella).")

    if "has_einvoice" in signals:
        facts_db["PAGOS Y FACTURACIÓN"].append("Facturación Electrónica: Se solicita completando el formulario en el sitio web oficial y llega por correo electrónico.")

    if "has_employment" in signals:
        facts_db["EMPLEO Y TALENTO"].append("Canales oficiales: Las vacantes se publican exclusivamente en LinkedIn y Computrabajo Colombia.")
        facts_db["EMPLEO Y TALENTO"].append("Programas especiales: Disponibilidad de 'Trainee Program' para recién graduados de maestría.")

    if "has_recruitment_fraud" in signals:
        facts_db["EMPLEO Y TALENTO"].append("Seguridad laboral: Dollarcity NO solicita pagos de ningún tipo en sus procesos de selección o contratación.")

    if "has_pets" in signals:
        facts_db["POLÍTICAS"].append("Mascotas: No se permite el ingreso de mascotas a las tiendas debido a protocolos de licencia de alimentos.")

    if "has_franchise" in signals:
        facts_db["POLÍTICAS"].append("Franquicias: El modelo de negocio actual no contempla la concesión de franquicias.")

    if "has_locations" in signals:
        facts_db["POLÍTICAS"].append("Ubicaciones y Horarios: Deben consultarse directamente en la sección de 'Ubicaciones' del sitio web oficial.")

    return facts_db

def build_knowledge_base():
    """Orquesta el pipeline de síntesis de conocimiento."""
    print("Analizando señales en archivos raw...")
    signals = extract_signals()
    
    print("Construyendo hechos canónicos...")
    facts_sections = build_facts(signals)
    
    KB_DIR.mkdir(parents=True, exist_ok=True)
    
    output = [
        "# BASE DE CONOCIMIENTO - DOLLARCITY COLOMBIA",
        "Regla: Responde únicamente basándote en estos hechos validados.",
        ""
    ]

    for section, facts in facts_sections.items():
        if facts:
            output.append(f"## {section}")
            for fact in facts:
                output.append(f"- {fact}")
            output.append("")

    KB_FILE_PATH.write_text("\n".join(output), encoding="utf-8")
    print(f"KB Generada exitosamente en: {KB_FILE_PATH}")

def run_semantic_curation():
    build_knowledge_base()

if __name__ == "__main__":
    run_semantic_curation()