"""
Módulo de servicio centralizado para la recuperación semántica (RAG) de Dollarcity.

Este componente abstrae las operaciones de consulta vectorial e indexación semántica
de la base de conocimiento utilizando ChromaDB y HuggingFaceEmbeddings. En el contexto
del Módulo 3, este servicio funciona de forma desacoplada y sin dependencias del 
modelo de lenguaje (LLM), de la memoria conversacional o de prompts específicos.
Provee una interfaz determinista de recuperación semántica que será expuesta mediante
herramientas agénticas (Function Calling) en etapas posteriores del proyecto.

Asignatura: Técnicas Avanzadas de IA Aplicadas en Modelos de Lenguaje
Ruta Seleccionada: Ruta A (LangChain Backend Enterprise Service Layer)
"""

from typing import Any
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.config.settings import (
    KB_FILE_PATH,
    CHROMA_PATH,
    EMBEDDING_MODEL_NAME
)

# Variable global privada encargada de retener la instancia del Singleton
_rag_service = None


class RagService:
    """
    Clase de servicio encargada de gobernar el ciclo de vida de las búsquedas
    vectoriales y la extracción de contexto grounded para el sistema de RAG.
    """

    def __init__(self, k: int = 3, max_context_chars: int = 5000, fallback_chars: int = 4000) -> None:
        """
        Inicializa los motores de embeddings, la conexión con ChromaDB y la carga 
        del contexto estático de contingencia corporativa.

        Args:
            k (int): Cantidad por defecto de documentos top-K a recuperar.
            max_context_chars (int): Umbral estricto de truncamiento para el contexto vectorial.
            fallback_chars (int): Umbral de truncamiento aplicado al contexto estático de respaldo.
        """
        self.k = k
        self.max_context_chars = max_context_chars
        self.fallback_chars = fallback_chars

        # Inicialización del modelo de representación semántica vectorial
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        # Inicialización del cliente indexador de la base de datos vectorial
        self.vector_db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=self.embeddings
        )

        # Ingestión preventiva del archivo plano de conocimiento institucional
        self.static_context = self._load_static_context()

    def _load_static_context(self) -> str:
        """
        Lee físicamente la base de conocimiento en formato markdown para construir
        la memoria estática de contingencia ante fallos del vector store.

        Returns:
            str: Contenido completo del archivo o cadena vacía en caso de anomalía.
        """
        try:
            if KB_FILE_PATH.exists():
                return KB_FILE_PATH.read_text(encoding="utf-8")
        except Exception:
            # Captura controlada para evitar fallos de inicialización durante el despliegue
            pass
        return ""

    def retrieve(self, query: str, k: int | None = None) -> dict[str, Any]:
        """
        Ejecuta una búsqueda por similitud vectorial en ChromaDB y formatea el 
        payload resultante bajo un esquema estricto de auditoría y telemetría.

        Args:
            query (str): Consulta en lenguaje natural emitida por el canal u orquestador.
            k (int | None): Sobreescritura opcional del parámetro top-K para esta consulta.

        Returns:
            dict: Estructura unificada que contiene el estado operacional, los fragmentos
                  recuperados y metadatos del motor de embeddings.
        """
        current_k = k if k is not None else self.k
        
        try:
            # Ejecución de la búsqueda semántica basada en distancias vectoriales
            docs = self.vector_db.similarity_search(query, k=current_k)

            if docs:
                retrieved_chunks = []
                full_text_list = []

                for idx, doc in enumerate(docs):
                    # Construcción indexada de metadatos desglosados para auditoría t-SNE/UMAP
                    retrieved_chunks.append({
                        "chunk_index": idx,
                        "source": doc.metadata.get("source", "unknown"),
                        "section": doc.metadata.get("section", "unknown"),
                        "preview": doc.page_content[:200].replace("\n", " ") + "...",
                        "metadata": doc.metadata
                    })
                    full_text_list.append(doc.page_content)

                # Consolidación y truncamiento determinista del buffer de texto
                context_str = "\n\n".join(full_text_list)
                if len(context_str) > self.max_context_chars:
                    context_str = context_str[:self.max_context_chars]

                return {
                    "status": "success",
                    "query": query,
                    "context": context_str,
                    "docs_count": len(docs),
                    "source_type": "vector_db",
                    "retrieved_chunks": retrieved_chunks,
                    "context_length": len(context_str),
                    "embedding_model": EMBEDDING_MODEL_NAME,
                    "chroma_path": str(CHROMA_PATH)
                }

            # Flujo alterno (Fallback): Vector DB activa pero sin coincidencias semánticas relevantes
            static_fallback = self.static_context[:self.fallback_chars]
            return {
                "status": "warning",
                "query": query,
                "context": static_fallback,
                "docs_count": 0,
                "source_type": "static_context_fallback",
                "retrieved_chunks": [],
                "context_length": len(static_fallback),
                "embedding_model": EMBEDDING_MODEL_NAME,
                "chroma_path": str(CHROMA_PATH)
            }

        except Exception as e:
            # Flujo de mitigación ante excepciones operativas críticas en la capa de persistencia local
            static_fallback = self.static_context[:self.fallback_chars]
            return {
                "status": "error",
                "query": query,
                "context": static_fallback,
                "docs_count": 0,
                "source_type": "error_fallback",
                "retrieved_chunks": [],
                "context_length": len(static_fallback),
                "embedding_model": EMBEDDING_MODEL_NAME,
                "chroma_path": str(CHROMA_PATH),
                "error": str(e)
            }

    def diagnostics(self) -> dict[str, Any]:
        """
        Analiza estructuralmente la integridad física y volumétrica del motor RAG.

        Returns:
            dict: Indicadores clave de salud de ChromaDB y el archivo plano markdown.
        """
        try:
            # Inspección directa de la colección subyacente de Chroma
            collection_count = self.vector_db._collection.count()
        except Exception:
            collection_count = "unknown"

        path_exists = CHROMA_PATH.exists()
        
        # El estado global es óptimo únicamente si existe la base vectorial y es legible
        status = "success" if (path_exists and collection_count != "unknown") else "warning"

        return {
            "chroma_path": str(CHROMA_PATH),
            "chroma_path_exists": path_exists,
            "static_context_length": len(self.static_context),
            "collection_count": collection_count,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "status": status
        }


# =====================================================================
# SECCIÓN II: PATRÓN FACTORY Y FUNCIONES DE CONVENIENCIA (API CORE)
# =====================================================================

def get_rag_service() -> RagService:
    """
    Fábrica constructora basada en el patrón de diseño Singleton.
    Garantiza que el modelo de embeddings y la conexión con la base vectorial local 
    se inicialicen una única vez en el ciclo de ejecución de la instancia del backend.

    Returns:
        RagService: Instancia compartida del servicio de recuperación semántica.
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service


def retrieve_knowledge(query: str, k: int | None = None) -> dict[str, Any]:
    """
    Función de conveniencia unificada para invocar la recuperación semántica local.
    Diseñada para ser inyectada directamente como lógica core en las herramientas del agente.
    """
    return get_rag_service().retrieve(query, k=k)


def get_rag_diagnostics() -> dict[str, Any]:
    """
    Función de conveniencia unificada para auditoría externa de la salud del vector store.
    Utilizada en los endpoints de instrumentación y monitoreo del API REST.
    """
    return get_rag_service().diagnostics()


# Declaración explícita de símbolos exportables del módulo
__all__ = [
    "RagService",
    "get_rag_service",
    "retrieve_knowledge",
    "get_rag_diagnostics"
]

# Block de ejecución aislado para pruebas unitarias y diagnósticos en consola remota
if __name__ == "__main__":
    print("=====================================================================")
    print(" DIAGNÓSTICO EJECUCIÓN AISLADA - RAG_SERVICE V3")
    print("=====================================================================")
    service = get_rag_service()
    print("[DIAGNOSTICS]:", service.diagnostics())
    print("---------------------------------------------------------------------")
    print("[TEST RETRIEVE]:", service.retrieve("historia de Dollarcity", k=1))
    print("=====================================================================")