# ZenGlow RAG Infrastructure Setup

Documentation domains now live under `docs/` but the canonical project overview remains this root README for developer onboarding.

Key Doc Links:
- Main Docs Index: `docs/DOCS_INDEX.md`
- DevOps Practices: `docs/devops/DEVOPS.md`
- DevOps Project Strategy: `docs/devops/DEVOPS_PROJECT.md`
- Testing Guide: `docs/testing/AGENT_TEST_EXECUTION.md`
- Deployment: `docs/deployment/PRODUCTION_DEPLOYMENT.md`
- Security (RLS): `docs/security/RLS_POLICY_REFERENCE.md`
- Workspace Layout: `docs/workspace/REMOTE_WORKSPACE_LAYOUT.md`
- SOPs: `docs/sop/AI_TERMINAL_SOP.md`

## Prerequisites
- Docker & Docker Compose installed
- Python 3.10+ (for local dev)
- Multi-GPU setup: RTX 3060 Ti + GTX 1660 Super
- NVIDIA Container Toolkit for GPU support

## Current AI Architecture
## AI Architecture

The system utilizes a multi-GPU setup with specialized AI personalities:

- **Leonardo** (Mistral 7B Q5_K_M on RTX 3060 Ti): Analytical reasoning and deep thinking
  - Fine-tunable for family context and educational excellence
  - Personalized tutoring capabilities with family values integration
- **Jarvis** (Phi3 Q4_0 on GTX 1660 Super): Conversational assistance and TTS integration

Both models are containerized using Ollama with NVIDIA Container Toolkit for efficient GPU resource management.

### Fine-Tuning Capabilities

Leonardo supports family-specific fine-tuning with a two-epoch approach:
1. **Epoch 1**: Family context integration (history, values, learning styles)
2. **Epoch 2**: Educational excellence (world-class tutoring capabilities)

See `docs/LEONARDO_FINE_TUNING.md` for comprehensive implementation details.
- **Specialized workload distribution**: Deep thinking vs. conversational interaction

## Quickstart
1. Copy `.env.example` to `.env` and adjust secrets as needed.
2. Build and start Ollama and API services:
   ```bash
   docker-compose up --build
   ```
3. Ensure external databases (Postgres, Redis, Chroma) are running and accessible from the API container.
4. Access API at `http://localhost:8000`.

## Services
- **ollama**: Local LLM inference (multi-GPU distributed)
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

### Python 3.12 Environment for Embeddings
Transformers/tokenizers currently lag Python 3.13 support. For full embedding features use Python 3.12:
```bash
bash scripts/setup_py312_env.sh
source .venv312/bin/activate
```
Extra embedding deps live in `requirements-embed.txt` (installed by the script). Fallback hash embeddings work without it.

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
See `docs/devops/DEVOPS.md` for evolving operational tasks (CI, metrics, deployment strategy).

## Extending
- Add new endpoints in `app/main.py` and modules in `app/rag/`.
- Add migrations to `sql/migrations/`.
- Add tests to `tests/`.

---
For more details, see `docs/AGENT_BOOTSTRAP_CONTEXT.md` and `docs/MEMORY_RAG_INTEGRATION.md`.

## Docker Compose Usage & Nuances

The provided `docker-compose.yml` spins up:
1. `backend` (FastAPI) on host port 8000
2. `ollama` (LLM server) internal port 11434, mapped to host 11435 if 11434 already in use
3. `open-webui` (optional UI) on port 3000
4. `redis` (if enabled in compose) on 6379

Key behaviors / gotchas:
- A host-level `uvicorn` or prior container can block port 8000; run `make compose-restart` or manually kill the process.
- If you already have a host Ollama listening on 11434, the compose file maps the container to 11435 externally. Adjust mapping back to `11434:11434` if you prefer and no host conflict.
- Backend outbound LLM calls are restricted unless allowed by `LLM_ALLOW_PREFIXES` (set to `http://ollama:`) or `LLM_ALLOW_EXTERNAL=1`.
- To rebuild cleanly: `make compose-restart` (performs down -> build -> up -> health wait).
- To simply start existing images: `make compose-up`.
- Health check uses `/health`; ensure that endpoint stays lightweight.

Common commands:
```bash
make compose-up        # start stack
make compose-restart   # full rebuild & restart
docker compose logs -f backend
curl -s localhost:8000/llm/probe | jq
```

Troubleshooting:
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `address already in use` on 8000 | Host uvicorn still running | `fuser -k 8000/tcp` or `make compose-restart` |
| Ollama container stuck `created` | Port 11434 bound by host ollama | Change mapping or stop host service |
| `blocked outbound (ollama)` in probe | Outbound restriction without prefix | Ensure `LLM_ALLOW_PREFIXES` contains `http://ollama:` or set `LLM_ALLOW_EXTERNAL=1` |
| Backend health timeout in restart | Slow image build or app crash | Check `docker compose logs backend` |


## Runtime Indexing & Memory (Knowledge Capture)
An automated lightweight index of Python modules can be generated via:

```
python scripts/index_codebase.py
```

This produces `project-index-runtime.json` with module hashes & LOC and (optionally) seeds the in‑process model registry. Set `HINT_MODELS="name:family,name2:family2"` to append additional model stubs.

Archived / deprecated experimental folders are moved into `archive/` and intentionally excluded from future planning. The index script should ignore `archive/` (future enhancement) to keep noise low.

Memory / MCP Guidance: Key architectural summaries (RAG pipeline, active models, cleaned workspace state) should be persisted via the Memory MCP so subsequent agent tasks can quickly orient without re‑scanning the tree.

### Snapshot & Restore Utilities
Two helper scripts manage versioned knowledge-graph snapshots:

| Script | Purpose |
|--------|---------|
| `scripts/memory-save.mjs` | Create timestamped `run-YYYYMMDD-HHMMSS` snapshot and update `latest` pointer. |
| `scripts/memory-restore.mjs` | Restore a snapshot back into graph root or just repoint `latest`. |

Examples:
```bash
node scripts/memory-save.mjs --note "post-instrumentation"
node scripts/memory-restore.mjs --run run-20250827-120301 --clean-root
```

Environment override: set `KNOWLEDGE_GRAPH_ROOT` to control snapshot location.

## GemmaPhi Chat UI (Live)
The React dashboard includes a `GemmaPhi` page (route `/gemma-phi`, or via Dashboard link) providing a minimal multi‑agent chat:

Features (implemented):
- Dual agent comparison (toggle Dual Mode) with backend selection: `auto | edge | ollama | llama`.
- Persona selection (`persona_key` passed to backend).
- Stage timing + backend + latency display (data from `answer_meta.timings` when available).
- Piper TTS playback (voices: amy, jarvis, alan, southern_male) with mute + volume.
- Whisper.cpp STT recording (MediaRecorder → `/audio/transcribe`).
- Backend health indicator (pings `/metrics/basic`).

### Minimal Chat Stack Quickstart (1–8)
1. Clone repo & create `.env` (copy from template if present).
2. Prepare Python env & deps:
   - `make venv && make dev-setup`
3. Build whisper.cpp & download model:
   - `make whisper-setup` (default model `small.en`).
4. Install / place Piper binary & models:
   - Ensure `vendor/piper/piper` exists & executable.
   - Place ONNX models under `models/piper/` (e.g. `en_US-amy-low.onnx`).
   - Export voice alias env vars if using alternates (see below).
5. Start API (FastAPI dev):
   - `make serve` (listens on `:8000`).
6. Build dashboard (one‑time or after UI edits):
   - `make dashboard-build` (copies into `app/static/dashboard`).
7. Visit dashboard:
   - `http://localhost:8000/dashboard` → navigate /gemma-phi (SPA route) or link.
8. Test endpoints manually (sanity):
   - `curl -X POST localhost:8000/rag/query -H 'Content-Type: application/json' -d '{"query":"hello"}'`
   - `curl localhost:8000/metrics/basic`
   - `curl -X POST localhost:8000/audio/tts -H 'Content-Type: application/json' -d '{"text":"Test voice","voice":"amy","format":"base64"}'`
   - `curl -F file=@<wav_or_webm> localhost:8000/audio/transcribe`

If the health pill shows `backend: down`, verify server running & `fetch /metrics/basic` returns 200.

### Audio (TTS / STT) Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `PIPER_BIN` | Path to Piper binary | `vendor/piper/piper` |
| `PIPER_MODEL` | Default voice model | `models/piper/en_US-amy-low.onnx` |
| `PIPER_JARVIS_MODEL` | Jarvis/Alan alias base | `models/piper/en_GB-alan-low.onnx` |
| `PIPER_ALAN_MODEL` | Alan alias (fallback to JARVIS) | (same as jarvis) |
| `PIPER_SOUTHERN_MALE_MODEL` | Southern male voice | `models/piper/en_GB-southern_english_male-low.onnx` |
| `WHISPER_CPP_DIR` | whisper.cpp directory | `vendor/whisper.cpp` |
| `WHISPER_MODEL` | Whisper model name | `small.en` |

Voices are selected in UI by alias; if a model path doesn’t exist the `/audio/tts` call returns 500.

### Notes
- Direct navigation to `/gemma-phi` may require a catch‑all route; entering via `/dashboard` ensures SPA assets loaded.
- Stage timings require active retrieval path; if retrieval fails you may still get a fallback answer without timings.

## Archived Directories
Relocated to `archive/` (kept for reference, not active development):
`dashboard (copy)`, `dashboard_handoff (copy)`, `extracted_zip`, `gemma_phi_ui`, `model_finetune_quant (copy)` and several zip artifacts. These should not be modified; create new feature work under current `frontend/dashboard` or `app/`.

## Metrics Dashboard
The React metrics dashboard lives in `frontend/dashboard` and is served (after build) at `/dashboard`.

### Build & Sync (copies optimized assets to `app/static/dashboard`)
```bash
make dashboard-build
```
Then visit:
```
http://localhost:8000/dashboard
```

### Fast Rebuild After Edits
Inside `frontend/dashboard`:
```bash
npm run build && cp -r dist/* ../../app/static/dashboard/
```

### API Endpoint Used
The UI polls `GET /metrics/dashboard` every 15s (override with `VITE_METRICS_URL` at build time if needed).

### Auth Header (Optional)
If `X_ZENDEXER_KEY` env/API key protection is enabled, enter the key in the password field in the toolbar and the dashboard will include it as `X-Zendexer-Key`.

### Notes
- No Node runtime needed in production if you build once; only static files are served.
- Rebuild only when dashboard source changes.
- Make target `dashboard-build` ensures assets stay in sync.

## Frontend Metrics Polling Controls (New)
Add these to your dashboard build env (e.g. `.env` consumed by Vite) to reduce or eliminate network polling during troubleshooting:

| Variable | Effect | Default |
|----------|--------|---------|
| `VITE_DISABLE_METRICS` | Hides metrics panels entirely, chat iframe still available | `0` |
| `VITE_DISABLE_METRICS_POLLING` | Disables automatic interval polling (manual Refresh button only) | `0` |
| `VITE_METRICS_POLL_INTERVAL_MS` | Interval between polls when enabled (min enforced 10000 ms) | `30000` |
| `VITE_METRICS_MANUAL_COOLDOWN_MS` | Minimum time between manual refresh clicks | `5000` |
| `VITE_METRICS_URL` | Override metrics endpoint path | `/metrics/dashboard` |

Example `.env.dashboard`:
```bash
VITE_DISABLE_METRICS=1
VITE_DISABLE_METRICS_POLLING=1
VITE_METRICS_POLL_INTERVAL_MS=60000
VITE_METRICS_MANUAL_COOLDOWN_MS=8000
VITE_METRICS_URL=/metrics/dashboard
```

When both `VITE_DISABLE_METRICS=1` and `VITE_DISABLE_METRICS_POLLING=1` are set, network chatter from metrics is fully suppressed.
