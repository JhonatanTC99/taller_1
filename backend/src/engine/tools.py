"""
Módulo de definición de herramientas estructuradas para el orquestador agéntico.

Este componente expone las interfaces semánticas unificadas (Tools) compatibles con 
el framework LangChain y los mecanismos de Function Calling de los LLM del Módulo 3.
Cada herramienta integra esquemas de validación estrictos basados en Pydantic v2,
permitiendo al agente conversacional interactuar de forma segura y determinística 
con bases de conocimiento JSON locales, ejecutar consultas de recuperación semántica (RAG)
en el vector store persistente, aplicar políticas de fronteras de dominio y preparar
hooks interceptables por procesos Human-in-the-Loop (HITL).

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A: LangChain / LangGraph Tools para Function Calling
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool
from src.engine.structured_tool import get_corporate_data
from src.engine.rag_service import retrieve_knowledge


# =====================================================================
# SECCIÓN I: ESQUEMAS DE VALIDACIÓN PYDANTIC (Input Schemas)
# =====================================================================

class CorporateDataInput(BaseModel):
    """Esquema de entrada para la consulta estructurada de datos institucionales de la compañía."""
    tipo_dato: str = Field(
        ...,
        description=(
            "Identificador del dato corporativo requerido. Debe corresponder estrictamente a "
            "una de las siguientes llaves indexadas: 'nit', 'telefono', 'correo', 'horario', "
            "'sede', 'ciudades', 'devoluciones', 'facturacion', 'redes', 'empleo'."
        )
    )


class RagKnowledgeInput(BaseModel):
    """Esquema de entrada para la búsqueda semántica en la base de conocimiento indexada (RAG)."""
    query: str = Field(
        ...,
        description="Pregunta o necesidad informativa del usuario que requiere búsqueda semántica en la base de conocimiento."
    )
    k: int | None = Field(
        default=None,
        description="Número opcional de fragmentos de conocimiento (top-K) a recuperar del vector store."
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_and_clean_query(cls, value: Any) -> str:
        """Garantiza que la consulta no sea nula, remueve espacios y restringe cadenas vacías."""
        if value is None:
            raise ValueError("El campo 'query' no puede ser nulo o indefinido.")
        cleaned_value = str(value).strip()
        if not cleaned_value:
            raise ValueError("El campo 'query' es mandatorio y no puede estar vacío.")
        return cleaned_value

    @field_validator("k")
    @classmethod
    def validate_k(cls, value: int | None) -> int | None:
        """Valida que el parámetro de vecindad top-K sea un entero estrictamente positivo."""
        if value is not None and value <= 0:
            raise ValueError("El número de fragmentos 'k' debe ser estrictamente mayor que cero.")
        return value


class OutOfDomainInput(BaseModel):
    """Esquema de entrada para el control y desvío de tópicos ajenos al ecosistema operativo."""
    motivo: str | None = Field(
        default=None,
        description="Descripción opcional o justificación semántica del desvío de dominio detectado."
    )


class LeadInput(BaseModel):
    """Esquema de entrada para la pre-ingestión de contactos y prospectos de negocio corporativos."""
    nombre: str | None = Field(
        default=None, 
        description="Nombre completo o razón social proporcionada por el prospecto interesado."
    )
    telefono: str | None = Field(
        default=None, 
        description="Número de teléfono celular o canal telefónico de contacto directo."
    )
    interes: str = Field(
        ..., 
        description="Categoría o vector de interés específico (ej. 'empleo', 'proveedores', 'contacto_comercial')."
    )


# =====================================================================
# SECCIÓN II: IMPLEMENTACIÓN DE HERRAMIENTAS (LangChain Tools)
# =====================================================================

@tool(args_schema=CorporateDataInput)
def consultar_dato_corporativo(tipo_dato: str) -> dict[str, Any]:
    """
    Consulta información corporativa y datos estáticos oficiales de Dollarcity.
    
    Invoque esta herramienta únicamente cuando el usuario haga preguntas explícitas sobre
    parámetros institucionales estables de la empresa como: NIT, número legal, teléfono 
    de soporte, correos de atención a clientes o proveedores, horarios generales de tiendas, 
    dirección de la sede administrativa principal, ciudades con cobertura comercial, 
    políticas de devoluciones y cambios de mercancía, acceso al portal de facturación 
    electrónica, redes sociales del corporativo o canales oficiales para aplicar a empleos.
    """
    return get_corporate_data(tipo_dato)


@tool(args_schema=RagKnowledgeInput)
def consultar_base_conocimiento_rag(query: str, k: int | None = None) -> dict[str, Any]:
    """
    Ejecuta una búsqueda semántica detallada en la base de conocimiento indexada de Dollarcity.
    
    Invoque esta herramienta de forma prioritaria ante preguntas abiertas, históricas, conceptuales, 
    contextuales o documentales sobre Dollarcity. Esto incluye consultas sobre su origen y trayectoria, 
    estrategias de expansión regional, modelo de negocio de bajo costo (hard discount), noticias de la 
    compañía, reportes empresariales, cultura corporativa o cualquier información pública detallada 
    que no consista en un dato institucional único o estático.
    """
    # Delegación de la búsqueda semántica al servicio RAG desacoplado
    result = retrieve_knowledge(query=query, k=k)
    
    # Construcción estructurada del payload respetando los contratos de auditoría v3
    return {
        "status": result.get("status", "success"),
        "answer": (
            "Se recuperaron fragmentos relevantes de la base de conocimiento corporativa. "
            "Use el campo context para formular la respuesta final."
        ),
        "source_type": result.get("source_type", "vector_db"),
        "docs_count": result.get("docs_count", 0),
        "retrieved_chunks": result.get("retrieved_chunks", []),
        "context_length": result.get("context_length", 0),
        "context": result.get("context", ""),
        "tool_used": "consultar_base_conocimiento_rag"
    }


@tool(args_schema=OutOfDomainInput)
def responder_fuera_de_dominio(motivo: str | None = None) -> dict[str, Any]:
    """
    Aplica la política de contención semántica ante peticiones que exceden el dominio operativo.
    
    Invoque esta herramienta de forma mandatoria cuando el usuario formule preguntas que no tengan 
    vínculo alguno con Dollarcity, sus tiendas o su operación (tales como consultas del clima, 
    debates políticos globales, resolución de ecuaciones matemáticas exógenas, recetas gastronómicas, 
    solicitud de chistes de propósito general o soporte técnico sobre productos ajenos a la marca).
    """
    return {
        "status": "success",
        "answer": (
            "Lo sentimos, como asistente académico de información corporativa sobre Dollarcity, mi alcance está restringido "
            "a resolver dudas sobre nuestra información institucional, sucursales, canales de contacto, "
            "horarios, oportunidades de empleo o directrices públicas de la compañía. Por favor, reformula "
            "tu consulta orientándola hacia alguno de nuestros servicios o presencia comercial."
        ),
        "source_type": "policy",
        "tool_used": "responder_fuera_de_dominio"
    }


@tool(args_schema=LeadInput)
def registrar_lead_interesado(nombre: str | None = None, telefono: str | None = None, interes: str = "") -> dict[str, Any]:
    """
    Pre-registra el interés de un usuario para postularse a vacantes laborales o alianzas de proveedores.
    
    Invoque esta herramienta inmediatamente cuando el usuario exprese la intención explícita de 
    querer trabajar en Dollarcity, enviar su hoja de vida/currículum, ofrecer productos para ser 
    proveedor de las tiendas o registrar datos personales con fines comerciales o de contratación.
    Esta acción suspende el pipeline automático y activa una solicitud pendiente de auditoría humana.
    """
    return {
        "status": "pending_human_review",
        "answer": (
            "Hemos recibido tu solicitud de pre-registro de interés correctamente. Para cumplir con las "
            "políticas de seguridad de datos de Dollarcity, este proceso requiere una verificación manual. "
            "La solicitud ha sido enviada al módulo de revisión humana (Human-in-the-Loop Middleware) y "
            "quedará en estado 'Pendiente' hasta que un administrador valide y apruebe el registro."
        ),
        "source_type": "human_in_the_loop",
        "tool_used": "registrar_lead_interesado"
    }


# =====================================================================
# SECCIÓN III: FACTORY / EXPORTACIÓN DEL TOOLSET
# =====================================================================

def get_agent_tools() -> list[Any]:
    """
    Compila y expone el listado indexado de herramientas estructuradas de producción.
    Diseñado para alimentar el nodo de herramientas en arquitecturas de grafos de LangGraph.

    Returns:
        list: Colección de herramientas LangChain decoradas listas para Function Calling.
    """
    return [
        consultar_dato_corporativo,
        consultar_base_conocimiento_rag,
        responder_fuera_de_dominio,
        registrar_lead_interesado
    ]


# Definición formal de los símbolos exportables del módulo
__all__ = [
    "CorporateDataInput",
    "RagKnowledgeInput",
    "OutOfDomainInput",
    "LeadInput",
    "consultar_dato_corporativo",
    "consultar_base_conocimiento_rag",
    "responder_fuera_de_dominio",
    "registrar_lead_interesado",
    "get_agent_tools"
]