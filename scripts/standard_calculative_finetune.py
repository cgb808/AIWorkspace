#!/usr/bin/env python3
"""
STANDARD Calculative Multi-Phase Fine-tuning Pipeline
This is the official implementation for all subject specializations
"""

import argparse
import json
from datetime import datetime

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments)


class StandardCalculativeFineTuner:
    """Standard implementation of calculative epoch strategy"""

    def __init__(
        self, base_model="microsoft/Phi-3-mini-4k-instruct", subject="mathematics"
    ):
        self.base_model = base_model
        self.subject = subject
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize components
        self.tokenizer = None
        self.model = None

        # Enable optimizations for memory efficiency
        self.use_cache = False

        # STANDARD CALCULATIVE PARAMETERS
        self.PHASE_CONFIG = {
            "phase_1_foundation": {
                "name": "Subject Matter Expertise",
                "learning_rate": 2e-4,
                "epochs": 2,
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.1,
                "batch_size": 1,
                "gradient_accumulation": 4,
            },
            "phase_2_methodology": {
                "name": "Tutoring & Pedagogical Skills",
                "learning_rate": 1e-4,
                "epochs": 1,
                "lora_r": 8,
                "lora_alpha": 16,
                "lora_dropout": 0.05,
                "batch_size": 2,
                "gradient_accumulation": 2,
            },
            "phase_3_communication": {
                "name": "Family-Oriented Communication",
                "learning_rate": 5e-5,
                "epochs": 1,
                "lora_r": 4,
                "lora_alpha": 8,
                "lora_dropout": 0.02,
                "batch_size": 2,
                "gradient_accumulation": 2,
            },
            "phase_4_personality": {
                "name": "Persona Integration",
                "learning_rate": 2e-5,
                "epochs": 1,
                "lora_r": 4,
                "lora_alpha": 8,
                "lora_dropout": 0.01,
                "batch_size": 4,
                "gradient_accumulation": 1,
            },
            "phase_5_adaptation": {
                "name": "Contextual Awareness",
                "learning_rate": 1e-5,
                "epochs": 1,
                "lora_r": 2,
                "lora_alpha": 4,
                "lora_dropout": 0.01,
                "batch_size": 4,
                "gradient_accumulation": 1,
            },
        }

    def prepare_model(self):
        """Load and prepare model for fine-tuning"""
        print(f"🔧 Preparing {self.base_model} for calculative fine-tuning...")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model, trust_remote_code=True, use_fast=True
        )

        # Ensure pad token is set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with optimizations
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                use_cache=self.use_cache,
                load_in_4bit=True,  # Enable 4-bit quantization for memory efficiency
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            print("✅ Model loaded successfully with 4-bit quantization")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("🔄 Trying without quantization...")
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.base_model,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    use_cache=self.use_cache,
                )
                print("✅ Model loaded successfully without quantization")
            except Exception as e2:
                print(f"❌ Failed to load model even without quantization: {e2}")
                raise e2

    def execute_phase(
        self, phase_key, train_dataset, output_dir, previous_checkpoint=None
    ):
        """Execute a single phase of calculative training"""
        config = self.PHASE_CONFIG[phase_key]
        phase_name = config["name"]

        print(f"\n🚀 EXECUTING {phase_key.upper()}: {phase_name}")
        print(f"   📈 Learning Rate: {config['learning_rate']}")
        print(f"   🔄 Epochs: {config['epochs']}")
        print(f"   💾 Batch Size: {config['batch_size']}")

        # Configure LoRA for this phase
        if previous_checkpoint and phase_key != "phase_1_foundation":
            # Load previous phase checkpoint
            print(f"   📂 Loading checkpoint: {previous_checkpoint}")
            # Implementation for loading previous checkpoint

        lora_config = LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=config["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM",
        )

        if previous_checkpoint is None:  # First phase
            model = get_peft_model(self.model, lora_config)
        else:
            model = self.model  # Already has LoRA from previous phase

        # Training arguments
        phase_output_dir = f"{output_dir}/{phase_key}"
        training_args = TrainingArguments(
            output_dir=phase_output_dir,
            num_train_epochs=config["epochs"],
            per_device_train_batch_size=config["batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation"],
            learning_rate=config["learning_rate"],
            fp16=True,
            logging_steps=10,
            save_steps=500,
            evaluation_strategy="no",
            save_strategy="epoch",
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            gradient_checkpointing=True,
        )

        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=self.tokenizer,
        )

        # Execute training
        print("   🏃 Starting training...")
        trainer.train()

        # Save phase checkpoint
        trainer.save_model(phase_output_dir)
        print(f"   ✅ Phase completed. Saved to: {phase_output_dir}")

        return phase_output_dir

    def execute_full_pipeline(self, train_file, output_base_dir):
        """Execute the complete 5-phase calculative training pipeline"""
        print("🎯 STANDARD CALCULATIVE FINE-TUNING PIPELINE")
        print("=" * 60)
        print(f"Subject: {self.subject}")
        print(f"Base Model: {self.base_model}")
        print(f"Training Data: {train_file}")
        print(f"Output Directory: {output_base_dir}")

        # Prepare model
        self.prepare_model()

        # Load training data
        with open(train_file, "r") as f:
            data = [json.loads(line) for line in f]

        def tokenize_function(examples):
            # Convert to chat format
            texts = []
            for example in examples:
                if "messages" in example:
                    text = self.tokenizer.apply_chat_template(
                        example["messages"], tokenize=False, add_generation_prompt=False
                    )
                    texts.append(text)

            return self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt",
            )

        dataset = Dataset.from_list(data)
        tokenized_dataset = dataset.map(tokenize_function, batched=True)

        # Execute phases sequentially
        previous_checkpoint = None

        for phase_key in self.PHASE_CONFIG.keys():
            checkpoint = self.execute_phase(
                phase_key, tokenized_dataset, output_base_dir, previous_checkpoint
            )
            previous_checkpoint = checkpoint

        print("\n✅ CALCULATIVE FINE-TUNING PIPELINE COMPLETED!")
        print(f"Final model saved to: {previous_checkpoint}")

        return previous_checkpoint


def main():
    parser = argparse.ArgumentParser(description="Standard Calculative Fine-tuning")
    parser.add_argument("--train-file", required=True, help="Training dataset file")
    parser.add_argument(
        "--subject", required=True, choices=["mathematics", "english", "science"]
    )
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument(
        "--base-model", default="microsoft/Phi-3-mini-4k-instruct", help="Base model"
    )

    args = parser.parse_args()

    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = f"{args.output_dir}/phi3_{args.subject}_{timestamp}"

    # Initialize and run pipeline
    tuner = StandardCalculativeFineTuner(args.base_model, args.subject)
    final_model_path = tuner.execute_full_pipeline(args.train_file, full_output_dir)

    print("\n🎯 STANDARD PIPELINE COMPLETED")
    print(f"Subject: {args.subject}")
    print(f"Final Model: {final_model_path}")


if __name__ == "__main__":
    main()
