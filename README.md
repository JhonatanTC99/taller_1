# Dollarcity AI - Sistema Agentico Conversacional (Fase 3)

Sistema conversacional sobre informacion corporativa de Dollarcity Colombia, desarrollado como entregable de **Fase 3 / Modulo 3** para el taller de Sistemas de Recomendacion, Agentes y N8N.

La fase actual se centra en un backend **FastAPI** con un agente **LangGraph/LangChain**, herramientas de Function Calling, memoria persistente en **PostgreSQL** mediante **PostgresSaver**, recuperacion semantica con **ChromaDB** y despliegue por canales externos usando **N8N + Ngrok + WhatsApp/Twilio**.

## Integrantes

- ERICA ROCIO MARQUEZ MENESES
- JOHN MARIO CARMONA DAVID
- JHONATAN ANDRES TAPIA CORDOBA
- LUIS FERNANDO MEZA RAMIREZ

## Arquitectura Fase 3

El flujo principal de esta fase usa el endpoint productivo `/api/channel/chat`:

```text
Usuario WhatsApp
      |
Twilio Sandbox / WhatsApp API
      |
N8N Webhook + HTTP Request
      |
Ngrok
      |
FastAPI /api/channel/chat
      |
LangGraph Agent
      |-- PostgreSQL / PostgresSaver para memoria por usuario
      |-- ChromaDB para consultas RAG
      |-- JSON corporativo para datos deterministas
      |
Respuesta JSON hacia N8N y WhatsApp
```

## Herramientas del Agente

El agente selecciona herramientas de forma autonoma segun la intencion del usuario:

- `consultar_dato_corporativo`: consulta datos estructurados como NIT, telefonos, correos, horarios, ciudades, devoluciones, facturacion, redes y empleo.
- `consultar_base_conocimiento_rag`: recupera contexto desde ChromaDB para preguntas abiertas sobre historia, expansion, noticias, cultura y modelo de negocio de Dollarcity.
- `responder_fuera_de_dominio`: aplica contencion cuando la pregunta no pertenece al dominio de Dollarcity.
- `registrar_lead_interesado`: identifica intenciones de empleo, proveedores o contacto comercial y devuelve una respuesta controlada de pre-registro pendiente.

## Requisitos

- Python 3.12 o superior.
- `uv` para gestionar dependencias del backend.
- Docker o Docker Desktop para levantar PostgreSQL.
- Ngrok para exponer el backend local.
- Cuenta o instancia de N8N.
- Twilio Sandbox o integracion WhatsApp equivalente.
- API key de Google Gemini.
- Node.js solo si se desea ejecutar el frontend opcional.

## Instalacion

Clona el repositorio desde la rama `fase-3`:

```bash
git clone -b fase-3 https://github.com/JhonatanTC99/taller_1.git
cd taller_1
```

Instala las dependencias del backend:

```bash
cd backend
uv sync
```

Crea el archivo de variables de entorno a partir del ejemplo:

```bash
cp .env.example .env
```

Configura como minimo estos valores en `backend/.env`:

```env
LLM_PROVIDER=google
AGENT_PROVIDER=google
GOOGLE_API_KEY=tu_api_key_aqui
GOOGLE_MODEL=gemini-3.1-flash-lite
AGENT_MODEL=gemini-3.1-flash-lite
ENABLE_AGENT_V3=true
ENABLE_HITL=false
ENABLE_CONVERSATION_LOGGING=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dollarcity_agent
CHECKPOINT_TABLE_PREFIX=dollarcity_agent
```

## Ejecucion Del Backend

Desde la carpeta `backend/`, levanta PostgreSQL:

```bash
docker compose up -d
```

Si es la primera ejecucion o se requiere regenerar la base de conocimiento, ejecuta el flujo completo de ingesta, curacion e indexacion:

```bash
uv run python main.py --full
```

Para iniciar solo el servidor FastAPI:

```bash
uv run python main.py --server
```

El backend queda disponible en:

```text
http://127.0.0.1:8000
```

Tambien se puede usar el arranque rapido desde la raiz del proyecto:

```bash
./start.sh
```

En Windows:

```bat
start.bat
```

Estos scripts levantan PostgreSQL con Docker Compose e inician el servidor FastAPI.

## Contrato Del Endpoint Principal

Endpoint productivo para N8N, WhatsApp, Telegram u otros canales:

```text
POST /api/channel/chat
```

Payload esperado:

```json
{
  "user_id": "573001234567",
  "message": "Cual es el horario de Dollarcity?",
  "channel": "whatsapp",
  "metadata": {
    "message_id": "opcional",
    "source": "n8n"
  }
}
```

Respuesta esperada:

```json
{
  "content": "Respuesta final del agente",
  "status": "success",
  "model": "gemini-3.1-flash-lite",
  "session_id": "573001234567",
  "channel": "whatsapp",
  "tool_used": "consultar_dato_corporativo",
  "source_type": "json_db",
  "docs_count": null,
  "timing_ms": null,
  "metadata": {
    "agent_v3": true,
    "legacy_bridge": false
  }
}
```

## Conexion Con WhatsApp, N8N Y Ngrok

Con el backend corriendo, abre otra terminal y expone el puerto local:

```bash
ngrok http 8000
```

En N8N, configura el nodo HTTP Request para enviar mensajes al endpoint:

```text
https://tu-url-ngrok.ngrok-free.app/api/channel/chat
```

Ejemplo de payload desde Twilio:

```json
{
  "user_id": "{{ $json.body.WaId }}",
  "message": "{{ $json.body.Body }}",
  "channel": "whatsapp",
  "metadata": {
    "from": "{{ $json.body.From }}",
    "message_sid": "{{ $json.body.MessageSid }}"
  }
}
```

Para responder en el ultimo nodo de Twilio, mapea el texto del agente con:

```text
{{ $json.content }}
```

## Endpoints De Validacion Local

El backend tambien conserva endpoints utiles para pruebas locales y compatibilidad:

- `GET /`: estado basico del backend.
- `GET /debug`: configuracion activa, feature flags y modelo.
- `GET /api/llm-health`: prueba de conexion con el proveedor LLM.
- `GET /api/rag-diagnostics`: diagnostico de ChromaDB y RAG.
- `GET /api/summary`: resumen corporativo.
- `GET /api/faq`: preguntas frecuentes.
- `POST /api/chat`: chat legacy usado por la interfaz web local.
- `POST /api/rag-debug`: inspeccion de fragmentos recuperados por RAG.

## Frontend Opcional

El frontend React/Vite no es requerido para la Fase 3 ni para el flujo N8N/WhatsApp. Se conserva como consola local de demostracion y validacion para `/api/chat`, `/api/summary` y `/api/faq`.

Para ejecutarlo:

```bash
cd frontend
npm install
npm run dev
```

La interfaz usa por defecto:

```text
http://localhost:8000/api
```

## Evaluacion Y Pruebas

Desde `backend/`, ejecuta la bateria de preguntas:

```bash
uv run python tests/questions.py
```

El resultado se genera en:

```text
backend/data/evaluation_results.csv
```

Esta evaluacion permite revisar latencia, seleccion de herramientas, recuperacion RAG y calidad de respuesta.

## Comandos Utiles

Desde la raiz del proyecto:

```bash
make backend
make frontend
make pipeline
make lint
```

Nota: `make run-all` conserva pasos historicos asociados a Ollama. Para Fase 3 con Gemini, se recomienda usar `./start.sh`, `start.bat` o los comandos directos del backend descritos arriba.

## Estado Del Entregable

La Fase 3 queda orientada al flujo productivo:

- Backend FastAPI operativo.
- Endpoint `/api/channel/chat` para integraciones externas.
- Agente LangGraph/LangChain con herramientas tipadas.
- Persistencia conversacional en PostgreSQL.
- RAG con ChromaDB.
- Integracion demostrable con N8N, Ngrok y WhatsApp/Twilio.

Proyecto academico desarrollado para la Maestria en Ciencia de Datos e IA.
