#!/usr/bin/env python3
"""
Train the tiny tool controller model for fast tool classification.
"""

import json

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)


class TinyToolControllerTrainer:
    def __init__(self):
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.output_dir = "/home/cgbowen/AIWorkspace/models/tiny_tool_controller"
        self.max_length = 512

    def load_training_data(self, file_path: str) -> Dataset:
        """Load and prepare training data."""
        examples = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))

        # Format for tool classification
        formatted_examples = []
        for example in examples:
            if "tool_category" in example:
                text = f"Classify tool needed: {example.get('instruction', '')}\nUser input: {example.get('input', '')}\nTool category: {example['tool_category']}"
                formatted_examples.append({"text": text})

        return Dataset.from_list(formatted_examples)

    def train(self, training_file: str):
        """Train the tiny tool controller."""
        print("🚀 Training tiny tool controller...")

        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype=torch.float16, device_map="auto"
        )

        # Load and tokenize data
        dataset = self.load_training_data(training_file)

        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=self.max_length,
            )

        tokenized_dataset = dataset.map(tokenize_function, batched=True)

        # Training arguments for speed optimization
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=8,
            gradient_accumulation_steps=2,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=f"{self.output_dir}/logs",
            logging_steps=50,
            save_steps=500,
            evaluation_strategy="no",
            save_total_limit=2,
            load_best_model_at_end=False,
            metric_for_best_model="loss",
            greater_is_better=False,
            fp16=True,  # Speed optimization
            dataloader_num_workers=4,
            remove_unused_columns=False,
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

        print(f"✅ Tiny tool controller saved to: {self.output_dir}")


if __name__ == "__main__":
    trainer = TinyToolControllerTrainer()
    trainer.train(
        "/home/cgbowen/AIWorkspace/fine_tuning/datasets/tool_control/consolidated_tool_control.jsonl"
    )
