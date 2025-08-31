#!/usr/bin/env python
"""Interactive inference for Gemma 2B (base or LoRA/QLoRA adapter).

Env vars / arguments:
  GEMMA_MODEL=google/gemma-2b-it (default)  # any HF Gemma checkpoint
  LORA_ADAPTER=models/gemma-eli5-lora       # path to PEFT adapter (optional)
  LOAD_8BIT=1 | QLORA=1                    # match fine-tune settings (one or none)
  MAX_NEW_TOKENS=256

Usage:
  python scripts/run_gemma_infer.py            # base
  LORA_ADAPTER=models/gemma-eli5-lora python scripts/run_gemma_infer.py

Type 'exit' or Ctrl+D to quit.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import torch

try:
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception as e:  # noqa: BLE001
    raise SystemExit(
        "Install transformers and peft first (see requirements.txt)"
    ) from e

MODEL_NAME = os.getenv("GEMMA_MODEL", "google/gemma-2b-it")
ADAPTER_PATH: Optional[str] = os.getenv("LORA_ADAPTER") or None
QLORA = os.getenv("QLORA", "0") == "1"
LOAD_8BIT = os.getenv("LOAD_8BIT", "0") == "1"
MAX_NEW = int(os.getenv("MAX_NEW_TOKENS", "256"))

from typing import Any

load_kwargs: dict[str, Any] = {"device_map": "auto"}
if QLORA:
    load_kwargs["load_in_4bit"] = True
elif LOAD_8BIT:
    load_kwargs["load_in_8bit"] = True

print(
    f"Loading model: {MODEL_NAME} (adapter={ADAPTER_PATH or 'none'}, qlora={QLORA}, 8bit={LOAD_8BIT})"
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, **load_kwargs)
if ADAPTER_PATH:
    print(f"Attaching LoRA adapter: {ADAPTER_PATH}")
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)

model.eval()
print("Ready. Enter your prompt.")


def generate(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    # Attempt to return only the continuation
    return text[len(prompt) :].strip() if text.startswith(prompt) else text


try:
    for line in sys.stdin:
        prompt = line.strip()
        if not prompt or prompt.lower() in {"exit", "quit"}:
            break
        resp = generate(prompt)
        print("---")
        print(resp)
        print("===")
except (EOFError, KeyboardInterrupt):
    pass
print("Bye.")
