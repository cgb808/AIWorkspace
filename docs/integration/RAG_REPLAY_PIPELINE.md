# RAG Replay & Offline Artifact Ingestion

Covers utilities that (re)ingest previously exported / offline‑generated retrieval artifacts back into `doc_embeddings` and keep a directory of MessagePack batches synchronized with the database.

## Components
| Script | Purpose |
|--------|---------|
| `scripts/rag_replay_msgpack.py` | One‑shot replay of one or many `.msgpack` batch files into Postgres (optionally re‑embedding). |
| `scripts/rag_replay_watch.py` | Polling watcher that continuously discovers new batch files and replays them (stateful restart). |
| `scripts/replay_msgpack_ingest.py` | Legacy/minimal ingest (kept for back‑compat) – simple re‑embed if missing. |
| `scripts/rag_training_example_builder.py` | Generates synthetic RAG usage examples (Q/A pairs) with optional MsgPack sibling for training. |

## Batch File Structure (MessagePack)
Typical keys produced by upstream exporters (`rag_ingest.py --msgpack-out ...`):
```
{
  "version": 1,
  "source": "docs" | "memory" | custom,
  "batch_tag": "rag_batch_docs_...",
  "created_at": <iso/epoch>,
  "embedding_dim": 768,
  "records": [
     {"text": "...", "embedding": [...]/optional, "metadata": {...}, "source": "docs", "batch_tag": "..."}
  ]
}
```

## Replay Scenarios
| Scenario | Flags | Notes |
|----------|-------|-------|
| Ingest pre‑embedded batches | none (default) | Existing `embedding` vectors inserted directly. |
| Force fresh embeddings | `--reembed` | Replaces any stored embedding (model evolution). |
| Fill missing embeddings with zeros | `--dummy-fill 768` | Useful for dry structural loading before model ready. |
| Avoid re‑inserting duplicates (within replay set) | (default) | Content hashes computed and deduped in‑memory. |
| Skip hashes already in DB | `--skip-existing` | DB lookup by `metadata.content_hash`. |
| Throttle embedding throughput | `--embed-batch-size N --sleep S` | Micro‑batching + optional sleep. |

## Core Script Usage
### One‑Shot Replay
```bash
python scripts/rag_replay_msgpack.py \
  --glob 'data/msgpack/rag_batch_*.msgpack' \
  --reembed --embed-batch-size 32 --skip-existing
```

### Continuous Watch
```bash
python scripts/rag_replay_watch.py \
  --glob 'data/msgpack/*.msgpack' \
  --interval 15 --skip-existing --dummy-fill 768 --state-file data/msgpack/.replay_state.json
```
State file holds processed filename list (JSON array) to skip on restart.

## Environment
```
DATABASE_URL / SUPABASE_DB_URL   # Postgres DSN (pgvector installed)
EMBED_ENDPOINT                   # HTTP embedding endpoint (default http://127.0.0.1:8000/model/embed)
```

## Content Hashing
`metadata.content_hash` preserved if present, else SHA256 of raw text is injected so later dedup logic (`--skip-existing`) works uniformly.

## Failure Modes & Recovery
| Issue | Mitigation |
|-------|------------|
| Endpoint timeout | Re‑run with `--dummy-fill` to stage rows; backfill embeddings later with `--reembed`. |
| Partial batch crash | Idempotent due to per‑row hash filtering on rerun. |
| Large backlog | Run one‑shot with higher `--embed-batch-size`; then start watcher. |

## Future Enhancements
- Metrics emission (ingested rows/sec, embedding latency).
- Optional async worker queue instead of inline HTTP calls.
- Automatic archival / compression of replayed batch files.

---
See also: `docs/MEMORY_RAG_INTEGRATION.md` for live memory ingestion.
