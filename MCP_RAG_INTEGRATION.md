# MCP Memory ↔ RAG Integration

Goal: Leverage the MCP `server-memory` storage file as a continuously ingested semantic knowledge base powering RAG queries and contextual generation.

## Components
| Component | Purpose |
|----------|---------|
| `@modelcontextprotocol/server-memory` | Produces JSONL memory file (append-only). |
| `memory_rag_bridge.py` | Tails memory file, embeds new lines, stores vectors in Postgres. |
| `doc_embeddings` (pgvector) | Unified semantic store (source='memory' rows). |
| FastAPI `/rag/query` (planned) | Retrieves + composes context for LLM generation. |

## Data Flow
1. User / agents write conversational or event entries → memory server appends JSON object per line.
2. Bridge script polls file tail, extracts text, deduplicates via SHA-256 hash.
3. Text batch embedded via `EMBED_ENDPOINT` (FastAPI /model/embed).
4. Embeddings inserted into `doc_embeddings` with `source='memory'` and hash recorded in `memory_ingest_dedup`.
5. RAG queries include memory-derived context using similarity on `source='memory'` (or union with other sources).

```
Memory JSONL --> memory_rag_bridge --> embeddings --> pgvector(doc_embeddings) --> RAG retrieval --> LLM
```

## Setup
1. Ensure Postgres + pgvector schema applied (`sql/rag_core_schema.sql`).
2. Export env vars:
```bash
export MEMORY_FILE_PATH=/path/to/mcp_memory.jsonl
export DATABASE_URL=postgresql://user:pass@localhost:5432/zenglow
export EMBED_ENDPOINT=http://127.0.0.1:8000/model/embed
```
3. Start bridge (continuous):
```bash
python dev-indexer_1/mcp/memory_rag_bridge.py
```
4. One-off sync:
```bash
python dev-indexer_1/mcp/memory_rag_bridge.py --once
```
5. Semantic search CLI:
```bash
python dev-indexer_1/mcp/memory_rag_bridge.py --search "optimize vector retrieval" --top-k 5
```

## VS Code Integration (mcp.json Suggestion)
Add a new custom MCP server entry that can issue semantic search commands by shelling to the bridge script, or extend existing memory server with a secondary indexer. Example addition:
```jsonc
"memory-rag-search": {
  "type": "stdio",
  "command": "python",
  "args": ["dev-indexer_1/mcp/memory_rag_bridge.py", "--once"],
  "env": {
    "MEMORY_FILE_PATH": "${input:memory_file_path}",
    "DATABASE_URL": "${input:database_url}",
    "EMBED_ENDPOINT": "http://127.0.0.1:8000/model/embed"
  },
  "gallery": false
}
```
Or create a background task in `.vscode/tasks.json`:
```jsonc
{
  "label": "Memory→RAG Bridge",
  "type": "shell",
  "command": "bash -lc 'source .venv/bin/activate 2>/dev/null || true; python dev-indexer_1/mcp/memory_rag_bridge.py'",
  "problemMatcher": [],
  "isBackground": true
}
```

## Deduplication
* Table `memory_ingest_dedup` stores `content_hash`.
* Replays produce no duplicate embeddings.

## Extending Retrieval
Merge memory + document context:
```sql
(
  SELECT chunk, embedding <-> $Q AS dist FROM doc_embeddings WHERE source='memory'
  UNION ALL
  SELECT chunk, embedding <-> $Q AS dist FROM doc_embeddings WHERE source='docs'
) ORDER BY dist ASC LIMIT $K;
```

## Future Enhancements
| Theme | Idea |
|-------|------|
| Scaling | Switch to asynchronous embedding queue (Redis + worker). |
| Quality | Add summarization pass before storing to reduce duplication. |
| Governance | Add PII redaction hook. |
| Freshness | Provide TTL cleanup for stale memory vectors. |
| Metrics | Count ingested lines, embedding latency histogram, similarity latency. |

## Failure Modes & Recovery
| Issue | Mitigation |
|-------|-----------|
| Bridge crash mid-batch | Idempotent dedup table prevents duplicates. Re-run resumes. |
| Memory file rotation | Detect inode change & reset offset (add TODO hook). |
| Embed endpoint timeout | Retry with exponential backoff (future enhancement). |

---
This bridge enables the assistant to ground responses in persisted MCP memory through unified pgvector retrieval.
