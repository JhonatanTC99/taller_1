import sys
from pathlib import Path
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configuración de rutas para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import KB_FILE_PATH, DEFAULT_MODEL, OLLAMA_BASE_URL
from engine.prompts import SYSTEM_PROMPT, USER_TEMPLATE

class LLMService:
    def __init__(self):
        self.model_name = DEFAULT_MODEL
        self.llm = ChatOllama(model=self.model_name, base_url=OLLAMA_BASE_URL)
        self.context = self._load_context()
        self.parser = StrOutputParser()

    def _load_context(self):
        """Carga la base de conocimiento curada."""
        try:
            if not KB_FILE_PATH.exists():
                print(f"[ERROR] No se encontró la KB en {KB_FILE_PATH}")
                return ""
            with open(KB_FILE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] Error al cargar contexto: {e}")
            return ""

    def get_response(self, question: str):
        """Genera una respuesta basada en el contexto."""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", USER_TEMPLATE)
        ])
        
        # Crear cadena (Chain)
        chain = prompt_template | self.llm | self.parser
        
        try:
            # Ejecutar inferencia
            response = chain.invoke({
                "context": self.context,
                "question": question
            })
            return response
        except Exception as e:
            return f"Error en el servicio de IA: {str(e)}"

def start_console_chat():
    """Bucle de chat por consola para pruebas."""
    print(f"\n--- Iniciando Cerebro IA de Dollarcity (Modelo: {DEFAULT_MODEL}) ---")
    print("Escribe 'salir' para terminar.\n")
    
    service = LLMService()
    
    while True:
        user_input = input("Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            break
            
        print("\nDollarcity AI está pensando...", end="\r")
        response = service.get_response(user_input)
        print(f"Asistente: {response}\n")

if __name__ == "__main__":
    start_console_chat()