# =========================
# CONFIGURACIÓN GLOBAL
# =========================
BACKEND_DIR=backend
FRONTEND_DIR=frontend

APP=main:app
PORT=8000

PYTHON=python
UV=uv

LLM_MODEL ?= gemma3:1b
AUTO_APPROVE ?= 0

# =========================
# DETECCIÓN DE OS
# =========================
ifeq ($(OS),Windows_NT)
    FIND_CMD = findstr
    CAT_CMD = type
    NULL_DEV = NUL
    RM_FILE = del /Q
    RM_DIR = rmdir /S /Q
else
    FIND_CMD = grep -q
    CAT_CMD = cat
    NULL_DEV = /dev/null
    RM_FILE = rm -f
    RM_DIR = rm -rf
endif

# =========================
# SETUP
# =========================
setup:
	@echo "Configurando backend..."
	cd $(BACKEND_DIR) && $(UV) sync
	cd $(BACKEND_DIR) && $(UV) run playwright install chromium

	@echo "Configurando frontend..."
	cd $(FRONTEND_DIR) && npm install

	@echo "Verificando Ollama..."
	@ollama list >$(NULL_DEV) 2>&1 || (echo "Ollama no está instalado o no corre" && exit 1)

	@echo "Setup completo"

# =========================
# MODELO
# =========================
check-model:
	@echo "Verificando modelo $(LLM_MODEL)..."
	@ollama list > temp_ollama.txt 2>$(NULL_DEV) || (echo "Error ejecutando ollama" && exit 1)
	@$(CAT_CMD) temp_ollama.txt | $(FIND_CMD) "$(LLM_MODEL)" >$(NULL_DEV) 2>&1 || \
	( \
		echo "Modelo $(LLM_MODEL) NO está instalado."; \
		if [ "$(AUTO_APPROVE)" = "1" ]; then \
			echo "⬇ Descargando automáticamente..."; \
			ollama pull $(LLM_MODEL) || exit 1; \
		else \
			echo "Modelo no instalado."; \
			echo "Ejecuta:"; \
			echo "   make run-all AUTO_APPROVE=1"; \
			$(RM_FILE) temp_ollama.txt; \
			exit 1; \
		fi \
	)
	@$(RM_FILE) temp_ollama.txt

serve-model:
	@echo "Levantando modelo..."
	@ollama run $(LLM_MODEL)

model:
	@echo "Modo interactivo..."
	ollama run $(LLM_MODEL)

# =========================
# PIPELINE
# =========================
pipeline:
	@echo "Ejecutando pipeline..."
	cd $(BACKEND_DIR) && $(UV) run python main.py --full

# =========================
# BACKEND
# =========================
backend:
	@echo "Iniciando backend..."
	cd $(BACKEND_DIR) && $(UV) run uvicorn $(APP) --reload --host 0.0.0.0 --port $(PORT)

# =========================
# FRONTEND
# =========================
frontend:
	@echo "Iniciando frontend..."
	cd $(FRONTEND_DIR) && npm run dev

# =========================
# DEV (sin background raro)
# =========================
dev:
	@echo "Ejecuta backend y frontend en terminales separadas:"
	@echo "make backend"
	@echo "make frontend"

# =========================
# RUN TODO
# =========================
run-all:
	@echo "Ejecutando sistema completo..."
	$(MAKE) setup
	$(MAKE) check-model
	$(MAKE) serve-model
	$(MAKE) pipeline
	@echo "Ahora ejecuta: make dev"

# =========================
# SCRAPING / DATA
# =========================
scrape:
	cd $(BACKEND_DIR) && $(UV) run python main.py --scrape

clean-data:
	cd $(BACKEND_DIR) && $(UV) run python main.py --clean

chat:
	cd $(BACKEND_DIR) && $(UV) run python main.py --chat

# =========================
# LIMPIEZA (PORTABLE)
# =========================
clean:
	@echo "Limpiando..."
	$(RM_DIR) $(BACKEND_DIR)/.venv
	$(RM_DIR) $(BACKEND_DIR)/__pycache__
	$(RM_DIR) $(BACKEND_DIR)/.pytest_cache
	$(RM_DIR) $(BACKEND_DIR)/data/raw
	$(RM_DIR) $(BACKEND_DIR)/data/knowledge_base
	$(RM_DIR) $(FRONTEND_DIR)/node_modules

reset: clean setup

# =========================
# LINT
# =========================
lint:
	cd $(BACKEND_DIR) && $(UV) run ruff check .

format:
	cd $(BACKEND_DIR) && $(UV) run ruff format .

# =========================
# HELP
# =========================
help:
	@echo ""
	@echo "COMANDOS:"
	@echo "make run-all                 -> Todo automático"
	@echo "make run-all AUTO_APPROVE=1  -> Descarga modelo automática"
	@echo "make backend                -> API"
	@echo "make frontend               -> UI"
	@echo "make dev                    -> Instrucciones dev"
	@echo ""