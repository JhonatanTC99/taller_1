# Dollarcity AI - Agente Conversacional

Sistema conversacional basado en modelos de lenguaje para interactuar con una base de conocimiento semantica sobre Dollarcity Colombia. El proyecto corresponde al **Taller 2 - Aplicacion de Tecnicas Avanzadas de IA en Modelos de Lenguaje** y extiende el sistema Q&A del modulo anterior con memoria conversacional, RAG, herramienta de datos estructurados y un router de peticiones.

## Integrantes

- ERICA ROCIO MARQUEZ MENESES
- JOHN MARIO CARMONA DAVID
- JHONATAN ANDRES TAPIA CORDOBA
- LUIS FERNANDO MEZA RAMREZ

## Alcance del prototipo

El sistema responde preguntas informativas con base en fuentes publicas sobre Dollarcity Colombia. Su objetivo es demostrar un flujo incremental de construccion de base de conocimiento, Prompt Engineering, RAG, memoria conversacional y enrutamiento de herramientas.

El prototipo **no tiene acceso a sistemas internos de Dollarcity** y no ejecuta operaciones reales de la empresa. Por tanto:

- No consulta inventario real.
- No confirma disponibilidad de productos por tienda.
- No procesa compras en linea.
- No recibe pagos.
- No genera domicilios.
- No valida ofertas laborales en tiempo real.
- No previene fraudes.

Cuando una consulta requiere informacion actualizada, transaccional o validada directamente por la empresa, el asistente debe orientar al usuario hacia tiendas o canales oficiales.

## Funcionalidades

- Scraping de fuentes publicas web y PDF.
- Limpieza, filtrado, deduplicacion y curacion semantica.
- Consolidacion de una base de conocimiento en Markdown.
- Indexacion y consulta semantica con ChromaDB.
- Generacion de resumen ejecutivo.
- Generacion automatica de FAQ.
- Chat conversacional con historial visible.
- Memoria persistente por sesion mediante historial en archivos.
- Herramienta estructurada basada en JSON para datos exactos.
- Router hibrido para elegir entre RAG, memoria, herramienta estructurada y reglas de negocio.
- API backend con FastAPI.
- Interfaz web de prueba con React + Vite.

## Arquitectura

| Capa | Tecnologia | Funcion |
|---|---|---|
| Ingestion | Python, Crawl4AI, Playwright, BeautifulSoup, httpx, PyMuPDF | Extraer informacion publica desde fuentes web y PDF. |
| Datos crudos | Archivos Markdown en `backend/data/raw/` | Conservar contenido extraido para trazabilidad. |
| Curacion | Python | Limpiar, filtrar, deduplicar y organizar semanticamente el texto. |
| Base de conocimiento | `backend/data/knowledge_base/dollarcity_context.md` | Centralizar el conocimiento usado por el asistente. |
| Base vectorial | ChromaDB + HuggingFace Embeddings | Recuperar fragmentos relevantes para preguntas abiertas. |
| Memoria | LangChain `FileChatMessageHistory` | Guardar historial por sesion y permitir preguntas de seguimiento. |
| Herramienta estructurada | JSON + Python | Responder datos exactos como NIT, telefono, horarios y correos. |
| Router | Python + LangChain | Elegir entre RAG, memoria, herramienta estructurada o reglas. |
| Motor LLM | LangChain + Ollama/Gemini | Ejecutar prompts de resumen, FAQ y respuestas con contexto. |
| API | FastAPI + Uvicorn | Exponer endpoints consumidos por el frontend. |
| Frontend | React + Vite | Probar resumen, FAQ y chat con historial desde navegador. |

Flujo principal del agente:

```text
Usuario -> Frontend React -> API FastAPI -> Router
  -> structured_tool | memory_engine | rule_engine | rag_engine
  -> LLM / respuesta deterministica
  -> historial de sesion
  -> Usuario
```

## Modelo LLM

El proyecto puede ejecutarse con Ollama local o con Google Generative AI, segun variables de entorno. Para la ejecucion local se usa por defecto `gemma3:1b`, un modelo liviano que permite reducir consumo de memoria y tiempo de respuesta.

Configuracion principal:

- Proveedor local por defecto: Ollama.
- Modelo local por defecto: `gemma3:1b`.
- Proveedor alternativo: Google Generative AI.
- Modelo alternativo configurable: `gemini-3.1-flash-lite`.
- Temperatura: `0.1`.
- Embeddings: `all-MiniLM-L6-v2`.

## Estructura principal

```text
.
├── backend/
│   ├── main.py
│   ├── src/
│   │   ├── config/settings.py
│   │   ├── scraper/collector.py
│   │   ├── processor/cleaner.py
│   │   └── engine/
│   │       ├── llm_service.py
│   │       ├── structured_tool.py
│   │       └── prompts.py
│   ├── data/
│   │   ├── chroma_db/
│   │   ├── history/
│   │   ├── raw/
│   │   ├── specific_questions/data_corporativa.json
│   │   └── knowledge_base/dollarcity_context.md
│   └── tests/questions.py
├── frontend/
│   └── src/App.jsx
└── Makefile
```

## Requisitos

- Python 3.12 o superior.
- Node.js y npm.
- Make.
- UV.
- Ollama.

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/JhonatanTC99/taller_1.git
cd taller_1
```

### 2. Instalar dependencias

```bash
make setup
```

Este comando instala dependencias del backend, navegadores requeridos por Playwright y dependencias del frontend.

### 3. Verificar modelo

El `Makefile` usa por defecto `gemma3:1b` para facilitar la ejecucion local:

```bash
make check-model
```

Si el modelo no esta instalado, se puede descargar automaticamente con:

```bash
make check-model AUTO_APPROVE=1
```

Para usar otro modelo compatible con Ollama:

```bash
LLM_MODEL=gemma4:latest make backend
```

## Ejecucion

### Ejecutar scraping

```bash
make scrape
```

### Construir la base de conocimiento curada

```bash
make clean-data
```

Este comando tambien prepara la informacion que utiliza el motor RAG.

### Levantar backend

```bash
make backend
```

La API queda disponible en:

```text
http://localhost:8000
```

### Levantar frontend

```bash
make frontend
```

Vite mostrara la URL local disponible para abrir la interfaz web.

### Chat por consola

```bash
make chat
```

## Endpoints principales

| Endpoint | Metodo | Funcion |
|---|---|---|
| `/` | GET | Verificar que el backend esta en linea. |
| `/api/summary` | GET | Generar resumen ejecutivo. |
| `/api/faq` | GET | Generar preguntas frecuentes. |
| `/api/chat` | POST | Ejecutar el router y responder preguntas del usuario. |
| `/api/rag-diagnostics` | GET | Revisar estado de ChromaDB, contexto y embeddings. |
| `/api/rag-debug` | POST | Consultar fragmentos recuperados sin invocar el LLM. |
| `/api/llm-health` | GET | Validar conectividad con el proveedor LLM. |
| `/debug` | GET | Consultar informacion basica del modelo activo. |

## Herramienta estructurada

La herramienta de datos exactos esta implementada en:

```text
backend/src/engine/structured_tool.py
```

Los datos consultados se almacenan en:

```text
backend/data/specific_questions/data_corporativa.json
```

Esta ruta responde preguntas sobre NIT, telefono, correos, horarios, sede administrativa, ciudades, facturacion, redes y empleo sin usar la base vectorial.

## Memoria conversacional

La memoria usa `FileChatMessageHistory` de LangChain y guarda el historial por sesion en:

```text
backend/data/history/
```

El agente puede recordar informacion declarada dentro de la misma conversacion, por ejemplo:

```text
Usuario: Mi nombre es Erica
Usuario: ¿Como me llamo?
Asistente: Te llamas Erica.
```

## Router del agente

El metodo principal de enrutamiento esta en `backend/src/engine/llm_service.py`. La decision sigue este orden:

1. Preguntas de datos exactos -> `structured_tool`.
2. Preguntas o declaraciones de memoria -> `memory_engine`.
3. Preguntas fuera de dominio o entradas invalidas -> `rule_engine`.
4. Preguntas abiertas sobre Dollarcity -> `rag_engine`.

## Preguntas de prueba

La bateria de evaluacion se encuentra en:

```text
backend/tests/questions.py
```

Incluye pruebas para RAG, memoria, herramienta estructurada y enrutamiento. Los resultados se guardan en:

```text
backend/data/evaluation_results.csv
```

Ejemplos de validacion:

- RAG: `¿Cual es la mision de Dollarcity?`
- Memoria: `Mi nombre es Erica` y luego `¿Como me llamo?`
- Herramienta estructurada: `¿Cual es el horario?`
- Enrutamiento: combinar horario, memoria, mision y una pregunta fuera de dominio.
