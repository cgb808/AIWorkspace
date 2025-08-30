#!/usr/bin/env python
"""Transfer selected tables between two Postgres databases (local <-> cloud).

Usage examples:
  # Push core RAG tables to cloud
  python scripts/transfer_tables_between_dbs.py --source $LOCAL_DSN --target $CLOUD_DSN --tables documents,chunks,chunk_features,users,groups,user_memory_items

  # Pull finetune examples back local
  python scripts/transfer_tables_between_dbs.py --source $CLOUD_DSN --target $LOCAL_DSN --tables finetune_examples

Notes:
  - Simple approach: TRUNCATE target tables then COPY data over (destructive!).
  - Requires both DSNs passed explicitly (so we don't confuse precedence envs).
  - Assumes identical schemas already applied on both ends.
  - Skips sequences auto (IDENTITY) because COPY preserves values; optionally resets.
"""
from __future__ import annotations
import argparse, psycopg2, sys
from psycopg2 import sql


def open_conn(dsn: str):
    return psycopg2.connect(dsn)


def truncate(cur, table: str):
    cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(sql.Identifier(table)))


def copy_table(src_conn, tgt_conn, table: str):
    print(f"Transferring {table} ...")
    with src_conn.cursor() as s, tgt_conn.cursor() as t:
        # check existence
        s.execute("SELECT to_regclass(%s)", (table,))
        if not s.fetchone()[0]:
            print(f"  Source missing {table}, skipping")
            return
        t.execute("SELECT to_regclass(%s)", (table,))
        if not t.fetchone()[0]:
            print(f"  Target missing {table}, skipping")
            return
        truncate(t, table)
        import io
        buf = io.BytesIO()
        s.copy_expert(f"COPY {table} TO STDOUT WITH (FORMAT binary)", buf)
        buf.seek(0)
        t.copy_expert(f"COPY {table} FROM STDIN WITH (FORMAT binary)", buf)
    tgt_conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='Source DSN')
    ap.add_argument('--target', required=True, help='Target DSN')
    ap.add_argument('--tables', required=True, help='Comma list of tables to transfer')
    args = ap.parse_args()

    tables = [t.strip() for t in args.tables.split(',') if t.strip()]
    src = open_conn(args.source)
    tgt = open_conn(args.target)
    try:
        for tbl in tables:
            copy_table(src, tgt, tbl)
        print('Done.')
    finally:
        src.close(); tgt.close()

if __name__ == '__main__':
    main()
