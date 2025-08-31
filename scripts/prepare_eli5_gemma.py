#!/usr/bin/env python
"""Prepare ELI5 (or stub) data into instruction-tuning JSONL for Gemma.

Reads: data/eli5_sample.jsonl
Writes: data/eli5_gemma.jsonl with fields: instruction, input, output
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("data/eli5_sample.jsonl")
DST = Path("data/eli5_gemma.jsonl")

TEMPLATE_SYSTEM = "You are a patient tutor. Provide concise, kid-friendly explanations."


def convert():
    if not SRC.exists():
        raise SystemExit(
            f"Source file not found: {SRC}. Run scripts/fetch_eli5.py first."
        )
    out_lines = []
    with SRC.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            q = obj.get("question", "").strip()
            a = obj.get("answer", "").strip()
            if not q or not a:
                continue
            out = {
                "instruction": q,
                "input": "",  # no separate context
                "output": a,
                "system": TEMPLATE_SYSTEM,
            }
            out_lines.append(out)
    with DST.open("w", encoding="utf-8") as f:
        for o in out_lines:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out_lines)} records to {DST}")


if __name__ == "__main__":
    convert()
