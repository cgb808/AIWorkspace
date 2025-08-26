# ZenGlow RAG Infrastructure Setup

## Prerequisites
- Docker & Docker Compose installed
- Python 3.10+ (for local dev)


## Quickstart
1. Copy `.env.example` to `.env` and adjust secrets as needed.
2. Build and start Ollama and API services:
   ```bash
   docker-compose up --build
   ```
3. Ensure external databases (Postgres, Redis, Chroma) are running and accessible from the API container.
4. Access API at `http://localhost:8000`.

## Services
- **ollama**: Local LLM inference
- **api**: FastAPI app (RAG, health, embedding endpoints)

> Note: The API connects to external databases (Postgres, Redis, Chroma) via environment variables. These services are not managed by this compose file and must be available separately.

## Development

### Virtual Environment (Recommended)

Create and populate a local venv (handles missing ensurepip fallback):

```bash
make venv        # creates .venv (bootstraps pip if needed)
make dev-setup   # installs runtime + dev deps
source .venv/bin/activate
make test        # run tests
make serve       # start API (uvicorn)
```

If venv creation warns about ensurepip missing, the Makefile target attempts a manual pip bootstrap. On Debian/Ubuntu you can also install system package support:
```bash
sudo apt-get update && sudo apt-get install -y python3-venv
```

### Running Tests
```bash
make test
```

### Formatting & Lint
```bash
make fmt
make lint
```
### Environment Setup
```bash
make setup
cp .env.example .env  # then edit secrets
```

### Common Tasks
| Action | Command |
|--------|---------|
| Format code | `make fmt` |
| Lint (ruff + mypy) | `make lint` |
| Run tests | `make test` |
| Full check (lint + tests) | `make check` |
| Dev server (FastAPI reload) | `make serve` |
| Whisper.cpp setup | `make whisper-setup` |
| Print key RAG env weights | `make print-env` |

### Caching Layers
1. Feature cache (Redis, short TTL) stores feature vectors + LTR scores.
2. Full response cache keyed by query + top_k (invalidated when fusion weights change).

### Scoring
Fusion: `fused = w_ltr * norm(ltr) + w_concept * conceptual_similarity`. Weights env-configured (`RAG_FUSION_LTR_WEIGHT`, `RAG_FUSION_CONCEPTUAL_WEIGHT`). Normalization: min-max per request.

### Legacy Code Removal
Deprecated modules (`app/rag/embeddings.py`, `app/rag/retrieval.py`) removed; `/rag/query` now delegates to `/rag/query2` logic.

### Pre-Commit
Install hooks:
```bash
pre-commit install
```
Hooks run ruff (auto-fix), black, isort, mypy (non-blocking).

### Folder Highlights
| Path | Purpose |
|------|---------|
| `app/rag/ranking_router.py` | Retrieval + feature assembly + LTR + fusion |
| `app/rag/feature_assembler.py` | Feature schema v1 (similarity, log_length, bias) |
| `app/rag/pipeline.py` | End-to-end RAG pipeline (conceptual scoring) |
| `scripts/setup_whisper_cpp.sh` | Local speech-to-text build & model fetch |
| `app/audio/transcription_router.py` | `/audio/transcribe` endpoint |
| `docs/TASK_CHECKLIST.md` | Rolling implementation status |

### DevOps Tracking
See `DEVOPS.md` for evolving operational tasks (CI, metrics, deployment strategy).

## Extending
- Add new endpoints in `app/main.py` and modules in `app/rag/`.
- Add migrations to `sql/migrations/`.
- Add tests to `tests/`.

---
For more details, see `docs/AGENT_BOOTSTRAP_CONTEXT.md` and `docs/MEMORY_RAG_INTEGRATION.md`.
