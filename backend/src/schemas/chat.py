"""
Módulo de definición de esquemas de datos corporativos para el sistema conversacional.

Este componente centraliza los contratos de datos (Data Transfer Objects) basados en
Pydantic v2 para gestionar la comunicación síncrona y agéntica del Módulo 3. Define 
los esquemas de validación estrictos de entrada y salida para integraciones multiproveedor 
(N8N, WhatsApp, Telegram, Web), asegurando la inmutabilidad y la sanidad de los tipos de 
datos en el pipeline de ejecución.

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A (FastAPI + LangChain Backend Core)
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator


class ChannelChatRequest(BaseModel):
    """
    Contrato de entrada unificado para los canales de mensajería productivos (Módulo 3).
    Aplica políticas de limpieza de datos antes de transferir el payload al orquestador agéntico.
    """
    user_id: str = Field(
        ...,
        description="Identificador persistente y unificado del usuario o sesión en el canal de origen."
    )
    message: str = Field(
        ...,
        description="Contenido textual del mensaje emitido por el usuario final."
    )
    channel: str = Field(
        default="web",
        description="Canal originario de la petición (ej. web, n8n, whatsapp, telegram, api)."
    )
    model: str | None = Field(
        default=None,
        description="Identificador opcional del modelo de lenguaje solicitado para preservar compatibilidad."
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Estructura flexible para almacenar metadatos específicos del canal (message_id, timestamps)."
    )

    @field_validator("user_id", mode="before")
    @classmethod
    def validate_and_clean_user_id(cls, value: Any) -> str:
        """Remueve espacios en blanco exógenos y valida que el identificador no sea nulo o vacío."""
        if value is None:
            raise ValueError("El campo 'user_id' es obligatorio y no puede ser nulo.")
        cleaned_value = str(value).strip()
        if not cleaned_value:
            raise ValueError("El campo 'user_id' no puede consistir únicamente en espacios en blanco o estar vacío.")
        return cleaned_value

    @field_validator("message", mode="before")
    @classmethod
    def validate_and_clean_message(cls, value: Any) -> str:
        """Limpia el contenido del mensaje y restringe strings vacíos."""
        if value is None:
            raise ValueError("El campo 'message' es obligatorio y no puede ser nulo.")
        cleaned_value = str(value).strip()
        if not cleaned_value:
            raise ValueError("El campo 'message' no puede consistir únicamente en espacios en blanco o estar vacío.")
        return cleaned_value

    @field_validator("channel", mode="before")
    @classmethod
    def normalize_channel(cls, value: Any) -> str:
        """Normaliza el canal a minúsculas y asigna el valor por defecto ante vacíos."""
        if value is None:
            return "web"
        cleaned_channel = str(value).strip().lower()
        if not cleaned_channel:
            return "web"
        return cleaned_channel


class ChannelChatResponse(BaseModel):
    """
    Contrato de salida unificado para las respuestas del sistema agéntico (Módulo 3).
    Estructura la respuesta final junto con metadatos de observabilidad y diagnóstico RAG.
    """
    content: str = Field(
        ...,
        description="Texto final generado por el agente conversacional para ser devuelto al usuario."
    )
    status: str = Field(
        default="success",
        description="Estado operativo de la resolución de la petición (success, error, warning)."
    )
    model: str | None = Field(
        default=None,
        description="Nombre o identificador técnico del LLM utilizado en la inferencia."
    )
    session_id: str = Field(
        ...,
        description="Mapeo directo del identificador de conversación utilizado por el motor de persistencia."
    )
    channel: str = Field(
        default="web",
        description="Confirmación del canal por el cual se transmite la respuesta."
    )
    tool_used: str | None = Field(
        default=None,
        description="Identificador de la herramienta de Function Calling invocada durante la ejecución."
    )
    source_type: str | None = Field(
        default=None,
        description="Clasificación de la fuente de la respuesta (json_db, vector_db, rule, agent, error)."
    )
    docs_count: int | None = Field(
        default=None,
        description="Cantidad de fragmentos de conocimiento recuperados mediante el motor RAG."
    )
    timing_ms: dict[str, float] | None = Field(
        default=None,
        description="Métricas desagregadas de latencia expresadas en milisegundos."
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Estructura abierta para telemetría adicional o cargas útiles de proveedores externos."
    )


class LegacyChatRequest(BaseModel):
    """
    Esquema de datos preservado para dar soporte al flujo lineal preexistente (Módulo 2).
    Garantiza la inmutabilidad operacional del endpoint legacy /api/chat.
    """
    question: str = Field(
        ...,
        description="Pregunta original enviada por la interfaz de usuario legacy."
    )
    model: str | None = Field(
        default=None,
        description="Especificación opcional del modelo de lenguaje síncrono."
    )

    @field_validator("question", mode="before")
    @classmethod
    def clean_legacy_question(cls, value: Any) -> str:
        """Aplica saneamiento básico y restringe entradas nulas o vacías en el flujo heredado."""
        if value is None:
            raise ValueError("El campo 'question' es mandatorio.")
        cleaned_question = str(value).strip()
        if not cleaned_question:
            raise ValueError("El campo 'question' no puede estar vacío.")
        return cleaned_question


class ErrorResponse(BaseModel):
    """
    Contrato estandarizado para la notificación de excepciones en la capa de API REST.
    Permite el manejo estructurado de fallos en llamadas asíncronas de webhooks externos.
    """
    content: str = Field(
        ...,
        description="Mensaje descriptivo del error adaptado para el usuario final o canal."
    )
    status: str = Field(
        default="error",
        description="Indicador fijo de estado anómalo en el procesamiento."
    )
    detail: str | None = Field(
        default=None,
        description="Trazado técnico del error o código interno de excepción para debugging."
    )
    session_id: str | None = Field(
        default=None,
        description="Identificador de la sesión afectada si logró determinarse en el ciclo de vida."
    )
    channel: str | None = Field(
        default=None,
        description="Canal que originó la petición fallida."
    )


# Declaración explícita de símbolos exportables del módulo
__all__ = [
    "ChannelChatRequest",
    "ChannelChatResponse",
    "LegacyChatRequest",
    "ErrorResponse"
]