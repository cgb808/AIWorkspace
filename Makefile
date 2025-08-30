########################################
# ZenGlow RAG Dev Workflow Makefile
########################################

PYTHON ?= python
PIP ?= pip
API_PORT ?= 8000

.DEFAULT_GOAL := help

## ---- Helper ----
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sed -e 's/:.*##/\t-/' | sort

## ---- Environment ----
venv: ## Create virtual environment (.venv) if missing
	@if [ -d .venv ]; then echo ".venv already exists"; else $(PYTHON) -m venv .venv || true; fi

setup: venv ## Install runtime + dev deps (no torch specialization)
	. .venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt -r requirements-dev.txt

freeze: ## Export resolved dependencies (runtime only)
	. .venv/bin/activate && pip freeze > requirements.lock

deps-gpu-or-cpu: ## GPU-first dependency install with CPU torch fallback
	@set -e; \
	if [ ! -d .venv ]; then echo "Creating venv"; $(PYTHON) -m venv .venv; fi; \
	. .venv/bin/activate; \
	pip install --upgrade pip setuptools wheel; \
	if command -v nvidia-smi >/dev/null 2>&1; then \
	  echo "[deps] GPU detected -> installing requirements (torch will resolve GPU build)"; \
	  pip install -r requirements.txt; \
	else \
	  echo "[deps] No GPU detected -> installing CPU torch first"; \
	  pip install --force-reinstall --index-url https://download.pytorch.org/whl/cpu torch; \
	  pip install -r requirements.txt; \
	fi; \
	pip install -r requirements-dev.txt; \
	python -c 'import fastapi, torch, transformers; print("[deps] Smoke import OK")'

## ---- Quality ----
fmt: ## Run formatters
	. .venv/bin/activate && ruff check --fix . || true
	. .venv/bin/activate && isort .
	. .venv/bin/activate && black .

lint: ## Run linters
	. .venv/bin/activate && ruff check .
	. .venv/bin/activate && mypy . || true

check: lint test ## Lint + tests

## ---- Tests ----
pytest_args ?=
test: ## Run pytest
	. .venv/bin/activate && python -m pytest -q $(pytest_args)

## ---- Dev Server ----
serve: ## Run FastAPI dev server
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

chat-dev: ## Run API + dashboard dev (Vite)
	@if [ -f .api_pid ]; then OLD_PID=`cat .api_pid`; if ps -p $$OLD_PID >/dev/null 2>&1; then echo "Stopping previous API $$OLD_PID"; kill $$OLD_PID || true; fi; rm -f .api_pid; fi; \
	if ss -ltn | grep -q ':$$API_PORT '; then echo "Port $$API_PORT busy - freeing"; fuser -k $$API_PORT/tcp || true; fi; \
	(. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port $$API_PORT & echo $$! > .api_pid); \
	cd frontend/dashboard && npm run dev; \
	echo "Shutting down API dev server"; \
	if [ -f .api_pid ]; then kill `cat .api_pid` || true; rm .api_pid; fi

stop: ## Stop API dev server
	@if [ -f .api_pid ]; then kill `cat .api_pid` || true; rm .api_pid; echo "Stopped"; else echo "No running API"; fi

## ---- Containers ----
pg-up: ## Start disposable Postgres
	docker run -d --name zenglow-pg -e POSTGRES_USER=zenglow -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=zenglow -p 5432:5432 postgres:15-alpine >/dev/null 2>&1 || echo "Already running?"
	@echo "Postgres starting..."

pg-down: ## Remove disposable Postgres
	-docker rm -f zenglow-pg >/dev/null 2>&1 || true
	@echo "Postgres removed"

ollama-down: ## Remove ollama container
	-docker rm -f ollama >/dev/null 2>&1 || true
	@echo "Ollama removed (if existed)"

redis-down: ## Remove redis container
	-docker rm -f zenglow-redis >/dev/null 2>&1 || true
	@echo "Redis removed (if existed)"

stack-down: ## Remove all known containers
	-docker rm -f ollama zenglow-redis zenglow-pg zenglow-backend open-webui >/dev/null 2>&1 || true
	@echo "Stack containers removed"

compose-up: ## Bring up docker compose stack (build if needed)
	docker compose up -d
	docker compose ps

compose-restart: ## Full rebuild: down (wait) -> build -> up -> health check
	@echo "[compose] Stopping existing stack (ignore errors)"; \
	  docker compose down --remove-orphans || true; \
	  echo "[compose] Freeing common host ports (8000,11434,11435)"; \
	  fuser -k 8000/tcp 2>/dev/null || true; \
	  fuser -k 11434/tcp 2>/dev/null || true; \
	  fuser -k 11435/tcp 2>/dev/null || true; \
	  echo "[compose] Building images (pull latest bases)"; \
	  docker compose build --pull; \
	  echo "[compose] Starting services"; \
	  docker compose up -d; \
	  echo "[compose] Waiting for backend health endpoint (max 45s)"; \
	  timeout 45 bash -c 'until curl -sf localhost:8000/health >/dev/null 2>&1; do sleep 2; done' || echo "[compose] Backend health timed out"; \
	  docker compose ps

## ---- Builds ----
dashboard-build: ## Build full dashboard
	cd frontend/dashboard && npm run build
	mkdir -p app/static/dashboard && cp -r frontend/dashboard/dist/* app/static/dashboard/
	@echo "Dashboard synced"

dashboard-build-nometrics: ## Build dashboard without metrics polling
	cd frontend/dashboard && VITE_DISABLE_METRICS=1 npm run build
	mkdir -p app/static/dashboard && cp -r frontend/dashboard/dist/* app/static/dashboard/
	@echo "Dashboard (no metrics) synced"

chat-build: ## Build chat-only UI (metrics disabled)
	cd frontend/dashboard && VITE_DISABLE_METRICS=1 npm run build
	mkdir -p app/static/dashboard && cp -r frontend/dashboard/dist/* app/static/dashboard/
	@echo "Chat UI build complete"

## ---- Utilities ----
clear-cache: ## Flush Redis DB (dangerous)
	. .venv/bin/activate && python -c 'import os,redis; r=redis.Redis(host=os.getenv("REDIS_HOST","localhost"),port=int(os.getenv("REDIS_PORT","6379")),db=int(os.getenv("REDIS_DB","0"))); r.flushdb(); print("Flushed")'

whisper-setup: ## Setup whisper.cpp (build binary)
	bash scripts/setup_whisper_cpp.sh

print-env: ## Print key env vars
	@echo RAG_FUSION_LTR_WEIGHT=${RAG_FUSION_LTR_WEIGHT}
	@echo RAG_FUSION_CONCEPTUAL_WEIGHT=${RAG_FUSION_CONCEPTUAL_WEIGHT}
	@echo EMBED_ENDPOINT=${EMBED_ENDPOINT}

## ---- Governance / SOP ----
sop-sync: ## Ensure AI_TERMINAL_SOP.md symlinks exist across common project roots
	@if [ ! -f AI_TERMINAL_SOP.md ]; then echo "Canonical AI_TERMINAL_SOP.md missing"; exit 1; fi
	. .venv/bin/activate 2>/dev/null || true; python3 scripts/create_sop_symlinks.py --paths \
	  .venv frontend infrastructure gemma_phi_ui knowledge-graph fine_tuning scripts supabase app models tests || true
	@echo "[sop-sync] Complete"

## ---- Datasets ----
manifest: ## Build consolidated processed dataset manifest
	python3 fine_tuning/training/scripts/build_dataset_manifest.py --pretty

dedupe-%: ## Deduplicate a JSONL (usage: make dedupe-path=path/to/file.jsonl FIELDS="prompt response")
	@if [ -z "${dedupe_in}" ]; then echo "Provide dedupe_in=... (input .jsonl)"; exit 1; fi; \
	 if [ -z "${dedupe_out}" ]; then echo "Provide dedupe_out=... (output .jsonl)"; exit 1; fi; \
	 FARGS=""; if [ -n "${FIELDS}" ]; then FARGS="--fields ${FIELDS}"; fi; \
	 python3 fine_tuning/training/scripts/dedupe_jsonl.py --in ${dedupe_in} --out ${dedupe_out} $$FARGS

interrupt-gen: ## Regenerate interruption recovery datasets (seed overridable: SEED=42)
	python3 fine_tuning/training/scripts/generate_interruption_recovery_dataset.py --out-dir fine_tuning/datasets/processed/interruption_handling --seed ${SEED}

.PHONY: help venv setup freeze deps-gpu-or-cpu fmt lint check test serve chat-dev stop pg-up pg-down ollama-down redis-down stack-down compose-up compose-restart dashboard-build dashboard-build-nometrics chat-build clear-cache whisper-setup print-env sop-sync manifest dedupe-% interrupt-gen
