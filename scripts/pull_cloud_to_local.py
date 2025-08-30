#!/usr/bin/env python
"""Convenience wrapper to pull core RAG & personalization tables from cloud (Supabase) to local.

Env expectations:
  SUPABASE_DB_URL   Cloud Postgres DSN (or DATABASE_URL already pointing to cloud)
Optional overrides:
  LOCAL_DSN         Defaults to postgresql://postgres:postgres@localhost:5432/rag_db
  TABLES            Comma list override. Default set declared below.
Usage:
  python scripts/pull_cloud_to_local.py
"""
from __future__ import annotations
import os, sys, subprocess, shlex

DEFAULT_TABLES = [
  'users','groups','group_memberships','user_traits','user_persona_prefs',
  'user_sessions','user_memory_items','user_embeddings','documents','chunks','chunk_features',
  'tags','tag_assignments','finetune_examples'
]

def main():
  cloud = (
    os.getenv('SUPABASE_DB_URL')
    or os.getenv('SUPABASE_DIRECT_URL')
    or os.getenv('SUPABASE_POOLER_URL')
    or os.getenv('DATABASE_URL')
  )
  if not cloud:
    print('ERROR: Set one of SUPABASE_DB_URL / SUPABASE_DIRECT_URL / SUPABASE_POOLER_URL / DATABASE_URL to cloud DSN', file=sys.stderr)
    return 2
  local = os.getenv('LOCAL_DSN','postgresql://postgres:postgres@localhost:5432/rag_db')
  tables = os.getenv('TABLES')
  if tables:
    table_list = [t.strip() for t in tables.split(',') if t.strip()]
  else:
    table_list = DEFAULT_TABLES
  cmd = [sys.executable,'scripts/transfer_tables_between_dbs.py','--source',cloud,'--target',local,'--tables',','.join(table_list)]
  print('Running:',' '.join(shlex.quote(c) for c in cmd))
  return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
