from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.tools import Tool
from langchain_core.exceptions import OutputParserException
import langchainhub as hub
from langchain.agents import create_react_agent, AgentExecutor

import re
from src.config.settings import (
    KB_FILE_PATH, DEFAULT_MODEL, EMBEDDING_MODEL_NAME, 
    OLLAMA_BASE_URL, CHROMA_PATH, HISTORY_DIR
)
from src.engine.prompts import RESUMEN_PROMPT, FAQ_PROMPT, QA_SYSTEM_PROMPT
from src.engine.structured_tool import get_dollarcity_info

# --- CONFIGURACIÓN DE PERSISTENCIA ---
MEMORIA_DIR = HISTORY_DIR
MEMORIA_DIR.mkdir(parents=True, exist_ok=True)

class LLMService:
    def __init__(self, session_id="default_user"):
        """Inicializa el motor con RAG y Memoria Persistente."""
        self.session_id = session_id
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.set_model(DEFAULT_MODEL)
        self.parser = StrOutputParser()
        
        # 1. CARGA DE CONTEXTO ESTÁTICO
        self.static_context = self._load_context()

        # 2. RAG: Base de Datos Vectorial
        self.vector_db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=self.embeddings
        )

        # 3. MEMORIA PERSISTENTE (Solo el historial)
        self.history = FileChatMessageHistory(str(HISTORY_DIR / f"{session_id}.json"))

        # 4. DEFINICIÓN DE HERRAMIENTAS (se conecta el RAG y la herramienta estructurada)
        self.tools = [
            Tool(
                name="Consultar_Biblioteca_Documental",
                func=self._consultar_rag,
                description="Útil para preguntas generales sobre historia, cultura, productos y conceptos de Dollarcity."
            ),
            Tool(
                name="Consultar_Datos_Corporativos",
                func=get_dollarcity_info,
                description="Útil para buscar datos exactos como NIT, teléfono, correos, horarios, sedes físicas y políticas de devolución."
            )
        ]

        # 5. CONFIGURACIÓN DEL AGENTE (Router)
        # Descargamos el prompt de razonamiento ReAct
        try:
            base_prompt = hub.pull("hwchase17/react-chat")

            self.prompt = base_prompt.partial(
                system_instructions=QA_SYSTEM_PROMPT,
                context_estatico=self.static_context
            )

            # Construir el agente (usa el LLM y las herramientas)
            self.agent = create_react_agent(self.llm, self.tools, self.prompt)

            # Crear el ejecutor con los parámetros
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True, # Para ver los "Thoughts" y "Actions" en consola
                handle_parsing_errors=True, # CRUCIAL para modelos locales como Ollama
                max_iterations=4, # Evita bucles infinitos si el modelo se confunde
                return_intermediate_steps=False # Cambia a True si se quiere auditar el razonamiento
            )
        except Exception as e:
            print(f"[CRITICAL ERROR] No se pudo inicializar el Agente: {e}")
        

    def _consultar_rag(self, query: str):
        """Recupera los 3 fragmentos más relevantes del taller."""
        try:
            docs = self.vector_db.similarity_search(query, k=3)
            if not docs:
                return self.static_context
            return "\n\n".join([d.page_content for d in docs])
        
        # Errores específicos de Chroma/Vector DB
        except (RuntimeError, ValueError) as e:
            print(f"[RAG ERROR] Fallo en la búsqueda vectorial: {e}")
            return self.static_context
        
        # Errores de conexión o configuración de embeddings
        except AttributeError as e:
            print(f"[RAG ERROR] Base de datos no inicializada: {e}")
            return self.static_context

    def set_model(self, model_name: str):
        self.llm = ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            num_ctx=32000, # regla nueva, probar con modelos pequeños
            seed=42,
            top_p=0.7,
            stop=["</output>"]
        )

    def _load_context(self) -> str:
        """Carga la base de conocimiento de forma segura."""
        try:
            if not KB_FILE_PATH.exists():
                return "Error: Base de conocimiento no encontrada."
            return KB_FILE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            return "Error: Base de conocimiento no encontrada."
        except PermissionError:
            return "Error: Permiso denegado al acceder a la base de conocimiento."
        except OSError as e:
            return f"Error de sistema al cargar contexto: {str(e)}"
    

    def _clean_output(self, text: str) -> str:
        if not text:
            return ""

        # 1. EXTRAER SOLO <output>
        match = re.search(r'<output>(.*?)</output>', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 2. FALLBACK: cortar desde donde empieza respuesta real
        fallback_markers = [
            "La información",
            "Nosotros",
            "Lo sentimos",
        ]

        for marker in fallback_markers:
            if marker in text:
                text = text.split(marker, 1)[1]
                text = marker + text
                break

        # 3. ELIMINAR TODO LO TÉCNICO
        text = re.sub(r"\[.*?\]", "", text, flags=re.DOTALL)

        # 4. LIMPIEZA FINAL
        return text.strip()

    def _run_chain(self, system_template: str, user_input: str = None) -> dict:
        """Motor unificado con RAG, Memoria Manual y Validaciones."""
        
        # PREPARAR CONTEXTO (RAG si hay pregunta, sino estático)
        contexto = self._consultar_rag(user_input) if user_input else self.static_context
        
        # PREPARAR HISTORIAL (Persistente)
        historial_previo = self.history.messages[-10:] # Últimos 10 mensajes para contexto

        # CONSTRUIR MENSAJES
        messages = [("system", system_template)]
        # Añadimos los mensajes previos del JSON a la conversación actual
        for msg in historial_previo:
            messages.append((msg.type, msg.content))
        
        input_data = {"context": contexto}
        if user_input:
            messages.append(("user", "{question}"))
            input_data["question"] = user_input

        prompt_template = ChatPromptTemplate.from_messages(messages)
        chain = prompt_template | self.llm | self.parser
        
        try:
            raw_response = chain.invoke(input_data)
            cleaned = self._clean_output(raw_response)

            # VALIDACIONES ESPECÍFICAS
            if system_template == FAQ_PROMPT and cleaned.lower().count("respuesta") < 5:
                return {"content": "Error: FAQ incompleto.", "status": "error"}

            if "Sintetizar la información" in system_template:
                cleaned = "\n\n".join(cleaned.split("\n\n")[:3])

            # ACTUALIZAR MEMORIA EN DISCO
            if user_input:
                self.history.add_user_message(user_input)
                self.history.add_ai_message(cleaned)

            return {
                "content": cleaned,
                "model": self.get_model_name(),
                "status": "success"
            }

        # --- GESTIÓN DE EXCEPCIONES ESPECÍFICAS ---
        except (ConnectionError, TimeoutError):
            return {
                "content": "Error de conexión con Ollama. Asegúrate de que el servidor esté activo.",
                "status": "error",
                "model": "Network"
            }

        except OutputParserException as e:
            return {
                "content": f"El modelo entregó un formato ilegible: {str(e)}",
                "status": "error",
                "model": "Parser"
            }

        except (KeyError, TypeError, AttributeError) as e:
            return {
                "content": f"Error de configuración o lógica interna: {str(e)}",
                "status": "error",
                "model": "Logic"
            }

        except Exception as e:
            # Esta línea captura cualquier error no previsto sin que Pylint se queje
            print(f"[FATAL ERROR] {type(e).__name__}: {e}")
            return {
                "content": "Ocurrió un error inesperado en el motor de IA.",
                "status": "error",
                "model": "Unknown"
            }
        
    def get_model_name(self):
        """Devuelve el nombre del modelo configurado."""
        return getattr(self.llm, "model", "unknown")

    # --- MÉTODOS DE INTERFAZ PÚBLICA ---

    def get_summary(self) -> str:
        """Tarea 1: Resumen de marca."""
        return self._run_chain(RESUMEN_PROMPT)

    def get_faq(self) -> str:
        """Tarea 2: FAQ Automático."""
        return self._run_chain(FAQ_PROMPT)

    def get_chat_response(self, question: str) -> dict:
        """Maneja la interacción de chat con el usuario."""
        if not question.strip():
            return {
                "content": "Por favor, escribe una pregunta.",
                "model": self.get_model_name(),
                "status": "error"
            }
        
        chat_history = self.history.messages[-10:]

        try:
            # El agente recibe el input y el historial
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": chat_history
            })

            respuesta_final = self._clean_output(result["output"])

            # Guardar en persistencia
            self.history.add_user_message(question)
            self.history.add_ai_message(respuesta_final)

            return {
                "content": respuesta_final,
                "model": self.get_model_name(),
                "status": "success"
            }
        except Exception as e:
            print(f"[AGENT ERROR]: {e}")
            # Aplicamos la NEGACIÓN ESTÁNDAR de tu prompt en caso de fallo crítico
            return {
                "content": "Lo sentimos, no contamos con esa información específica en este momento.",
                "status": "error"
            }
        
# --- INICIALIZADOR DE CONSOLA (Debug) ---
def start_console_chat():
    """Inicializa un bucle de chat interactivo por consola."""
    service = LLMService()
    print("\n[INFO] Dollarcity AI. Escribe 'salir' para finalizar.")
    while True:
        q = input("\nUsuario > ")
        if q.lower() in ['salir', 'exit']:
            break
        respuesta = service.get_chat_response(q)
        print(f"\nDollarcity: {respuesta.get('content')}")

if __name__ == "__main__":
    start_console_chat()