# Remote Workspace Optimal Layout (Indexer / RAG Node)

> Scope: Minimal-yet-complete structure to operate the indexer (FastAPI + RAG + Ollama proxy) on a remote GPU/CPU host. Marked (existing ✅ / planned 🆕 ).

```
dev-indexer_1/                          # Service root (rename to indexer/ in future?)
  app/                                   # Application code
    __init__.py 🆕
    main.py ✅                            # FastAPI entrypoint (extend with RAG endpoints)
    core/ 🆕                              # Cross-cutting utilities
      __init__.py 🆕
      config.py 🆕                        # Env parsing / settings (Pydantic BaseSettings)
      logging.py 🆕                       # Structured logger setup
    rag/ 🆕                               # Retrieval-Augmented Generation logic
      __init__.py 🆕
      embeddings.py 🆕                    # Embed model abstraction + batching
      store_pg.py 🆕                      # pgvector CRUD + similarity queries
      retrieval.py 🆕                     # Top‑K retrieval orchestration
      pipeline.py 🆕                      # End-to-end RAG compose + generation
      schemas.py 🆕                       # Pydantic models for RAG endpoints
    health/ 🆕                            # Health & readiness probes
      __init__.py 🆕
      ollama.py 🆕
      db.py 🆕
  scripts/                               # One-off operational utilities
    remote_ollama_bootstrap.sh ✅         # One-shot remote Ollama setup
    ollama_steps.sh ✅                    # Stepwise Ollama operations
    rag_ingest.py ✅                      # Batch embed + insert into Postgres
    model_smoke_test.py ✅ (if present)   # GPU / model capability probe
    storage_validate.sh ✅ (if present)   # ZFS / disk inspection
  sql/                                   # Schema + index artifacts
    rag_core_schema.sql ✅                # Core tables + hypertable
    rag_indexes.sql ✅                    # Vector indexes (IVF/HNSW)
    migrations/ 🆕                        # Timestamped, idempotent SQL migration files
      2025_08_25_0001_init.sql 🆕
  docs/                                  # Human + machine reference
    AGENT_BOOTSTRAP_CONTEXT.md ✅
    api_collection.postman.json ✅
    REMOTE_WORKSPACE_LAYOUT.md 🆕         # (this file)
    agent_bootstrap_context.json ✅
  tests/ 🆕                               # Automated tests (pytest)
    __init__.py 🆕
    test_health.py 🆕
    test_rag_pipeline.py 🆕
  data_sources/ ✅ (existing)             # Raw / sample ingest assets
  test_data/ ✅                           # Sample docs for ingestion
  requirements.txt ✅                     # Base dependencies (cpu)
  requirements-gpu.txt ✅                 # GPU variants / extra packages
  pyproject.toml ✅                       # (If migrating to unified build system)
  .env.example ✅                         # Template env config
  start.sh ✅ (if used)                   # Entrypoint launcher
  Dockerfile ✅                           # Container build for indexer
  docker-compose.yml ✅ (if scoping)      # Local service orchestration
```

## Directory Purpose Summary

| Path | Purpose |
|------|---------|
| `app/` | Service logic split into cohesive domains (core, rag, health). |
| `scripts/` | Operational + maintenance utilities (bootstrap, ingestion, storage checks). |
| `sql/` | Declarative schema & performance index definitions; migrations for reproducibility. |
| `docs/` | Human / agent onboarding, API examples, architectural context. |
| `tests/` | Regression & interface guarantees (health, RAG correctness, perf smoke). |
| `data_sources/` | External raw or staged inputs. |
| `test_data/` | Lightweight corpus for local ingest & CI validation. |

## Recommended Module Contracts

| Module | Key Functions / Classes | Notes |
|--------|-------------------------|-------|
| `core.config` | `Settings(BaseSettings)` | Centralized env ingestion (DB URL, model path, top_k). |
| `core.logging` | `get_logger()` | Structured logging (JSON lines) enabling ingestion into Loki/ELK. |
| `rag.embeddings` | `Embedder.embed(texts: List[str]) -> List[Vector]` | Swappable backend (HF, Ollama, remote service). |
| `rag.store_pg` | `upsert_embeddings(...)`, `similarity_search(query_vec, k)` | Encapsulate pgvector SQL & tuning. |
| `rag.retrieval` | `retrieve(query: str, k: int)` | Orchestrates embed + store search. |
| `rag.pipeline` | `generate_rag(query)` | Composes context + calls LLM (Ollama). |
| `health.ollama` | `check()` | Fast model & service ping (timeout bounded). |
| `health.db` | `check()` | Simple `SELECT 1` + extension presence validation. |

## Migration Strategy

Place each change in `sql/migrations/YYYY_MM_DD_nn_description.sql` and ensure idempotence:
```sql
-- Example 2025_08_25_0001_init.sql
BEGIN;
CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ DEFAULT now()
);
-- guard
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE id='2025_08_25_0001_init') THEN
  -- core objects
  CREATE TABLE IF NOT EXISTS ... ;
  INSERT INTO schema_migrations(id) VALUES ('2025_08_25_0001_init');
END IF; END $$;
COMMIT;
```

## Test Coverage Targets

| Test | Goal |
|------|------|
| `test_health.py` | All health endpoints return 200 and expected JSON keys. |
| `test_rag_pipeline.py` | Embedding dimension matches config, retrieval returns <=k, generation includes at least one retrieved snippet. |
| `performance_smoke` (optional) | RAG end-to-end under threshold (e.g., <1.5s on warm cache for tiny corpus). |

## Minimal Viable Deployment (Remote)
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt` (or GPU variant)
3. Apply `sql/rag_core_schema.sql` (and indexes when scale warrants).
4. Export env vars or copy `.env.example` -> `.env`.
5. `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
6. Ingest sample docs: `python scripts/rag_ingest.py --source quick --glob 'test_data/*.txt'`.
7. Query: POST `/rag/query`.

## Growth Path
| Phase | Enhancement |
|-------|-------------|
| 1 | Basic pgvector exact search + small corpus. |
| 2 | IVF / HNSW indexes + background refresh. |
| 3 | Add caching layer (Redis) for repeated queries. |
| 4 | Add tracing (OpenTelemetry) + metrics export. |
| 5 | Multi-tenant namespace column & row-level policies. |

## Legend
✅ = Exists now in repository
🆕 = Recommended addition (scaffold not yet created)

---
Generated to guide remote agent workspace normalization.
