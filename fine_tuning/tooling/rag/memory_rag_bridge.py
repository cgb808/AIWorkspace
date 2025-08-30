#!/usr/bin/env python
"""Memory ↔ RAG Bridge

Watches an MCP memory server file (JSONL) and ingests new memories into the
`doc_embeddings` table for semantic retrieval.

Env Vars:
  MEMORY_FILE_PATH (required) - path used by @modelcontextprotocol/server-memory
  DATABASE_URL (required)     - Postgres DSN with pgvector
  EMBED_ENDPOINT (optional)   - HTTP endpoint that accepts {"texts": [...]} and returns {"embeddings": [...]}
                                default: http://127.0.0.1:8000/model/embed
  BATCH_SIZE (optional)       - Number of memory lines to batch per embedding call (default 16)
  LOOP_INTERVAL (optional)    - Seconds to sleep between polling cycles (default 2)

CLI Usage:
  python memory_rag_bridge.py --once      # Run single sync pass then exit
  python memory_rag_bridge.py --search "query text" --top-k 5
  python memory_rag_bridge.py             # Continuous tail + ingest

Assumptions:
  * Memory file is append-only JSON Lines where each line is a JSON object containing at least:
      id (string/number), content (string), created_at (ISO) or timestamp.
    If fields differ, map them in `_extract_text`.
  * Duplicate prevention via storing a hash of content in doc_embeddings.batch_tag or using a dedicated table.
"""
from __future__ import annotations
import os, time, json, hashlib, argparse, sys
from dataclasses import dataclass
from typing import List, Optional
import psycopg2
from psycopg2.extras import execute_values
import requests

EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "http://127.0.0.1:8000/model/embed")
DSN = os.getenv("DATABASE_URL")
MEM_PATH = os.getenv("MEMORY_FILE_PATH")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))
LOOP_INTERVAL = float(os.getenv("LOOP_INTERVAL", "2"))

if not DSN:
    print("[bridge] DATABASE_URL not set", file=sys.stderr)
if not MEM_PATH:
    print("[bridge] MEMORY_FILE_PATH not set", file=sys.stderr)

@dataclass
class MemoryLine:
    raw: dict
    text: str
    content_hash: str

def _extract_text(obj: dict) -> str:
    # Adaptable mapping logic.
    if 'content' in obj:
        c = obj['content']
        if isinstance(c, dict) and 'text' in c:
            return str(c['text'])
        return str(c)
    # Fallback join of string values
    parts = []
    for k,v in obj.items():
        if isinstance(v, str):
            parts.append(v)
    return " | ".join(parts)

def load_ingested_hashes(conn) -> set:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_ingest_dedup (
              content_hash TEXT PRIMARY KEY,
              inserted_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        cur.execute("SELECT content_hash FROM memory_ingest_dedup")
        return {r[0] for r in cur.fetchall()}

def mark_hashes(conn, hashes: List[str]):
    with conn.cursor() as cur:
        execute_values(cur,
            "INSERT INTO memory_ingest_dedup(content_hash) VALUES %s ON CONFLICT DO NOTHING",
            [(h,) for h in hashes])

def embed_texts(texts: List[str]) -> List[List[float]]:
    r = requests.post(EMBED_ENDPOINT, json={"texts": texts}, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data['embeddings']

def insert_embeddings(conn, mems: List[MemoryLine], vectors: List[List[float]]):
    rows = []
    for m, vec in zip(mems, vectors):
        rows.append(("memory", m.text, vec, m.content_hash))
    with conn.cursor() as cur:
        execute_values(cur,
            "INSERT INTO doc_embeddings (source, chunk, embedding, batch_tag) VALUES %s ON CONFLICT DO NOTHING",
            rows)

def tail_once(state):
    new_lines = []
    with open(MEM_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(state['offset'])
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            state['offset'] = f.tell()
            line=line.strip()
            if not line:
                continue
            try:
                obj=json.loads(line)
            except Exception:
                continue
            txt=_extract_text(obj)
            if not txt:
                continue
            h=hashlib.sha256(txt.encode('utf-8')).hexdigest()
            new_lines.append(MemoryLine(obj, txt, h))
    return new_lines

def process_new():
    if not (DSN and MEM_PATH):
        return
    with psycopg2.connect(DSN) as conn:
        dedup = load_ingested_hashes(conn)
        state={'offset':0}
        # Recover previous offset if we store it in a sidecar? (Future)
        while True:
            mems = [m for m in tail_once(state) if m.content_hash not in dedup]
            if mems:
                # batch embed
                for i in range(0, len(mems), BATCH_SIZE):
                    batch=mems[i:i+BATCH_SIZE]
                    vecs=embed_texts([m.text for m in batch])
                    insert_embeddings(conn, batch, vecs)
                    mark_hashes(conn, [m.content_hash for m in batch])
                    dedup.update(m.content_hash for m in batch)
                print(f"[bridge] Ingested {len(mems)} new memory lines")
            if ARGS.once:
                break
            time.sleep(LOOP_INTERVAL)

def similarity_search(query: str, top_k: int):
    if not DSN:
        print("DATABASE_URL not set", file=sys.stderr); return
    # Embed query
    vec = embed_texts([query])[0]
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT chunk, 1 - (embedding <-> %s::vector) AS score
                FROM doc_embeddings
                WHERE source='memory'
                ORDER BY embedding <-> %s::vector
                LIMIT %s
            """, (vec, vec, top_k))
            rows=cur.fetchall()
            for r in rows:
                print(f"[score={r[1]:.4f}] {r[0][:160]}")

parser = argparse.ArgumentParser()
parser.add_argument('--once', action='store_true', help='Single pass ingest then exit')
parser.add_argument('--search', type=str, help='Run a semantic search instead of ingest loop')
parser.add_argument('--top-k', type=int, default=int(os.getenv('RAG_TOP_K_DEFAULT', '5')))
ARGS = parser.parse_args()

def main():
    if ARGS.search:
        similarity_search(ARGS.search, ARGS.top_k)
    else:
        process_new()

if __name__ == '__main__':
    main()
