# Dollarcity AI - Sistema Agéntico Conversacional (Módulo 3)

Sistema conversacional autónomo diseñado para interactuar con una base de conocimiento corporativa sobre Dollarcity Colombia. 

Este proyecto corresponde al **Taller 3 - Sistemas de Recomendación, Agentes y N8N (Ruta A)**. Representa la evolución final del asistente, pasando de un enrutador manual basado en reglas (Módulo 2) a un **Sistema Agéntico robusto** orquestado con LangGraph, con memoria persistente en bases de datos relacionales y desplegado en canales de mensajería reales (WhatsApp).

## 👥 Integrantes
- ERICA ROCIO MARQUEZ MENESES
- JOHN MARIO CARMONA DAVID
- JHONATAN ANDRES TAPIA CORDOBA
- LUIS FERNANDO MEZA RAMIREZ

---

## 🚀 Evolución Arquitectónica: Módulo 2 vs Módulo 3

Para este entregable de productización, la arquitectura sufrió una refactorización estricta hacia el estado del arte en agentes de IA:

1. **De Enrutador Manual a *Function Calling* Estricto:** El router antiguo (basado en palabras clave mediante `if/else`) fue reemplazado por un Agente autónomo de LangChain (`create_agent`). Ahora, el LLM decide por sí mismo qué herramienta usar basándose en esquemas estrictos de Pydantic.
2. **De Memoria en Archivos a Persistencia Relacional:** El historial en archivos `.json` (`FileChatMessageHistory`) se migró a un checkpointer distribuido utilizando **PostgresSaver**. La memoria ahora vive en una base de datos PostgreSQL alojada en un contenedor Docker, separando los hilos de conversación por número de teléfono (`thread_id`).
3. **Control de Flujo (Human-in-the-Loop):** Se integró el `HumanInTheLoopMiddleware` para pausar la ejecución del agente y requerir aprobación humana cuando un usuario intenta realizar acciones sensibles (ej. registrarse para una oferta de empleo).
4. **Despliegue Omnicanal:** El sistema dejó de ser un script local para convertirse en una API REST (FastAPI) expuesta a internet mediante **Ngrok**, conectada a **N8N** para orquestar la recepción y envío de mensajes vía **WhatsApp (Twilio)**.

---

## 🧩 Herramientas del Agente (Tools)

El agente está dotado de 4 herramientas o "brazos operativos" que invoca de forma autónoma según la intención del usuario:

1. **`consultar_dato_corporativo`:** Accede a una base de datos estructurada (JSON) para devolver respuestas exactas y deterministas (NIT, teléfonos, direcciones, horarios).
2. **`consultar_base_conocimiento_rag`:** Activa el motor de recuperación semántica (RAG) sobre **ChromaDB** para preguntas abiertas, historia de la empresa, noticias y cultura organizacional.
3. **`responder_fuera_de_dominio`:** Herramienta de seguridad que aplica políticas de contención si el usuario pregunta sobre clima, política o temas ajenos a Dollarcity.
4. **`registrar_lead_interesado`:** Herramienta que captura intenciones de empleo o contacto comercial y activa el **Human-in-the-Loop**, dejando la solicitud en estado de "revisión pendiente" en el backend.

---

## 🏗️ Arquitectura y Flujo End-to-End

El sistema sigue la **Ruta A** exigida en el taller, garantizando una comunicación fluida y sin latencia excesiva.

```text
📱 Usuario (WhatsApp) 
      ↓ 
💬 Twilio (Sandbox / WhatsApp API) 
      ↓ 
⚙️ N8N (Webhook -> HTTP Request) 
      ↓ 
🌐 Ngrok (Túnel seguro a localhost) 
      ↓ 
🖥️ FastAPI (Endpoint: /api/channel/chat) 
      ↓ 
🧠 LangGraph Agent (Evalúa intención y extrae Thread ID)
      ├── 🐘 PostgresSaver (Recupera memoria del usuario)
      └── 🛠️ Function Calling (Elige entre ChromaDB, JSON o HITL)
      ↓
(Retorno del JSON estructurado hacia N8N y finalmente al Usuario)

```

---

## ⚙️ Requisitos Previos

* **Python 3.12** o superior (Gestión con `uv`).
* **Docker Desktop** (Para levantar PostgreSQL).
* **Ngrok** (Para exponer el puerto local a internet).
* Cuenta en **N8N** (Cloud o Local) y **Twilio** (Para WhatsApp).
* API Key de **Google Gemini** (`gemini-3.1-flash-lite`).

---

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio e instalar dependencias

```bash
git clone [https://github.com/JhonatanTC99/taller_1.git](https://github.com/JhonatanTC99/taller_1.git)
cd taller_1/backend
uv sync

```

### 2. Variables de Entorno

Crea un archivo `.env` en la carpeta `backend/` con la siguiente estructura:

```env
LLM_PROVIDER=google
AGENT_PROVIDER=google
GOOGLE_API_KEY=tu_api_key_aqui
GOOGLE_MODEL=gemini-3.1-flash-lite
AGENT_MODEL=gemini-3.1-flash-lite
ENABLE_AGENT_V3=true
ENABLE_HITL=false
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dollarcity_agent

```

### 3. Preparación de Datos (Primera Ejecución)

Si es la primera vez que clonas el repositorio, debes poblar la base de datos vectorial ChromaDB ejecutando el pipeline de curación:

```bash
uv run python main.py --full

```

### 4. Ejecución Rápida del Servidor

Para levantar todo el ecosistema local de forma automática, desde la raíz del proyecto haz doble clic o ejecuta desde consola:

```bash
start.bat

```

*Este script levanta el contenedor de PostgreSQL en Docker y enciende el servidor FastAPI con observabilidad a color en la consola.*

---

## 🌍 Conexión con WhatsApp (N8N + Ngrok)

Para que el bot responda mensajes reales desde un celular:

1. Mientras `start.bat` está corriendo, abre una nueva terminal y ejecuta Ngrok:
```bash
ngrok http 8000

```


2. Copia la URL pública generada (ej. `https://xxxx.ngrok-free.app`).
3. Ve a tu flujo de **N8N**. En el nodo de **HTTP Request**, configura la URL hacia:
`https://xxxx.ngrok-free.app/api/channel/chat`
4. Asegúrate de que N8N envíe el payload en formato JSON bajo el contrato esperado:
```json
{
  "user_id": "{{ $json.body.WaId }}",
  "message": "{{ $json.body.Body }}",
  "channel": "whatsapp"
}

```


5. En el último nodo de respuesta de Twilio, asegúrate de mapear únicamente el texto resultante del agente usando la expresión: `{{ $json.content }}`.

---

## 📊 Evaluación y Pruebas (Testing)

El sistema incluye una batería de pruebas automatizada para auditar los tiempos de latencia, la decisión de enrutamiento (Routing) y la calidad del RAG.

Para ejecutarla, abre una terminal en la carpeta `backend/` y lanza:

```bash
uv run python tests/questions.py

```

Esto generará el archivo `backend/data/evaluation_results.csv`, donde se evidencia el uso correcto de las herramientas, la recuperación exitosa desde ChromaDB y los tiempos de inferencia del LLM.

---

*Proyecto académico desarrollado para la Maestría en Ciencia de Datos e IA.*

```

```