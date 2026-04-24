from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config.settings import KB_FILE_PATH, DEFAULT_MODEL, OLLAMA_BASE_URL
from src.engine.prompts import RESUMEN_PROMPT, FAQ_PROMPT, QA_SYSTEM_PROMPT, USER_TEMPLATE

class LLMService:
    def __init__(self):
        """Inicializa el modelo local y carga la base de conocimiento."""
        self.llm = ChatOllama(
            model=DEFAULT_MODEL, 
            base_url=OLLAMA_BASE_URL,
            temperature=0.1
        )
        self.parser = StrOutputParser()
        self.context = self._load_context()

    def _load_context(self) -> str:
        """Carga la KB curada desde el sistema de archivos."""
        try:
            if not KB_FILE_PATH.exists():
                return "Error: No se encontró la base de conocimiento curada."
            return KB_FILE_PATH.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error al cargar contexto: {str(e)}"

    def _run_chain(self, system_template: str, user_input: str = "") -> str:
        """Helper privado para ejecutar cualquier cadena de LangChain."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", USER_TEMPLATE if user_input else "Procesa la solicitud.")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            return chain.invoke({
                "context": self.context,
                "question": user_input
            })
        except Exception as e:
            return f"[ERROR LLM]: {str(e)}"

    def get_summary(self) -> str:
        """Tarea 1: Generar resumen de la empresa."""
        return self._run_chain(RESUMEN_PROMPT)

    def get_faq(self) -> str:
        """Tarea 2: Generar listado automático de FAQ."""
        return self._run_chain(FAQ_PROMPT)

    def get_chat_response(self, question: str) -> str:
        """Tarea 3: Responder preguntas específicas (Q&A)."""
        return self._run_chain(QA_SYSTEM_PROMPT, question)

# --- FUNCIÓN DE INTERFAZ DE CONSOLA ---
def start_console_chat():
    """Lógica para el chat interactivo por terminal (Fase de Pruebas)."""
    print("\n" + "="*50)
    print("SISTEMA Q&A DOLLARCITY - MODO CONSOLA")
    print("Escribe 'salir' o 'exit' para terminar.")
    print("="*50)
    
    service = LLMService()
    
    while True:
        query = input("\nUsuario > ")
        if query.lower() in ["salir", "exit", "quit"]:
            print("Cerrando sesión...")
            break
            
        if not query.strip():
            continue
            
        print("\nAsistente Dollarcity (pensando)...")
        respuesta = service.get_chat_response(query)
        print(f"\n{respuesta}")

if __name__ == "__main__":
    # Test rápido de integridad
    s = LLMService()
    print("Contexto cargado correctamente.")