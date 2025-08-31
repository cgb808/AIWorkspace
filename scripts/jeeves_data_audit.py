#!/usr/bin/env python3
"""Data audit for Jeeves training artifacts.

Computes basic stats & duplicate detection across hybrid + RAG usage + optional rag batch msgpack files.
"""
from __future__ import annotations
import argparse, json, hashlib, glob, os
from pathlib import Path


def sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def audit_dataset(records, key_a: str, key_b: str):
    hashes = [sha(r.get(key_a, '') + '||' + r.get(key_b, '')) for r in records]
    dup_count = len(hashes) - len(set(hashes))
    lens_a = [len(r.get(key_a, '')) for r in records]
    lens_b = [len(r.get(key_b, '')) for r in records]
    return {
        'count': len(records),
        'duplicates': dup_count,
        'avg_' + key_a + '_len': (sum(lens_a)/len(lens_a)) if lens_a else 0,
        'avg_' + key_b + '_len': (sum(lens_b)/len(lens_b)) if lens_b else 0,
        'hash_coverage': len(set(hashes))
    }


def main():  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument('--hybrid', required=True)
    ap.add_argument('--rag-usage', required=True)
    ap.add_argument('--rag-batch-glob')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    hybrid = load_jsonl(Path(args.hybrid))
    rag_usage = load_jsonl(Path(args.rag_usage))
    rag_batches_found = glob.glob(args.rag_batch_glob) if args.rag_batch_glob else []
    payload = {
        'hybrid': audit_dataset(hybrid, 'instruction', 'response'),
        'rag_usage': audit_dataset(rag_usage, 'question', 'answer'),
        'rag_batch_files': rag_batches_found,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2))
    print(f"[audit] wrote {args.out}")


if __name__ == '__main__':
    main()
