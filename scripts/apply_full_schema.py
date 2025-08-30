#!/usr/bin/env python
"""Apply full RAG + personalization + tags schema to a target Postgres.

Usage:
  DATABASE_URL=postgresql://user:pass@host:5432/db python scripts/apply_full_schema.py
  (or) SUPABASE_DB_URL=... python scripts/apply_full_schema.py

This will execute, in order:
  1. sql/init.sql (legacy doc_embeddings + pgvector ext)
  2. sql/artifact_a_schema.sql
  3. sql/artifact_personalization_schema.sql
  4. sql/artifact_personalization_tags.sql

Idempotent: each file already guards with IF NOT EXISTS.
Safe to re-run. Aborts on first failure.
"""
from __future__ import annotations
import os, sys, psycopg2
from pathlib import Path

SQL_FILES = [
    "sql/init.sql",
    "sql/artifact_a_schema.sql",
    "sql/artifact_personalization_schema.sql",
    "sql/artifact_personalization_tags.sql",
]


def get_dsn() -> str:
    dsn = (
        os.getenv("DATABASE_URL")
        or os.getenv("SUPABASE_DB_URL")
        or os.getenv("SUPABASE_DIRECT_URL")
    )
    if not dsn:
        print("ERROR: Set DATABASE_URL or SUPABASE_DB_URL", file=sys.stderr)
        sys.exit(2)
    return dsn


def apply_file(cur, path: Path):
    sql = path.read_text()
    cur.execute(sql)


def main():
    dsn = get_dsn()
    print(f"Applying schema to: {dsn}")
    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                for rel in SQL_FILES:
                    p = Path(rel)
                    if not p.exists():
                        print(f"WARN: missing {rel}, skipping")
                        continue
                    print(f"-- Executing {rel}")
                    apply_file(cur, p)
        print("Schema application complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
