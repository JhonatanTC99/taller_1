"""
Módulo de extracción y normalización de información corporativa de Dollarcity.

Este componente actúa como la capa de abstracción de datos relacionales estáticos (JSON DB)
para el backend conversacional. En el marco del Módulo 3, se implementa un patrón híbrido
que provee soporte retrospectivo para el motor de emparejamiento lineal basado en palabras
clave (Modo Legacy) e introduce una interfaz determinista tipada orientada a la ejecución
por Function Calling en arquitecturas agénticas basadas en grafos cíclicos (Modo Módulo 3).

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A (Integración Enterprise REST / Webhook)
"""

import json
from src.config.settings import SPECIFIC_QUESTION_PATH


def _load_corporate_data() -> dict:
    """
    Realiza la lectura e Ingestión física del archivo estructurado de datos corporativos.

    Returns:
        dict: Subconjunto de datos bajo la clave jerárquica 'informacion_corporativa'.

    Raises:
        FileNotFoundError: Si el archivo físico no coexiste en la ruta parametrizada.
        json.JSONDecodeError: Si el contenido del archivo viola la especificación sintáctica JSON.
        KeyError: Si la estructura raíz carece del nodo corporativo mandatorio.
    """
    with open(SPECIFIC_QUESTION_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
        return payload["informacion_corporativa"]


def get_corporate_data(tipo_dato: str) -> dict:
    """
    Interfaz de consulta estructurada optimizada para Function Calling (Módulo 3).
    Sanea inputs exógenos, resuelve homónimos y alias mediante normalización léxica,
    y encapsula la respuesta en un diccionario con metadatos explícitos de auditoría.

    Args:
        tipo_dato (str): Identificador clave de la entidad corporativa solicitada.

    Returns:
        dict: Objeto estandarizado que contiene el estado operacional, la clave resuelta,
              la respuesta formateada y la trazabilidad de la fuente.
    """
    if not tipo_dato:
        return {
            "status": "not_found",
            "tipo_dato": "",
            "answer": "Lo siento, no tengo ese dato exacto en mi registro corporativo.",
            "source_type": "json_db",
            "source": "data_corporativa.json"
        }

    # Normalización primaria de la cadena de entrada
    clean_key = tipo_dato.strip().lower()

    # Matriz unificada de homologación léxica (Alias Mapping)
    alias_mapping = {
        "nit": "nit",
        "nombre legal": "nit",
        "identificacion": "nit",
        "identificación": "nit",
        "telefono": "telefono",
        "teléfono": "telefono",
        "contacto": "telefono",
        "llamada": "telefono",
        "correo": "correo",
        "email": "correo",
        "escribir": "correo",
        "horario": "horario",
        "sede": "sede",
        "dirección": "sede",
        "direccion": "sede",
        "oficina": "sede",
        "donde queda": "sede",
        "ciudades": "ciudades",
        "donde hay": "ciudades",
        "sucursales": "ciudades",
        "devolucion": "devoluciones",
        "devolución": "devoluciones",
        "devoluciones": "devoluciones",
        "cambio": "devoluciones",
        "garantia": "devoluciones",
        "garantía": "devoluciones",
        "factura": "facturacion",
        "facturacion": "facturacion",
        "facturación": "facturacion",
        "dian": "facturacion",
        "redes": "redes",
        "sociales": "redes",
        "instagram": "redes",
        "facebook": "redes",
        "empleo": "empleo",
        "trabajo": "empleo",
        "vacante": "empleo",
        "hoja de vida": "empleo"
    }

    target_key = alias_mapping.get(clean_key, clean_key)

    # Ingestión segura con manejo específico de excepciones estructurales e infraestructurales
    try:
        data = _load_corporate_data()
    except FileNotFoundError:
        return {
            "status": "error",
            "tipo_dato": tipo_dato,
            "answer": "Error: El archivo de configuración no existe.",
            "source_type": "json_db",
            "source": "data_corporativa.json"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "tipo_dato": tipo_dato,
            "answer": "Error: El archivo tiene un formato inválido.",
            "source_type": "json_db",
            "source": "data_corporativa.json"
        }
    except KeyError:
        return {
            "status": "error",
            "tipo_dato": tipo_dato,
            "answer": "Error: La información corporativa no está configurada correctamente.",
            "source_type": "json_db",
            "source": "data_corporativa.json"
        }

    # Resolución determinista del pipeline de datos corporativos
    if target_key == "nit":
        answer = f"El NIT es {data['nit']} (Razón social: {data['nombre_legal']})."
    elif target_key == "telefono":
        answer = f"El teléfono de contacto es {data['telefono_contacto']}."
    elif target_key == "correo":
        answer = f"Clientes: {data['correo_servicio_cliente']} | Proveedores: {data['correo_proveedores']}."
    elif target_key == "horario":
        answer = f"Los horarios generales son: {data['horario_general']}."
    elif target_key == "sede":
        answer = f"La sede administrativa principal es en {data['sede_administrativa']}."
    elif target_key == "ciudades":
        answer = f"Ciudades con presencia: {', '.join(data['ciudades_presencia'])}."
    elif target_key == "devoluciones":
        answer = f"Política de cambios: {data['politica_devoluciones']}."
    elif target_key == "facturacion":
        answer = f"Portal de facturación: {data['facturacion_electronica']}."
    elif target_key == "redes":
        answer = f"Redes oficiales: {data['redes_sociales']}."
    elif target_key == "empleo":
        answer = f"Para aplicar a vacantes: {data['empleo_canal']}."
    else:
        return {
            "status": "not_found",
            "tipo_dato": tipo_dato,
            "answer": "Lo siento, no tengo ese dato exacto en mi registro corporativo.",
            "source_type": "json_db",
            "source": "data_corporativa.json"
        }

    return {
        "status": "success",
        "tipo_dato": target_key,
        "answer": answer,
        "source_type": "json_db",
        "source": "data_corporativa.json"
    }


def get_dollarcity_info(query: str) -> str:
    """
    Enrutador semántico síngrono preservado para compatibilidad retrospectiva (Modo Legacy).
    Analiza lenguaje libre a través de coincidencia heurística de firmas léxicas, delega el 
    procesamiento al nuevo motor estructurado v3 y extrae la respuesta plana.
    """
    q = query.lower()
    detected_tipo_dato = None

    if any(w in q for w in ["nit", "nombre legal", "identificación", "identificacion"]):
        detected_tipo_dato = "nit"
    elif any(w in q for w in ["teléfono", "contacto", "llamada", "telefono"]):
        detected_tipo_dato = "telefono"
    elif any(w in q for w in ["correo", "email", "escribir"]):
        detected_tipo_dato = "correo"
    elif "horario" in q:
        detected_tipo_dato = "horario"
    elif any(w in q for w in ["sede", "dirección", "oficina", "donde queda", "direccion"]):
        detected_tipo_dato = "sede"
    elif any(w in q for w in ["ciudades", "donde hay", "sucursales"]):
        detected_tipo_dato = "ciudades"
    elif any(w in q for w in ["devolución", "cambio", "garantía", "devolucion", "garantia", "devoluciones"]):
        detected_tipo_dato = "devoluciones"
    elif any(w in q for w in ["factura", "facturación", "dian", "facturacion"]):
        detected_tipo_dato = "facturacion"
    elif any(w in q for w in ["redes", "sociales", "instagram", "facebook"]):
        detected_tipo_dato = "redes"
    elif any(w in q for w in ["trabajo", "vacante", "empleo", "hoja de vida"]):
        detected_tipo_dato = "empleo"

    # Invocación puente al flujo estructurado determinista
    if detected_tipo_dato:
        result = get_corporate_data(detected_tipo_dato)
    else:
        result = get_corporate_data(query)

    return result["answer"]


# Definición explícita de símbolos exportables del módulo
__all__ = [
    "get_dollarcity_info",
    "get_corporate_data"
]