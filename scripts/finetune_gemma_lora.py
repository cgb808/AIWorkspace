#!/usr/bin/env python
"""LoRA (QLoRA optional) fine-tuning script for Gemma 2B on prepared ELI5 data.

Prereqs:
  1. Run scripts/fetch_eli5.py
  2. Run scripts/prepare_eli5_gemma.py
  3. Ensure requirements installed (transformers, peft, bitsandbytes, accelerate)

Environment (optional overrides):
  GEMMA_MODEL=google/gemma-2b-it (default)
  ELI5_TRAIN_FILE=data/eli5_gemma.jsonl
  OUTPUT_DIR=models/gemma-eli5-lora
  QLORA=1 (enable 4-bit quantization path)

Produces a PEFT adapter directory you can merge at inference or load with PEFT.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

try:
    import bitsandbytes as bnb  # noqa: F401
except Exception:  # noqa: BLE001
    bnb = None  # type: ignore


@dataclass
class Rec:
    instruction: str
    input: str
    output: str
    system: str | None = None


class InstDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_len: int = 1024):
        self.rows: list[Rec] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            self.rows.append(
                Rec(
                    instruction=obj.get("instruction", ""),
                    input=obj.get("input", ""),
                    output=obj.get("output", ""),
                    system=obj.get("system"),
                )
            )
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx: int):
        r = self.rows[idx]
        parts = []
        if r.system:
            parts.append(f"<|system|>\n{r.system}\n")
        parts.append(f"<|user|>\n{r.instruction}\n")
        if r.input:
            parts.append(f"Context:\n{r.input}\n")
        parts.append(f"<|assistant|>\n{r.output}\n")
        text = "".join(parts)
        toks = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )
        toks["labels"] = toks["input_ids"].clone()
        return {k: v.squeeze(0) for k, v in toks.items()}


def main():
    model_name = os.getenv("GEMMA_MODEL", "google/gemma-2b-it")
    train_path = Path(os.getenv("ELI5_TRAIN_FILE", "data/eli5_gemma.jsonl"))
    out_dir = Path(os.getenv("OUTPUT_DIR", "models/gemma-eli5-lora"))
    qlora = os.getenv("QLORA", "0") == "1"
    load_8bit = os.getenv("LOAD_8BIT", "0") == "1"
    if not train_path.exists():
        raise SystemExit(
            f"Training file {train_path} not found. Run prepare script first."
        )

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Model load (4-bit if QLoRA, else optional 8-bit)
    load_kwargs = {}
    if qlora:
        if bnb is None:
            raise SystemExit("bitsandbytes not installed but QLORA=1 set")
        load_kwargs.update(
            dict(
                load_in_4bit=True,
                device_map="auto",
            )
        )
    elif load_8bit:
        if bnb is None:
            raise SystemExit("bitsandbytes not installed but LOAD_8BIT=1 set")
        load_kwargs.update(
            dict(
                load_in_8bit=True,
                device_map="auto",
            )
        )
    model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)

    if qlora or load_8bit:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    ds = InstDataset(train_path, tokenizer)

    steps_per_epoch = math.ceil(len(ds) / 4)  # batch 1 * grad_acc 4 below

    args = TrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=1,
        learning_rate=2e-4,
        fp16=not qlora,
        bf16=False,
        logging_steps=max(1, steps_per_epoch // 10),
        save_steps=steps_per_epoch,
        save_total_limit=2,
        report_to=[],
        optim="adamw_torch",
        warmup_steps=max(1, steps_per_epoch // 10),
    )

    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=collator,
    )
    trainer.train()
    trainer.save_model()
    print(f"Adapter saved to {out_dir}")


if __name__ == "__main__":
    main()
