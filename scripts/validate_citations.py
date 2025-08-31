"""Validate citation markers in a usage examples JSONL file.

Markers: [D1], [D2], ... appearing in 'response'/'answer' must exist in 'context'.
Warn on gaps (missing intermediate markers).
"""
from __future__ import annotations
import argparse, json, re, sys

PAT = re.compile(r"\[D(\d+)\]")

def extract(s: str):
    return {int(m) for m in PAT.findall(s or '')}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    args = ap.parse_args()
    total=errors=warnings=0
    with open(args.file,'r',encoding='utf-8') as f:
        for ln,line in enumerate(f,1):
            line=line.strip()
            if not line: continue
            total+=1
            try:
                obj=json.loads(line)
            except Exception as e:
                print(f"[E] line {ln} invalid JSON: {e}"); errors+=1; continue
            ctx=obj.get('context','')
            resp=obj.get('response') or obj.get('answer') or ''
            ctx_m=extract(ctx); resp_m=extract(resp)
            missing=resp_m-ctx_m
            if missing:
                print(f"[E] line {ln} unknown markers in response: {sorted(missing)}")
                errors+=1
            if resp_m:
                mx=max(resp_m)
                gap=set(range(1,mx+1))-resp_m
                if gap:
                    print(f"[W] line {ln} gaps in marker sequence: {sorted(gap)}")
                    warnings+=1
    print(f"Done lines={total} errors={errors} warnings={warnings}")
    if errors: sys.exit(1)

if __name__=='__main__':
    main()"""Validate citation markers in a usage examples JSONL file.

Each line: JSON object with at least a 'context' (string) and optionally an 'answer' or 'response'.
Citation markers format: [D<number>] (e.g., [D1], [D2]).

Checks performed:
 1. Every marker appearing in 'response'/'answer' exists somewhere in 'context'.
 2. (Optional) Gaps: if markers jump (D1,D3) missing D2 -> warn.

Usage:
  python scripts/validate_citations.py --file rag_usage_examples.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys
from typing import Set

MARKER_RE = re.compile(r"\[D(\d+)\]")

def extract(markers_src: str) -> Set[int]:
    return {int(m) for m in MARKER_RE.findall(markers_src or '')}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    args = ap.parse_args()
    total=0; errors=0; warnings=0
    with open(args.file,'r',encoding='utf-8') as f:
        for line_no, line in enumerate(f, start=1):
            line=line.strip()
            if not line:
                continue
            total+=1
            try:
                obj=json.loads(line)
            except Exception as e:
                print(f"[E] line {line_no}: invalid JSON: {e}")
                errors+=1; continue
            context=obj.get('context','')
            resp=obj.get('response') or obj.get('answer') or ''
            ctx_markers=extract(context)
            resp_markers=extract(resp)
            missing=resp_markers-ctx_markers
            if missing:
                print(f"[E] line {line_no}: markers referenced not in context: {sorted(missing)}")
                errors+=1
            if resp_markers:
                mx=max(resp_markers)
                expected=set(range(1,mx+1))
                gap=expected-resp_markers
                if gap:
                    print(f"[W] line {line_no}: citation gaps (missing markers in sequence): {sorted(gap)}")
                    warnings+=1
    print(f"Done. lines={total} errors={errors} warnings={warnings}")
    if errors:
        sys.exit(1)

if __name__=='__main__':
    main()