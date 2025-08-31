#!/usr/bin/env python3
"""
Train domain-specific Phi-3 specialist for art.
"""

import json
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)


class Phi3DomainTrainer:
    def __init__(self):
        self.model_name = "microsoft/Phi-3-mini-4k-instruct"
        self.output_dir = "/home/cgbowen/AIWorkspace/models/phi3_art_tutor"
        self.domain = "art"
        self.max_length = 2048

    def load_domain_data(self) -> Dataset:
        """Load domain-specific training data."""
        domain_path = Path(
            "/home/cgbowen/AIWorkspace/fine_tuning/datasets/academic_domains/art"
        )
        examples = []

        # Load all JSONL files in domain folder
        for jsonl_file in domain_path.glob("*.jsonl"):
            try:
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            example = json.loads(line)
                            examples.append(example)
            except Exception as e:
                print(f"Warning: Could not read {jsonl_file}: {e}")

        print(f"📊 Loaded {len(examples)} examples for {self.domain}")

        # Format for instruction following
        formatted_examples = []
        for example in examples:
            if "instruction" in example and "output" in example:
                text = f"<|user|>\n{example['instruction']}\n<|end|>\n<|assistant|>\n{example['output']}\n<|end|>"
                formatted_examples.append({"text": text})

        return Dataset.from_list(formatted_examples)

    def train(self):
        """Train the domain specialist."""
        print(f"🚀 Training {self.domain} specialist...")

        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )

        # Load and tokenize data
        dataset = self.load_domain_data()

        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=self.max_length,
            )

        tokenized_dataset = dataset.map(tokenize_function, batched=True)

        # Training arguments optimized for education
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=2,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=200,
            weight_decay=0.01,
            logging_dir=f"{self.output_dir}/logs",
            logging_steps=100,
            save_steps=1000,
            evaluation_strategy="no",
            save_total_limit=3,
            load_best_model_at_end=False,
            fp16=True,
            dataloader_num_workers=2,
            remove_unused_columns=False,
            report_to="none",  # Disable wandb
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )

        # Train
        trainer.train()

        # Save
        trainer.save_model()
        tokenizer.save_pretrained(self.output_dir)

        print(f"✅ {self.domain} specialist saved to: {self.output_dir}")


if __name__ == "__main__":
    trainer = Phi3DomainTrainer()
    trainer.train()
