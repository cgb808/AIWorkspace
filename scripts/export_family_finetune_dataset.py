"""Export fine-tuning dataset for family contextual knowledge.

Builds JSONL examples combining:
  * user_memory_items (individual & group visibility)
  * chunks (tagged with inside_joke / event / persona tags)
  * finetune_examples (curated prompt-response pairs) if present

Strategy:
  1. Gather candidate memories & chunks filtered by tenant, optional user/group.
  2. For each memory, produce a synthetic prompt/response pair if not already curated
     (e.g., prompt: "Remember: <content>" response: acknowledgement) -- flagged synthetic.
  3. For each curated finetune_examples row, emit as-is.
  4. Merge and shuffle deterministically (seed) for epoch training.

Environment:
  DATABASE_URL (pg connection string) OR PG_* vars.
  EXPORT_TENANT_ID (default 0)
  EXPORT_USER_ID / EXPORT_GROUP_ID (optional filters)
  EXPORT_LIMIT (max synthetic examples)
  EXPORT_OUT (output path, default data/finetune/family_dataset.jsonl)

Usage (example):
  python scripts/export_family_finetune_dataset.py
"""

from __future__ import annotations

import json
import os
import pathlib
import random
from typing import Any, Dict, List

import psycopg2
import psycopg2.extras

TENANT_ID = int(os.getenv("EXPORT_TENANT_ID", "0"))
USER_ID = os.getenv("EXPORT_USER_ID")
GROUP_ID = os.getenv("EXPORT_GROUP_ID")
LIMIT = int(os.getenv("EXPORT_LIMIT", "500"))
OUT_PATH = os.getenv("EXPORT_OUT", "data/finetune/family_dataset.jsonl")
SEED = int(os.getenv("EXPORT_SEED", "42"))


def _conn():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        dbname=os.getenv("PG_DB", "rag_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "password"),
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
    )


def fetch_rows(cur, sql: str, params: tuple) -> List[Dict[str, Any]]:
    cur.execute(sql, params)
    rows = cur.fetchall() or []
    return [dict(r) for r in rows]


def main():
    random.seed(SEED)
    pathlib.Path(os.path.dirname(OUT_PATH)).mkdir(parents=True, exist_ok=True)
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            filters_mem = ["tenant_id=%s", "archived=FALSE"]
            params_mem: List[Any] = [TENANT_ID]
            if USER_ID:
                filters_mem.append("(user_id=%s OR visibility IN ('group','global'))")
                params_mem.append(int(USER_ID))
            if GROUP_ID:
                filters_mem.append("(group_id=%s OR visibility='global')")
                params_mem.append(int(GROUP_ID))
            where_mem = " AND ".join(filters_mem)
            mem_sql = f"""
                SELECT id, user_id, group_id, content, visibility, meta
                FROM user_memory_items
                WHERE {where_mem}
                ORDER BY created_at DESC
                LIMIT %s
            """
            params_mem.append(LIMIT)
            memories = fetch_rows(cur, mem_sql, tuple(params_mem))

            # Tagged chunks (inside jokes / events)
            chunk_sql = """
                SELECT c.id, c.text, array_agg(t.tag) AS tags
                FROM chunks c
                JOIN tag_assignments ta ON ta.chunk_id = c.id
                JOIN tags t ON t.id = ta.tag_id
                WHERE c.tenant_id=%s
                  AND t.category IN ('inside_joke','event','persona','family_fact')
                GROUP BY c.id, c.text
                LIMIT %s
            """
            chunks = fetch_rows(cur, chunk_sql, (TENANT_ID, LIMIT))

            curated_sql = """
                SELECT id, prompt, response, tags, meta
                FROM finetune_examples
                WHERE tenant_id=%s
                ORDER BY created_at DESC
                LIMIT %s
            """
            curated = fetch_rows(cur, curated_sql, (TENANT_ID, LIMIT))

    examples: List[Dict[str, Any]] = []
    # Curated direct
    for row in curated:
        examples.append(
            {
                "messages": [
                    {"role": "user", "content": row["prompt"]},
                    {"role": "assistant", "content": row["response"]},
                ],
                "meta": {
                    "tags": row.get("tags"),
                    "curated": True,
                    **(row.get("meta") or {}),
                },
            }
        )
    # Synthetic from memories
    for m in memories:
        content = m["content"]
        prompt = f"Recall context: {content}"
        response = "Acknowledged. This will inform future personalized responses."  # neutral ack
        examples.append(
            {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                ],
                "meta": {
                    "source": "memory",
                    "visibility": m.get("visibility"),
                    "synthetic": True,
                    "user_id": m.get("user_id"),
                    "group_id": m.get("group_id"),
                },
            }
        )
    # Synthetic from tagged chunks
    for ch in chunks:
        txt = ch["text"]
        tags = ch.get("tags") or []
        prompt = (
            f"Family context reference ({', '.join(tags)}): {txt[:200]}"
            if tags
            else f"Family context reference: {txt[:200]}"
        )
        response = (
            "Noted. I'll use this shared family context when helpful."  # neutral ack
        )
        examples.append(
            {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                ],
                "meta": {"source": "chunk", "tags": tags, "synthetic": True},
            }
        )

    random.shuffle(examples)
    with open(OUT_PATH, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Exported {len(examples)} examples -> {OUT_PATH}")


if __name__ == "__main__":
    main()
