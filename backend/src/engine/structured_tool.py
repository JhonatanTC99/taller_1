"""
Módulo para consultar información corporativa de Dollarcity.
Este módulo carga datos desde un JSON y responde consultas del usuario.
"""
import json
from src.config.settings import SPECIFIC_QUESTION_PATH

def get_dollarcity_info(query: str) -> str:
    """Consulta información corporativa estructurada como NIT, teléfonos, sedes y horarios."""
    try:
        with open(SPECIFIC_QUESTION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)["informacion_corporativa"]
    except FileNotFoundError:
        return "Error: El archivo de configuración no existe."
    except json.JSONDecodeError:
        return "Error: El archivo tiene un formato inválido."
    except KeyError:
        return  "Error: La información corporativa no está configurada correctamente."

    q = query.lower()

    # Lógica de enrutamiento interno
    if any(w in q for w in ["nit", "nombre legal", "identificación"]):
        return f"El NIT es {data['nit']} (Razón social: {data['nombre_legal']})."
    
    elif any(w in q for w in ["teléfono", "contacto", "llamada"]):
        return f"El teléfono de contacto es {data['telefono_contacto']}."
    
    elif any(w in q for w in ["correo", "email", "escribir"]):
        return f"Clientes: {data['correo_servicio_cliente']} | Proveedores: {data['correo_proveedores']}."
    
    elif "horario" in q:
        return f"Los horarios generales son: {data['horario_general']}."
    
    elif any(w in q for w in ["sede", "dirección", "oficina", "donde queda"]):
        return f"La sede administrativa principal es en {data['sede_administrativa']}."
    
    elif any(w in q for w in ["ciudades", "donde hay", "sucursales"]):
        return f"Ciudades con presencia: {', '.join(data['ciudades_presencia'])}."
    
    elif any(w in q for w in ["devolución", "cambio", "garantía"]):
        return f"Política de cambios: {data['politica_devoluciones']}."
    
    elif any(w in q for w in ["factura", "facturación", "dian"]):
        return f"Portal de facturación: {data['facturacion_electronica']}."
    
    elif any(w in q for w in ["redes", "sociales", "instagram", "facebook"]):
        return f"Redes oficiales: {data['redes_sociales']}."
    
    elif any(w in q for w in ["trabajo", "vacante", "empleo", "hoja de vida"]):
        return f"Para aplicar a vacantes: {data['empleo_canal']}."
    
    else:
        return "Lo siento, no tengo ese dato exacto en mi registro corporativo."