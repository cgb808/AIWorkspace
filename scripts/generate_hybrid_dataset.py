#!/usr/bin/env python3
"""Generate a synthetic hybrid methodology + math dataset JSONL.

Each record: {"instruction": str, "response": str, "category": "pure"|"math"}
"""
from __future__ import annotations
import argparse, json, random, os
from pathlib import Path


PURE_TEMPLATES = [
    ("Explain the learning objective of topic {i}.", "The core learning objective of topic {i} is to build conceptual understanding."),
    ("Describe a reflective prompt for lesson {i}.", "A reflective prompt encourages metacognition about lesson {i}."),
]
MATH_TEMPLATES = [
    ("Solve: {i} + {j} = ?", "{ans}"),
    ("What is {i} * {j}?", "{ans}"),
]


def synth_examples(n_pure: int, n_math: int):
    rnd = random.Random(42)
    for k in range(n_pure):
        t = rnd.choice(PURE_TEMPLATES)
        i = rnd.randint(1, 100)
        yield {
            'instruction': t[0].format(i=i),
            'response': t[1].format(i=i),
            'category': 'pure'
        }
    for k in range(n_math):
        t = rnd.choice(MATH_TEMPLATES)
        i = rnd.randint(2, 12)
        j = rnd.randint(2, 12)
        ans = eval(f"{i}{'+' if '+' in t[0] else '*'}{j}") if '+' in t[0] else i * j
        yield {
            'instruction': t[0].format(i=i, j=j),
            'response': t[1].format(i=i, j=j, ans=ans),
            'category': 'math'
        }


def main():  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument('--pure', type=int, default=100)
    ap.add_argument('--math', type=int, default=100)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open('w', encoding='utf-8') as f:
        for rec in synth_examples(args.pure, args.math):
            f.write(json.dumps(rec) + '\n')
            count += 1
    print(f"[hybrid] wrote {count} records -> {out_path}")


if __name__ == '__main__':
    main()
