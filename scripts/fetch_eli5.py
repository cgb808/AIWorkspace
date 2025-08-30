#!/usr/bin/env python
"""Fetch and cache a small sampled subset of the ELI5 dataset.

Outputs:
  data/eli5_sample.jsonl  (one JSON object per line with fields: question, answer)

You can adjust SAMPLE_SIZE via env ELI5_SAMPLE (default 50).
"""
from __future__ import annotations
import os, json, random
from pathlib import Path

SAMPLE_SIZE = int(os.getenv("ELI5_SAMPLE", "50"))
OUT_DIR = Path("data")
OUT_FILE = OUT_DIR / "eli5_sample.jsonl"

try:  # Lazy import guard
    from datasets import load_dataset  # type: ignore
except Exception:  # noqa: BLE001
    load_dataset = None  # type: ignore
def main():
    print("Attempting to load ELI5 dataset...")
    dataset = None
    load_error = None
    if load_dataset is not None:
        for ds_name in ("eli5", "HuggingFaceH4/eli5"):
            try:
                dataset = load_dataset(ds_name)
                print(f"Loaded dataset id: {ds_name}")
                break
            except Exception as e:  # noqa: BLE001
                load_error = e
    else:
        load_error = RuntimeError("datasets library not available")

    samples: list[dict]
    if dataset is None:
        print(f"Falling back to stub examples (reason: {load_error})")
        samples = [
            {"question": "Why is the sky blue?", "answer": "Air molecules scatter blue light more than other colors."},
            {"question": "What is photosynthesis?", "answer": "Plants use sunlight to turn water and air into food (sugars)."},
            {"question": "Why do we yawn?", "answer": "Likely to help regulate brain temperature and oxygen / CO2 balance."},
        ]
    else:
        # Prefer train split
        if isinstance(dataset, dict) and "train" in dataset:  # type: ignore[arg-type]
            ds = dataset["train"]  # type: ignore[index]
        else:
            ds = dataset  # type: ignore[assignment]
        lim = min(SAMPLE_SIZE, len(ds))  # type: ignore[arg-type]
        if lim <= 0:
            samples = []
        else:
            # Random indices
            indices = random.sample(range(len(ds)), lim)  # type: ignore[arg-type]
            samples = []
            for i in indices:
                row = ds[i]  # type: ignore[index]
                # Row is a dict-like structure
                question = (
                    row.get("title")  # type: ignore[attr-defined]
                    or row.get("question")  # type: ignore[attr-defined]
                    or ""
                )
                # Answers may be dict with key 'text'
                answers = row.get("answers") or {}  # type: ignore[attr-defined]
                answer_texts = None
                if isinstance(answers, dict):
                    answer_texts = answers.get("text")
                answer = ""
                if isinstance(answer_texts, (list, tuple)) and answer_texts:
                    answer = answer_texts[0]
                samples.append(
                    {
                        "question": str(question).strip(),
                        "answer": str(answer).strip(),
                    }
                )
        print(f"Collected {len(samples)} samples from dataset")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for obj in samples:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"Wrote {len(samples)} records to {OUT_FILE}")

if __name__ == "__main__":
    main()
