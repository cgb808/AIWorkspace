#!/usr/bin/env python
"""Batch ingest for RAG doc embeddings.
Usage:
  python scripts/rag_ingest.py --source docs --file path/to/file.txt
  python scripts/rag_ingest.py --source guide --glob 'docs/**/*.md'

Splits text into ~800 char chunks, embeds via local /model/embed endpoint, inserts into Postgres doc_embeddings.
"""
from __future__ import annotations
import os, argparse, glob, json, textwrap
import requests, psycopg2
from typing import List

EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "http://127.0.0.1:8000/model/embed")
DSN = os.getenv("DATABASE_URL")
CHUNK_SIZE = 800
OVERLAP = 80

def read_text(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def chunk_text(txt: str) -> List[str]:
    txt = txt.replace('\r','')
    chunks=[]; start=0; n=len(txt)
    while start < n:
        end = min(start+CHUNK_SIZE, n)
        seg = txt[start:end].strip()
        if seg:
            chunks.append(seg)
        start = end - OVERLAP
        if start < 0: start = 0
        if start >= n: break
    return chunks

def embed(chunks: List[str]) -> List[List[float]]:
    r = requests.post(EMBED_ENDPOINT, json={"texts": chunks}, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["embeddings"]

def insert(rows):
    if not DSN:
        raise SystemExit("DATABASE_URL not set")
    import psycopg2
    from psycopg2.extras import execute_values
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            execute_values(cur,
                "INSERT INTO doc_embeddings (source, chunk, embedding, batch_tag) VALUES %s",
                rows)

def process(paths: List[str], source: str, batch_tag: str):
    all_rows=[]
    for p in paths:
        txt = read_text(p)
        chunks = chunk_text(txt)
        if not chunks:
            continue
        embs = embed(chunks)
        for c,e in zip(chunks, embs):
            all_rows.append((source, c, e, batch_tag))
    if all_rows:
        insert(all_rows)
    return len(all_rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--file')
    ap.add_argument('--glob')
    ap.add_argument('--batch-tag', default='manual_ingest')
    args = ap.parse_args()
    paths=[]
    if args.file:
        paths.append(args.file)
    if args.glob:
        paths.extend(glob.glob(args.glob, recursive=True))
    if not paths:
        raise SystemExit('Provide --file or --glob')
    total = process(paths, args.source, args.batch_tag)
    print(f"Ingested rows: {total}")

if __name__ == '__main__':
    main()
