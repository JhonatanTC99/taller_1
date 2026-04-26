from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re # Usaremos regex para limpieza

from src.config.settings import KB_FILE_PATH, DEFAULT_MODEL, OLLAMA_BASE_URL
from src.engine.prompts import RESUMEN_PROMPT, FAQ_PROMPT, QA_SYSTEM_PROMPT

class LLMService:
    def __init__(self):
        """Inicializa el modelo"""
        self.llm = ChatOllama(
            model=DEFAULT_MODEL, 
            base_url=OLLAMA_BASE_URL,
            temperature=0.2, 
            seed=42,
            top_p=0.7,
            stop=["</output>", "[CONTEXTO]", "[REGLAS", "[FLUJO", "BASE DE CONOCIMIENTO"] # El modelo se detiene inmediatamente al terminar la respuesta
        )
        self.parser = StrOutputParser()
        self.context = self._load_context()

    def _load_context(self) -> str:
        """Carga la base de conocimiento de forma segura."""
        try:
            if not KB_FILE_PATH.exists():
                return "Error: Base de conocimiento no encontrada."
            return KB_FILE_PATH.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error al cargar contexto: {str(e)}"

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
        text = re.sub(r"\(.*?\)", "", text, flags=re.DOTALL)

        # 4. LIMPIEZA FINAL
        return text.strip()

    def _run_chain(self, system_template: str, user_input: str = None) -> str:
        """Motor de ejecución unificado."""
        # Definimos los mensajes según si hay input del usuario o es tarea automática
        messages = [("system", system_template)]
        input_data = {"context": self.context}

        if user_input:
            messages.append(("user", "{question}"))
            input_data["question"] = user_input

        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Pipeline: Prompt -> LLM -> Parser -> Limpieza Pro
        chain = prompt | self.llm | self.parser
        
        try:
            raw_response = chain.invoke(input_data)
            return {
                "content": self._clean_output(raw_response),
                "model": str(DEFAULT_MODEL),
                "status": "success"
            }
        except Exception as e:
            return {"content": str(e), "model": "Error", "status": "error"}

    # --- MÉTODOS DE INTERFAZ PÚBLICA ---

    def get_summary(self) -> str:
        """Tarea 1: Resumen de marca."""
        return self._run_chain(RESUMEN_PROMPT)

    def get_faq(self) -> str:
        """Tarea 2: FAQ Automático."""
        return self._run_chain(FAQ_PROMPT)

    def get_chat_response(self, question: str) -> str:
        if not question.strip():
            return "Por favor, escribe una pregunta."
        return self._run_chain(QA_SYSTEM_PROMPT, question)

# --- INICIALIZADOR DE CONSOLA (Debug) ---
def start_console_chat():
    service = LLMService()
    print("\n[INFO] Dollarcity AI. Escribe 'salir' para finalizar.")
    while True:
        q = input("\nUsuario > ")
        if q.lower() in ['salir', 'exit']: break
        print(f"\nDollarcity: {service.get_chat_response(q)}")

if __name__ == "__main__":
    start_console_chat()