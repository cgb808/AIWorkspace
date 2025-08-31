#!/usr/bin/env python3
"""Apply SQL migrations in sql/migrations/ (idempotent).

Creates schema_migrations(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now()).
Each migration file is applied exactly once (ordered lexicographically by filename).

Usage:
  python scripts/apply_migrations.py            # Uses env DATABASE_URL or discrete PG* vars
  DRY_RUN=1 python scripts/apply_migrations.py  # Show planned migrations only

Environment precedence (same as DBClient): DATABASE_URL -> SUPABASE_DB_URL -> SUPABASE_DIRECT_URL -> PG*.
"""
from __future__ import annotations

import os, sys, glob, psycopg2, psycopg2.extras, textwrap
from pathlib import Path

MIGRATIONS_DIR = Path("sql/migrations")

def _connect():
    dsn = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or os.getenv("SUPABASE_DIRECT_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE") or os.getenv("PG_DB", "rag_db"),
        user=os.getenv("PGUSER") or os.getenv("PG_USER", "postgres"),
        password=os.getenv("PGPASSWORD") or os.getenv("PG_PASSWORD", "password"),
        host=os.getenv("PGHOST") or os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PGPORT") or os.getenv("PG_PORT", "5432")),
    )

def list_migrations() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(MIGRATIONS_DIR / "*.sql")))

def load_sql(path: Path) -> str:
    sql = path.read_text(encoding="utf-8")
    # Strip leading Python-style triple quoted comment blocks if present
    if sql.lstrip().startswith("\"\"\""):
        parts = sql.split("\"\"\"", 2)
        if len(parts) == 3:
            sql = parts[2]
    return sql.strip()

def ensure_migrations_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )

def fetch_applied(cur) -> set[str]:
    cur.execute("SELECT version FROM schema_migrations")
    return {r[0] for r in cur.fetchall()}

def apply(conn, path: Path, dry_run: bool = False):
    version = path.name
    sql = load_sql(path)
    if not sql:
        print(f"[skip] {version} (empty)")
        return
    if dry_run:
        print(f"[plan] Would apply {version} ({len(sql.splitlines())} lines)")
        return
    with conn.cursor() as cur:
        print(f"[apply] {version}")
        cur.execute(sql)
        cur.execute("INSERT INTO schema_migrations(version) VALUES (%s) ON CONFLICT DO NOTHING", (version,))
    conn.commit()

def main():  # pragma: no cover
    dry_run = os.getenv("DRY_RUN") == "1"
    migrations = list_migrations()
    if not migrations:
        print("[info] No migration files found")
        return 0
    try:
        conn = _connect()
    except Exception as e:
        print(f"[error] DB connect failed: {e}")
        return 2
    try:
        with conn.cursor() as cur:
            ensure_migrations_table(cur)
            applied = fetch_applied(cur)
        pending = [m for m in migrations if m.name not in applied]
        if not pending:
            print("[info] No pending migrations")
            return 0
        for m in pending:
            apply(conn, m, dry_run=dry_run)
        if dry_run:
            print(f"[plan] {len(pending)} migration(s) would be applied")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
