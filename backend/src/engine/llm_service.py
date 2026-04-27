from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re # Usaremos regex para limpieza

from src.config.settings import KB_FILE_PATH, DEFAULT_MODEL, OLLAMA_BASE_URL
from src.engine.prompts import RESUMEN_PROMPT, FAQ_PROMPT, QA_SYSTEM_PROMPT

class LLMService:
    def __init__(self):
        """Inicializa el modelo"""
        self.set_model(DEFAULT_MODEL)
        self.parser = StrOutputParser()
        self.context = self._load_context()
        self.chat_history = []

    def set_model(self, model_name: str):
        self.llm = ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.2,
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

        # 4. LIMPIEZA FINAL
        return text.strip()

    def _run_chain(self, system_template: str, user_input: str = None) -> str:
        """Motor de ejecución unificado."""
        # Definimos los mensajes según si hay input del usuario o es tarea automática
        messages = [("system", system_template)]
        input_data = {"context": self.context}

        if user_input:
            messages += self.chat_history
            messages.append(("user", "{question}"))
            input_data["question"] = user_input

        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Pipeline: Prompt -> LLM -> Parser -> Limpieza Pro
        chain = prompt | self.llm | self.parser
        
        try:
            raw_response = chain.invoke(input_data)
            cleaned = self._clean_output(raw_response)
            #cleaned = self._enforce_rules(cleaned, user_input or "")

            #VALIDACIÓN SOLO PARA FAQ
            is_faq = system_template == FAQ_PROMPT
            if is_faq and cleaned.count("Respuesta:") < 5:
                return {
                    "content": "Error: el modelo no generó respuestas completas.",
                    "model": self.get_model_name(),
                    "status": "error"
                }

            is_summary = "Sintetizar la información" in system_template

            if is_summary:
                paragraphs = cleaned.split("\n\n")
                cleaned = "\n\n".join(paragraphs[:3])

            #cleaned = self._enforce_rules(cleaned, user_input or "")
            if user_input:
                self.chat_history.append(("user", user_input))
                self.chat_history.append(("assistant", cleaned))

                MAX_TURNS = 5  # 5 intercambios (user + assistant)
                self.chat_history = self.chat_history[-(MAX_TURNS * 2):]
            return {
                "content": cleaned,
                "model": self.get_model_name(),
                "status": "success"
            }
        except Exception as e:
            return {
                "content": f"Error interno: {str(e)}",
                "model": "Error",
                "status": "error"
            }
    def get_model_name(self):
        return getattr(self.llm, "model", "unknown")

    # --- MÉTODOS DE INTERFAZ PÚBLICA ---

    def get_summary(self) -> str:
        """Tarea 1: Resumen de marca."""
        return self._run_chain(RESUMEN_PROMPT)

    def get_faq(self) -> str:
        """Tarea 2: FAQ Automático."""
        return self._run_chain(FAQ_PROMPT)

    def get_chat_response(self, question: str) -> str:
        if not question.strip():
                return {
                    "content": "Por favor, escribe una pregunta.",
                    "model": self.get_model_name(),
                    "status": "error"
                }
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