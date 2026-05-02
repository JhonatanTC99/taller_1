# Dollarcity AI - Knowledge Assistant

Sistema de consulta basado en modelos de lenguaje para interactuar con una base de conocimiento semantica sobre Dollarcity Colombia. El proyecto corresponde al **Taller 1 - Aplicacion de Tecnicas Avanzadas de IA en Modelos de Lenguaje** y construye un prototipo Q&A a partir de informacion publica recolectada, limpiada y consolidada.

## Integrantes

- ERICA ROCIO MARQUEZ MENESES
- JOHN MARIO CARMONA DAVID
- JHONATAN ANDRES TAPIA CORDOBA
- LUIS FERNANDO MEZA RAMREZ

## Alcance del prototipo

El sistema responde preguntas informativas con base en fuentes publicas sobre Dollarcity Colombia. Su objetivo es demostrar un flujo inicial de construccion de base de conocimiento, Prompt Engineering y Q&A contextual.

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
- Generacion de resumen ejecutivo.
- Generacion automatica de FAQ.
- Chat Q&A contextual.
- API backend con FastAPI.
- Interfaz web de prueba con React + Vite.

## Arquitectura

| Capa | Tecnologia | Funcion |
|---|---|---|
| Ingestion | Python, Crawl4AI, Playwright, BeautifulSoup, httpx, PyMuPDF | Extraer informacion publica desde fuentes web y PDF. |
| Datos crudos | Archivos Markdown en `backend/data/raw/` | Conservar contenido extraido para trazabilidad. |
| Curacion | Python | Limpiar, filtrar, deduplicar y organizar semanticamente el texto. |
| Base de conocimiento | `backend/data/knowledge_base/dollarcity_context.md` | Centralizar el conocimiento usado por el asistente. |
| Motor LLM | LangChain + Ollama | Ejecutar prompts de resumen, FAQ y Q&A. |
| API | FastAPI + Uvicorn | Exponer endpoints consumidos por el frontend. |
| Frontend | React + Vite | Probar resumen, FAQ y chat desde navegador. |

## Modelo LLM

El proyecto se planteo para ejecutarse con `gemma4:latest` mediante Ollama local. Sin embargo, por limitaciones de recursos de hardware durante la ejecucion del prototipo se utilizo `gemma3:1b`, un modelo mas liviano que permite reducir consumo de memoria y tiempo de respuesta.

Configuracion principal:

- Modelo objetivo: `gemma4:latest`.
- Modelo usado localmente por restricciones de hardware: `gemma3:1b`.
- Proveedor: Ollama local.
- Temperatura: `0.2`.
- `top_p`: `0.7`.
- Semilla: `42`.

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
│   │       └── prompts.py
│   ├── data/
│   │   ├── raw/
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
| `/api/chat` | POST | Responder preguntas del usuario. |
| `/debug` | GET | Consultar informacion basica del modelo activo. |

## Preguntas de prueba

La bateria de evaluacion se encuentra en:

```text
backend/tests/questions.py
```

Incluye 20 preguntas sobre identidad corporativa, productos, ubicaciones, pagos, politicas, talento humano, proveedores y casos fuera de dominio.
