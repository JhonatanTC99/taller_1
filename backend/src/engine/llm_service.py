import re
import os
import time
import traceback
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import FileChatMessageHistory
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

# Configuración del proyecto
from src.config.settings import (
    KB_FILE_PATH, DEFAULT_MODEL, EMBEDDING_MODEL_NAME, 
    OLLAMA_BASE_URL, CHROMA_PATH, HISTORY_DIR,
    LLM_PROVIDER, GOOGLE_API_KEY, GOOGLE_MODEL, OLLAMA_MODEL
)
# Prompts y Herramientas reales
from src.engine.prompts import RESUMEN_PROMPT, FAQ_PROMPT, QA_SYSTEM_PROMPT
from src.engine.structured_tool import get_dollarcity_info

class LLMService:
    def __init__(self, session_id="default_user"):
        """Inicializa el motor de IA con RAG, Memoria y Proveedor (Gemini/Ollama)."""
        self.session_id = session_id
        self.llm = None
        self.current_model_name = None
        
        # 1. Configuración de Embeddings y Modelo
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Inicialización protegida
        if not self.set_model(DEFAULT_MODEL):
            raise RuntimeError(f"[FATAL] No se pudo inicializar el modelo por defecto: {DEFAULT_MODEL}")
            
        self.parser = StrOutputParser()
        
        # 2. Carga de Contexto Estático (Markdown)
        self.static_context = self._load_context()
        
        # 3. Conexión a Base de Datos Vectorial (Chroma)
        self.vector_db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=self.embeddings
        )
        
        # 4. Memoria Persistente basada en archivos
        self.history = FileChatMessageHistory(str(HISTORY_DIR / f"{session_id}.json"))

    def set_model(self, model_name: str) -> bool:
        """
        Alterna dinámicamente entre Google Gen AI y Ollama Fallback.
        Optimizado para evitar reinstanciación innecesaria.
        """
        if model_name == self.current_model_name and self.llm is not None:
            return True

        # Lista de etiquetas internas que deben ser ignoradas
        internal_tags = [
            "rule_engine", "structured_tool", "structured_tool_logic", 
            "rag_engine", "fallback_debug", "unknown", "Modelo Desconocido",
            "Sincronizando...", "Servidor Offline", "Error de Conexión",
            "memory_engine"
        ]

        # Validar si el modelo es nulo, vacío o una etiqueta interna
        if not model_name or model_name in internal_tags:
            return False

        # Validar contra modelos permitidos en settings
        allowed_models = [DEFAULT_MODEL, GOOGLE_MODEL, OLLAMA_MODEL]
        if model_name not in allowed_models:
            return False

        try:
            if LLM_PROVIDER == "google":
                self.llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=GOOGLE_API_KEY,
                    temperature=0.1
                )
            else:
                self.llm = ChatOllama(
                    model=model_name,
                    base_url=OLLAMA_BASE_URL,
                    temperature=0.1
                )
            self.current_model_name = model_name
            return True
        except Exception as e:
            print(f"[LLM SERVICE] Error al configurar modelo {model_name}: {str(e)}")
            return False

    def get_model_name(self):
        """Metadata del modelo para fines de auditoría."""
        if self.current_model_name:
            return self.current_model_name
        return getattr(self.llm, "model", "unknown")

    def _is_memory_intent(self, q: str) -> bool:
        """Detecta si el usuario está declarando información personal o preguntando por ella."""
        q = q.lower()
        
        # Exclusiones: No debe dispararse para preguntas corporativas
        exclusions = ["empresa", "dollarcity", "tienda", "negocio", "compañía"]
        if any(ex in q for ex in exclusions) and ("nombre" in q or "llama" in q):
            return False

        intents = [
            "mi nombre es", "me llamo", "soy ", "recuerda que", "ten presente que",
            "acuérdate que", "acuerdate que", "como me llamo", "cómo me llamo",
            "como era que me llamaba", "cómo era que me llamaba", "cual es mi nombre",
            "cuál es mi nombre", "que te dije", "qué te dije", "recuerdas mi nombre",
            "recuerda mi nombre"
        ]
        return any(intent in q for intent in intents)

    def _extract_user_name_from_text(self, text: str) -> str | None:
        """Extrae el nombre propio de una frase de presentación."""
        text = text.lower().strip()
        patterns = [
            r"mi nombre es\s+([a-zñáéíóú\s]+)",
            r"me llamo\s+([a-zñáéíóú\s]+)",
            r"soy\s+([a-zñáéíóú\s]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Limpiar posibles restos de frase
                name = name.split(".")[0].split(",")[0].split("?")[0]
                return name.title()
        return None

    def _get_user_name_from_history(self) -> str | None:
        """Busca el nombre del usuario recorriendo el historial de atrás hacia adelante."""
        for msg in reversed(self.history.messages):
            if msg.type == "human":
                name = self._extract_user_name_from_text(msg.content)
                if name:
                    return name
        return None

    def _handle_memory_intent(self, question: str) -> dict:
        """Gestiona la respuesta para intenciones de memoria personal."""
        q_lower = question.lower()
        
        # 1. Caso: Declaración de nombre
        extracted_name = self._extract_user_name_from_text(question)
        if extracted_name:
            ans = f"Hola, {extracted_name}. Es un gusto saludarte. ¿En qué podemos ayudarte hoy?"
            self.history.add_user_message(question)
            self.history.add_ai_message(ans)
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "memory_engine",
                "source_type": "chat_history",
                "docs_count": 0
            }

        # 2. Caso: Pregunta por su nombre
        inquiry_keywords = ["como me llamo", "cómo me llamo", "como era que me llamaba", "cual es mi nombre", "cuál es mi nombre", "recuerdas mi nombre"]
        if any(k in q_lower for k in inquiry_keywords):
            history_name = self._get_user_name_from_history()
            if history_name:
                ans = f"Te llamas {history_name}."
            else:
                ans = "Aún no nos has indicado tu nombre en esta conversación."
            
            self.history.add_user_message(question)
            self.history.add_ai_message(ans)
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "memory_engine",
                "source_type": "chat_history",
                "docs_count": 0
            }

        # 3. Caso: Otros recordatorios o historial
        if "qué te dije" in q_lower or "que te dije" in q_lower or "recuerdas" in q_lower:
            # Recuperar últimos 3 intercambios humanos
            recent = [msg.content for msg in self.history.messages if msg.type == "human"][-3:]
            if recent:
                items = "\n- ".join(recent)
                ans = f"Recuerdo que recientemente hablamos de:\n- {items}"
            else:
                ans = "Aún estamos iniciando nuestra conversación, no tengo mucho que recordar todavía."
            
            self.history.add_user_message(question)
            self.history.add_ai_message(ans)
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "memory_engine",
                "source_type": "chat_history",
                "docs_count": 0
            }

        return self.get_chat_response(question)

    def _normalize_llm_content(self, response_or_content) -> str:
        """Normaliza la salida del LLM a un string plano."""
        content = getattr(response_or_content, 'content', response_or_content)
        if isinstance(content, str): return content
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, str): text_parts.append(part)
                elif isinstance(part, dict) and "text" in part: text_parts.append(part["text"])
                elif hasattr(part, 'text'): text_parts.append(part.text)
            return "".join(text_parts)
        return str(content)

    def _load_context(self) -> str:
        """Carga el conocimiento base desde el archivo markdown."""
        try:
            return KB_FILE_PATH.read_text(encoding="utf-8") if KB_FILE_PATH.exists() else ""
        except Exception:
            return ""

    def _clean_output(self, text: str) -> str:
        """Elimina etiquetas de control del modelo y espacios extra."""
        if not text: return ""
        text = re.sub(r'</?output>', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    @traceable(name="Chroma Retrieval", run_type="retriever")
    def _consultar_rag(self, query: str) -> dict:
        """Recupera fragmentos de Chroma o usa contexto estático con límites para optimizar latencia."""
        try:
            docs = self.vector_db.similarity_search(query, k=3)
            if docs:
                retrieved_chunks = []
                for d in docs:
                    retrieved_chunks.append({
                        "chunk_index": d.metadata.get("chunk_index"),
                        "source": d.metadata.get("source"),
                        "section": d.metadata.get("section", "No especificado"),
                        "preview": d.page_content[:350],
                        "metadata": d.metadata
                    })
                
                # Truncar contexto para el chat (máx 5000 chars)
                full_context = "\n\n".join([d.page_content for d in docs])
                final_context = full_context[:5000]

                return {
                    "context": final_context,
                    "docs_count": len(docs),
                    "source_type": "vector_db",
                    "retrieved_chunks": retrieved_chunks,
                    "context_length": len(final_context)
                }
            
            # Fallback truncado (máx 4000 chars)
            final_fallback = self.static_context[:4000]
            return {
                "context": final_fallback,
                "docs_count": 0,
                "source_type": "static_context_fallback",
                "retrieved_chunks": [],
                "context_length": len(final_fallback)
            }
        except Exception as e:
            print(f"[ERROR CHROMA]: {str(e)}")
            error_fallback = self.static_context[:4000]
            return {
                "context": error_fallback,
                "docs_count": 0,
                "source_type": "error_fallback",
                "retrieved_chunks": [],
                "context_length": len(error_fallback)
            }

    def debug_rag_query(self, question: str) -> dict:
        """Analiza exclusivamente la etapa de recuperación de información (Retrieval)."""
        rag_data = self._consultar_rag(question)
        collection_count = "unknown"
        if self.vector_db:
            try: collection_count = self.vector_db._collection.count()
            except Exception: pass
        return {
            "question": question,
            "source_type": rag_data['source_type'],
            "docs_count": rag_data['docs_count'],
            "retrieved_chunks": rag_data.get('retrieved_chunks', []),
            "context_length": len(rag_data['context']),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "chroma_count": collection_count,
            "status": "success"
        }

    def _invoke_llm_with_context(self, system_template: str, question: str, context: str) -> str:
        """Gestiona la cadena de invocación inyectando memoria e historial acotado."""
        # Reducción a 6 mensajes para optimizar el prompt enviado al LLM en chat
        historial = self.history.messages[-6:]
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_template),
            *[(msg.type, msg.content) for msg in historial],
            ("user", "{question}")
        ])
        chain = prompt_template | self.llm | self.parser
        res = chain.invoke({"context": context, "question": question})
        return self._normalize_llm_content(res)

    def get_rag_diagnostics(self) -> dict:
        """Analiza el estado de la base de datos vectorial y contexto."""
        count = "unknown"
        if self.vector_db:
            try: count = self.vector_db._collection.count()
            except Exception: count = "unknown"
        return {
            "chroma_path": str(CHROMA_PATH),
            "chroma_path_exists": os.path.exists(CHROMA_PATH),
            "static_context_length": len(self.static_context),
            "collection_count": count,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "status": "success" if count != 0 and count != "unknown" else "warning"
        }

    def test_llm_connection(self) -> dict:
        """Endpoint de salud para validar conectividad con el proveedor LLM."""
        try:
            res = self.llm.invoke("Responde únicamente: ok")
            content = self._normalize_llm_content(res)
            content = self._clean_output(content)
            return {
                "status": "success",
                "model": self.get_model_name(),
                "provider": LLM_PROVIDER,
                "content": content
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "provider": LLM_PROVIDER}

    def get_summary(self) -> dict:
        """Genera el resumen ejecutivo corporativo usando el contexto completo."""
        try:
            res = self._invoke_llm_with_context(RESUMEN_PROMPT, "Genera el resumen corporativo.", self.static_context)
            return {"content": self._clean_output(res), "model": self.get_model_name(), "status": "success"}
        except Exception as e:
            return {"content": f"Error en Resumen: {str(e)}", "status": "error"}

    def get_faq(self) -> dict:
        """Genera el listado dinámico de FAQ usando el contexto completo."""
        try:
            res = self._invoke_llm_with_context(FAQ_PROMPT, "Genera el FAQ.", self.static_context)
            return {"content": self._clean_output(res), "model": self.get_model_name(), "status": "success"}
        except Exception as e:
            return {"content": f"Error en FAQ: {str(e)}", "status": "error"}
    
    @traceable(name="Dollarcity Chat Router", run_type="chain")
    def get_chat_response(self, question: str) -> dict:
        """Router Híbrido Avanzado con Fast-Path de optimización incremental."""
        start_total = time.perf_counter()
        q = question.lower().strip()
        print(f"\n[ROUTER] Entrada: '{question}'")

        # 1. RUTA: Herramienta Estructurada (Datos exactos JSON)
        structured_keywords = [
            "nit", "teléfono", "telefono", "contacto", "correo", "email", "horario", 
            "horarios", "sede", "dirección", "direccion", "oficina", "ciudad", 
            "ciudades", "sucursal", "sucursales", "devolución", "devolucion", 
            "cambio", "garantía", "garantia", "factura", "facturación", 
            "facturacion", "redes", "instagram", "facebook", "trabajo", "vacante", "empleo"
        ]
        if any(w in q for w in structured_keywords):
            print("[ROUTER] Ruta elegida: structured_tool")
            ans = get_dollarcity_info(question)
            self.history.add_user_message(question)
            self.history.add_ai_message(ans)
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "structured_tool",
                "source_type": "json_db",
                "docs_count": 0
            }

        # 2. RUTA: Motor de Memoria Personal
        if self._is_memory_intent(question):
            print("[ROUTER] Ruta elegida: memory_engine")
            return self._handle_memory_intent(question)

        # 3. RUTA: Rule Engine - Fuera de Dominio Evidente
        out_of_domain = ["presidente", "clima", "fútbol", "futbol", "política", "politica", "noticias", "dólar hoy", "dolar hoy"]
        if any(w in q for w in out_of_domain):
            print("[ROUTER] Ruta elegida: rule_engine (out-of-domain)")
            ans = "Lo sentimos, no contamos con esa información específica. Nuestra labor se centra en ofrecerte la mejor experiencia en nuestras tiendas Dollarcity."
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "rule_engine",
                "source_type": "rule",
                "docs_count": 0
            }

        # 4. RUTA: Rule Engine - Producto Ambiguo
        product_trigger = ["venden", "tienen", "hay"]
        if any(w in q for w in product_trigger) and len(q.split()) < 7:
            print("[ROUTER] Ruta elegida: rule_engine (ambiguous-product)")
            ans = "Para consultar disponibilidad de productos específicos, te sugerimos visitar tu tienda Dollarcity más cercana o revisar nuestros canales oficiales."
            return {
                "content": ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "rule_engine",
                "source_type": "rule",
                "docs_count": 0
            }

        # 5. RUTA: Motor RAG (Conocimiento Corporativo) con Medición de Latencia
        print("[ROUTER] Ruta elegida: rag_engine")
        t_retrieval_start = time.perf_counter()
        rag_data = self._consultar_rag(question)
        t_retrieval_end = time.perf_counter()

        try:
            t_gen_start = time.perf_counter()
            raw_res = self._invoke_llm_with_context(QA_SYSTEM_PROMPT, question, rag_data['context'])
            final_ans = self._clean_output(raw_res)
            t_gen_end = time.perf_counter()
            
            self.history.add_user_message(question)
            self.history.add_ai_message(final_ans)
            
            end_total = time.perf_counter()
            
            return {
                "content": final_ans,
                "model": self.get_model_name(),
                "status": "success",
                "tool_used": "rag_engine",
                "source_type": rag_data['source_type'],
                "docs_count": rag_data['docs_count'],
                "timing_ms": {
                    "retrieval": round((t_retrieval_end - t_retrieval_start) * 1000, 2),
                    "generation": round((t_gen_end - t_gen_start) * 1000, 2),
                    "total": round((end_total - start_total) * 1000, 2)
                }
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "content": f"DEBUG ERROR RAG/LLM: {str(e)}", 
                "model": self.get_model_name(),
                "status": "error",
                "tool_used": "fallback_debug",
                "debug_error": str(e),
                "source_type": "error_fallback",
                "docs_count": 0
            }

def start_console_chat():
    """Inicia un bucle de chat interactivo en la consola con el servicio de IA de Dollarcity."""
    service = LLMService()
    print("\n      DOLLARCITY AI - MODO CONSOLA")
    while True:
        try:
            u = input("\nUsuario > ").strip()
            if u.lower() in ["salir", "exit"]: break
            if not u: continue
            res = service.get_chat_response(u)
            print(f"IA [{res['model']}] > {res['content']}")
        except KeyboardInterrupt: break