#!/usr/bin/env python
"""Phi-3 Fine-tuning Script for Family Tutor Dataset

Fine-tunes Microsoft Phi-3 model using LoRA/QLoRA on curated family tutor data.

Prerequisites:
  1. Run scripts/family_tutor_curation.py to generate training data
  2. Ensure requirements installed (transformers, peft, bitsandbytes, accelerate)

Environment variables:
  PHI3_MODEL=microsoft/Phi-3-mini-4k-instruct (default)
  TRAIN_FILE=data/family_tutor/curated_family_tutor.jsonl
  OUTPUT_DIR=models/phi3-family-tutor-lora
  QLORA=1 (enable 4-bit quantization)
  MAX_SEQ_LENGTH=2048
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

try:
    import bitsandbytes as bnb
except Exception:
    bnb = None


@dataclass
class ChatExample:
    messages: list
    meta: dict


class FamilyTutorDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_len: int = 2048):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.examples = []

        print(f"Loading dataset from {path}...")
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    self.examples.append(
                        ChatExample(
                            messages=data["messages"], meta=data.get("meta", {})
                        )
                    )
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
                    continue

        print(f"Loaded {len(self.examples)} examples")

        # Print some statistics
        categories = {}
        sources = {}
        for ex in self.examples:
            cat = ex.meta.get("category", "unknown")
            src = ex.meta.get("source", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            sources[src] = sources.get(src, 0) + 1

        print("Dataset composition:")
        print(f"  By category: {categories}")
        print(f"  By source: {sources}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx: int):
        example = self.examples[idx]

        # Format as Phi-3 chat template
        # Phi-3 uses <|user|> and <|assistant|> tokens
        conversation_text = ""
        for msg in example.messages:
            if msg["role"] == "user":
                conversation_text += f"<|user|>\n{msg['content']}<|end|>\n"
            elif msg["role"] == "assistant":
                conversation_text += f"<|assistant|>\n{msg['content']}<|end|>\n"

        # Tokenize
        encoding = self.tokenizer(
            conversation_text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )

        # Set labels for language modeling (same as input_ids)
        encoding["labels"] = encoding["input_ids"].clone()

        return {k: v.squeeze(0) for k, v in encoding.items()}


def main():
    # Configuration
    model_name = os.getenv("PHI3_MODEL", "microsoft/Phi-3-mini-4k-instruct")
    train_path = Path(
        os.getenv("TRAIN_FILE", "data/family_tutor/curated_family_tutor.jsonl")
    )
    output_dir = Path(os.getenv("OUTPUT_DIR", "models/phi3-family-tutor-lora"))
    max_seq_length = int(os.getenv("MAX_SEQ_LENGTH", "2048"))
    qlora = os.getenv("QLORA", "1") == "1"
    load_8bit = os.getenv("LOAD_8BIT", "0") == "1"

    print("Configuration:")
    print(f"  Model: {model_name}")
    print(f"  Training data: {train_path}")
    print(f"  Output directory: {output_dir}")
    print(f"  Max sequence length: {max_seq_length}")
    print(f"  QLoRA (4-bit): {qlora}")
    print(f"  8-bit loading: {load_8bit}")

    if not train_path.exists():
        raise SystemExit(
            f"Training file {train_path} not found. Run family_tutor_curation.py first."
        )

    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, use_fast=True, trust_remote_code=True
    )

    # Phi-3 specific: ensure proper special tokens
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Add special chat tokens if not present
    special_tokens = {
        "additional_special_tokens": ["<|user|>", "<|assistant|>", "<|end|>"]
    }
    tokenizer.add_special_tokens(special_tokens)

    # Load model with quantization if specified
    print("Loading model...")
    load_kwargs = {"torch_dtype": torch.float16, "device_map": "auto"}

    if qlora:
        if bnb is None:
            raise SystemExit("bitsandbytes not installed but QLORA=1 set")
        load_kwargs.update(
            {
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": torch.float16,
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_quant_type": "nf4",
            }
        )
    elif load_8bit:
        if bnb is None:
            raise SystemExit("bitsandbytes not installed but LOAD_8BIT=1 set")
        load_kwargs.update({"load_in_8bit": True})

    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, **load_kwargs
    )

    # Resize embeddings if we added tokens
    model.resize_token_embeddings(len(tokenizer))

    # Prepare model for quantized training if needed
    if qlora or load_8bit:
        model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    print("Configuring LoRA...")
    lora_config = LoraConfig(
        r=16,  # Rank
        lora_alpha=32,  # LoRA scaling parameter
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",  # Phi-3 specific modules
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    dataset = FamilyTutorDataset(train_path, tokenizer, max_seq_length)

    # Calculate training steps
    batch_size = 1  # Small batch due to memory constraints
    gradient_accumulation_steps = 8
    effective_batch_size = batch_size * gradient_accumulation_steps
    steps_per_epoch = math.ceil(len(dataset) / effective_batch_size)

    print("\nTraining configuration:")
    print(f"  Dataset size: {len(dataset)}")
    print(f"  Batch size: {batch_size}")
    print(f"  Gradient accumulation: {gradient_accumulation_steps}")
    print(f"  Effective batch size: {effective_batch_size}")
    print(f"  Steps per epoch: {steps_per_epoch}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_train_epochs=2,  # Start with 2 epochs for family tutor
        learning_rate=2e-4,
        fp16=not qlora,  # Use fp16 unless using QLoRA
        bf16=False,
        logging_steps=max(1, steps_per_epoch // 10),
        save_steps=steps_per_epoch,
        save_total_limit=3,
        report_to=[],  # Disable wandb/tensorboard for now
        optim="adamw_torch",
        warmup_steps=max(1, steps_per_epoch // 10),
        max_grad_norm=1.0,
        dataloader_pin_memory=False,  # Reduce memory usage
        remove_unused_columns=False,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # We're doing causal LM, not masked LM
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )

    # Start training
    print("\n🚀 Starting training...")
    trainer.train()

    # Save the final model
    print(f"\n💾 Saving model to {output_dir}...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)

    print(f"\n✅ Training complete! Model saved to {output_dir}")
    print("To use the model, load it with:")
    print("  from peft import PeftModel")
    print(f"  model = PeftModel.from_pretrained(base_model, '{output_dir}')")


if __name__ == "__main__":
    main()
