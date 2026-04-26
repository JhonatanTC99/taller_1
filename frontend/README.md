# Dollarcity AI – Knowledge Assistant

Sistema inteligente de consulta basado en LLM que permite interactuar con información oficial de Dollarcity Colombia mediante un pipeline completo de scraping, curación semántica y generación de respuestas.
---

## Elaborado Por:
 - John Carmona
 - Jhonatan Tapia
 - Erica Márquez
 - Luis Meza

---

## Arquitectura del Proyecto

El sistema está dividido en tres grandes componentes:

### 1. Ingesta de Datos (Scraping)
- Extracción automatizada desde el sitio oficial
- Herramienta: `Crawl4AI + Playwright`

### 2. Curación Semántica
- Limpieza, estructuración y normalización de contenido
- Generación de una base de conocimiento confiable (KB)

### 3. Motor de IA (LLM)
- Modelo local usando `Ollama`
- Funcionalidades:
  - Resumen ejecutivo
  - Generación de FAQ
  - Chat Q&A contextual

### 4. API Backend
- Framework: `FastAPI`
- Expone endpoints consumidos por el frontend

### 5. Frontend
- Framework: `React + Vite`
- UI moderna con:
  - TailwindCSS
  - Framer Motion
  - React Markdown



## Tecnologías Utilizadas

### Backend
- Python 3.11+
- FastAPI
- LangChain
- Ollama
- Crawl4AI
- Playwright
- Uvicorn

### Frontend
- React
- Vite
- TailwindCSS
- Framer Motion
- Lucide Icons
- React Markdown

---

## Instalación del Proyecto

### 1. Clonar repositorio

```bash
git clone https://github.com/JhonatanTC99/taller_1.git
cd taller_1

```

## Configuración por Sistema Operativo

### Linux

1. Instalar dependencias

```bash
sudo apt update
sudo apt install python3 python3-pip nodejs npm make -y
```

2. Instalar UV

```bash
pip install uv
```

3. Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

```

4. Ejecutar el sistema

```bash
make run-all

```

Si el modelo no está instalado:
```bash
make run-all AUTO_APPROVE=1

```


### macOS

1. Instalar Homebrew (si no lo tienes)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

```

2. Instalar dependencias

```bash
brew install python node make
pip install uv
```

3. Instalar Ollama
Descargar desde: https://ollama.com

O con brew:

```bash
brew install ollama
```

4. Ejecutar el sistema
```bash
make run-all
```
Si falta el modelo:

```bash
make run-all AUTO_APPROVE=1
```

### Windows

1. Instalar herramientas
Python: https://www.python.org/downloads/
Node.js: https://nodejs.org/
Git: https://git-scm.com/

2. Instalar UV
```bash
pip install uv
```
3. Instalar Ollama
https://ollama.com/download

Asegúrate de que esté corriendo

4. Ejecutar
```bash
make run-all
```

Si falta el modelo:

```bash
make run-all AUTO_APPROVE=1
```