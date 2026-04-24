import streamlit as st
from src.engine.llm_service import LLMService

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dollarcity AI - Módulo 1",
    page_icon="💰",
    layout="centered"
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DEL SERVICIO (Cache para eficiencia) ---
@st.cache_resource
def get_llm_service():
    """Mantiene una única instancia del servicio para evitar recargas de KB."""
    return LLMService()

def main():
    # Encabezado Principal
    st.title("🤖 Asistente Virtual Dollarcity")
    st.subheader("Base de Conocimiento Semántica - Módulo 1")
    st.info("Este sistema utiliza **Context Injection** para responder basándose exclusivamente en la información curada de Dollarcity Colombia.")

    try:
        service = get_llm_service()
    except Exception as e:
        st.error(f"No se pudo conectar con Ollama: {e}")
        return

    # --- NAVEGACIÓN POR PESTAÑAS (Rúbrica: Resumen, FAQ, Q&A) ---
    tab1, tab2, tab3 = st.tabs(["📋 Resumen Corporativo", "❓ Preguntas Frecuentes", "💬 Chat Q&A"])

    # --- PESTAÑA 1: RESUMEN ---
    with tab1:
        st.write("Genera una síntesis estratégica de la empresa basada en el contexto.")
        if st.button("✨ Generar Resumen Ejecutivo"):
            with st.spinner("Analizando base de conocimiento..."):
                resumen = service.get_summary()
                st.markdown("### Resumen Corporativo")
                st.write(resumen)

    # --- PESTAÑA 2: FAQ ---
    with tab2:
        st.write("Identificación automática de los puntos clave para el cliente.")
        if st.button("🔍 Extraer FAQ Automática"):
            with st.spinner("Identificando dudas comunes..."):
                faqs = service.get_faq()
                st.markdown("### Preguntas Frecuentes Detectadas")
                st.write(faqs)

    # --- PESTAÑA 3: CHAT Q&A ---
    with tab3:
        st.write("Realiza preguntas específicas sobre la operación en Colombia.")
        
        # Inicializar historial de chat simple si se desea (opcional para demo)
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Input de usuario
        user_query = st.text_input("¿En qué puedo ayudarte hoy?", placeholder="Ej: ¿Cómo pido factura electrónica?")

        if st.button("Enviar Pregunta") or user_query:
            if user_query:
                with st.spinner("Consultando contexto..."):
                    respuesta = service.get_chat_response(user_query)
                    
                    st.markdown("---")
                    st.markdown("**Asistente Dollarcity:**")
                    st.write(respuesta)
            else:
                st.warning("Por favor, escribe una pregunta.")

    # Sidebar con metadatos técnicos (Muy útil para la sustentación)
    with st.sidebar:
        st.image("https://dollarcity.com/wp-content/uploads/2020/09/logo-dollarcity.png", width=200)
        st.divider()
        st.markdown("### Detalles Técnicos")
        st.write(f"**Modelo:** `gemma4:latest` (Ollama)")
        st.write("**Arquitectura:** Context Injection")
        st.write("**Framework:** LangChain")
        st.divider()
        st.caption("Maestría en IA y Ciencia de Datos - TAIALM")

if __name__ == "__main__":
    main()