# Makefile for ZenGlow RAG Dev Workflow

PYTHON ?= python
PIP ?= pip
PROJECT_NAME := zenglow

.DEFAULT_GOAL := help

## ---- Helper ----
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sed -e 's/:.*##/\t-/' | sort

## ---- Environment ----
setup: ## Install runtime + dev dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

venv: ## Create virtual environment (.venv) with ensurepip fallback
	@if [ -d .venv ]; then echo ".venv already exists"; else \
		$(PYTHON) -m venv .venv 2>/dev/null || echo "venv creation reported error (ensurepip missing?)"; \
		if [ ! -f .venv/bin/pip ]; then echo "Bootstrapping pip"; curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && .venv/bin/python get-pip.py; fi; \
	fi

dev-setup: venv ## Create venv (if missing) & install deps
	. .venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && pip install -r requirements-dev.txt

freeze: ## Export resolved dependencies (runtime only)
	$(PIP) freeze > requirements.lock

## ---- Quality ----
fmt: ## Run code formatters (black, isort, ruff --fix)
	ruff check --fix . || true
	isort .
	black .

lint: ## Run linters (ruff + mypy)
	ruff check .
	mypy . || true

check: lint test ## Run lint + tests

## ---- Tests ----
pytest_args ?=

test: ## Run pytest
	$(PYTHON) -m pytest -q $(pytest_args)

## ---- Dev Server ----
serve: ## Run FastAPI dev server
	uvicorn app.main:app --reload --port 8000

## ---- Caching / Artifacts ----
clear-cache: ## Flush Redis (DANGEROUS: requires REDIS_* vars)
	python -c 'import os,redis; r=redis.Redis(host=os.getenv("REDIS_HOST","localhost"),port=int(os.getenv("REDIS_PORT","6379")),db=int(os.getenv("REDIS_DB","0"))); r.flushdb(); print("Flushed")'

## ---- Docs ----
docs-open: ## Open local docs index if exists
	@if [ -f docs/INDEX.md ]; then $(PYTHON) -c 'import webbrowser; webbrowser.open("docs/INDEX.md")'; else echo "docs/INDEX.md missing"; fi

## ---- Utilities ----
whisper-setup: ## Run whisper.cpp setup script
	bash scripts/setup_whisper_cpp.sh

print-env: ## Print key RAG env settings
	@echo RAG_FUSION_LTR_WEIGHT=${RAG_FUSION_LTR_WEIGHT}
	@echo RAG_FUSION_CONCEPTUAL_WEIGHT=${RAG_FUSION_CONCEPTUAL_WEIGHT}
	@echo EMBED_ENDPOINT=${EMBED_ENDPOINT}

.PHONY: help setup freeze fmt lint check test serve clear-cache docs-open whisper-setup print-env
