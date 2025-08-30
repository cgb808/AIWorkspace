#!/usr/bin/env python3
"""
Enhanced Phi-3 Fine-tuning with Quality-Validated Dataset
Supports both tagged and raw output modes for experimentation
"""

import json
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import Dataset
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPhi3Dataset(Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = 2048, use_tagged_output: bool = True):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.use_tagged_output = use_tagged_output
        
        # Load data
        self.examples = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    example = json.loads(line.strip())
                    self.examples.append(example)
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Loaded {len(self.examples)} examples from {data_path}")
        
        # Analyze role distribution
        role_counts = {}
        for example in self.examples:
            role = example.get("meta", {}).get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        logger.info("Role distribution:")
        for role, count in sorted(role_counts.items()):
            percentage = count / len(self.examples) * 100
            logger.info(f"  {role}: {count} ({percentage:.1f}%)")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Format for Phi-3 chat template
        instruction = example["instruction"]
        output = example["output"]
        
        # Choose between tagged output (with separators) or raw output
        if self.use_tagged_output:
            # Use the full instruction with separators
            formatted_instruction = instruction
        else:
            # Extract just the core instruction without separators
            # This is a simplified extraction - could be made more sophisticated
            role = example.get("meta", {}).get("role", "general_assistant")
            
            # Try to extract the main instruction part
            if "[TASK]" in instruction:
                # For general assistant
                parts = instruction.split("[TASK]")
                if len(parts) > 1:
                    formatted_instruction = parts[1].split("[RESPONSE]")[0].strip()
                else:
                    formatted_instruction = instruction
            elif "[LEARNING_OBJECTIVE]" in instruction:
                # For family tutor
                parts = instruction.split("[LEARNING_OBJECTIVE]")
                if len(parts) > 1:
                    formatted_instruction = parts[1].split("[RESPONSE]")[0].strip()
                else:
                    formatted_instruction = instruction
            elif "[REFLECTION_PROMPT]" in instruction:
                # For philosophical guide
                parts = instruction.split("[REFLECTION_PROMPT]")
                if len(parts) > 1:
                    formatted_instruction = parts[1].split("[GUIDANCE]")[0].strip()
                else:
                    formatted_instruction = instruction
            elif "[EXPLANATION_GOAL]" in instruction:
                # For educational expert
                parts = instruction.split("[EXPLANATION_GOAL]")
                if len(parts) > 1:
                    formatted_instruction = parts[1].split("[TEACHING_RESPONSE]")[0].strip()
                else:
                    formatted_instruction = instruction
            else:
                formatted_instruction = instruction
            
            # Clean up any remaining prefixes
            for prefix in ["As a helpful assistant, ", "As a family tutor, ", 
                          "As a philosophical guide, ", "As an educational expert, "]:
                if formatted_instruction.startswith(prefix):
                    formatted_instruction = formatted_instruction[len(prefix):]
                    break
        
        # Create chat format
        chat_text = f"<|user|>\n{formatted_instruction}<|end|>\n<|assistant|>\n{output}<|end|>"
        
        # Tokenize
        encoding = self.tokenizer(
            chat_text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors="pt"
        )
        
        input_ids = encoding["input_ids"].squeeze()
        attention_mask = encoding["attention_mask"].squeeze()
        
        # For causal LM, labels are the same as input_ids
        labels = input_ids.clone()
        
        # Mask the instruction part in labels (only learn from assistant response)
        user_end_token = self.tokenizer.encode("<|end|>")[0]
        assistant_start = None
        
        # Find where assistant response starts
        input_ids_list = input_ids.tolist()
        for i in range(len(input_ids_list) - 1):
            if input_ids_list[i] == user_end_token:
                # Look for assistant token after this
                assistant_start = i + 1
                break
        
        if assistant_start is not None:
            labels[:assistant_start] = -100  # Ignore instruction tokens in loss
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }

def setup_model_and_tokenizer(model_name: str, use_4bit: bool = True):
    """Setup model and tokenizer with optional 4-bit quantization"""
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Add special tokens if not present
    special_tokens = ["<|user|>", "<|assistant|>", "<|end|>"]
    new_tokens = []
    for token in special_tokens:
        if token not in tokenizer.get_vocab():
            new_tokens.append(token)
    
    if new_tokens:
        tokenizer.add_special_tokens({"additional_special_tokens": new_tokens})
    
    # Set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch.float16,
        "device_map": "auto"
    }
    
    if use_4bit:
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
    
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    
    # Resize embeddings if we added new tokens
    if new_tokens:
        model.resize_token_embeddings(len(tokenizer))
    
    return model, tokenizer

def setup_lora_config():
    """Setup LoRA configuration for Phi-3"""
    return LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

def main():
    parser = argparse.ArgumentParser(description="Enhanced Phi-3 Fine-tuning")
    parser.add_argument("--train-file", required=True, help="Training data file (JSONL)")
    parser.add_argument("--val-file", help="Validation data file (JSONL)")
    parser.add_argument("--model-name", default="microsoft/Phi-3-mini-4k-instruct", 
                       help="Base model name")
    parser.add_argument("--output-dir", default="models/phi3-enhanced-tutor", 
                       help="Output directory")
    parser.add_argument("--max-length", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--batch-size", type=int, default=4, help="Training batch size")
    parser.add_argument("--num-epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--use-4bit", action="store_true", default=True, 
                       help="Use 4-bit quantization")
    parser.add_argument("--use-tagged-output", action="store_true", default=True,
                       help="Use tagged output format (with separators)")
    parser.add_argument("--gradient-checkpointing", action="store_true", default=True,
                       help="Enable gradient checkpointing")
    parser.add_argument("--save-steps", type=int, default=250, help="Save checkpoint every N steps")
    parser.add_argument("--eval-steps", type=int, default=250, help="Evaluate every N steps")
    parser.add_argument("--warmup-steps", type=int, default=100, help="Warmup steps")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save training configuration
    config_path = output_dir / "training_config.json"
    with open(config_path, 'w') as f:
        json.dump(vars(args), f, indent=2)
    
    logger.info(f"Starting enhanced Phi-3 fine-tuning")
    logger.info(f"Training file: {args.train_file}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Using tagged output: {args.use_tagged_output}")
    
    # Setup model and tokenizer
    logger.info("Loading model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer(args.model_name, args.use_4bit)
    
    # Prepare model for training
    if args.use_4bit:
        model = prepare_model_for_kbit_training(model)
    
    # Setup LoRA
    logger.info("Setting up LoRA...")
    lora_config = setup_lora_config()
    model = get_peft_model(model, lora_config)
    
    # Print trainable parameters
    model.print_trainable_parameters()
    
    # Enable gradient checkpointing
    if args.gradient_checkpointing:
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable()
    
    # Load datasets
    logger.info("Loading datasets...")
    train_dataset = EnhancedPhi3Dataset(
        args.train_file, tokenizer, args.max_length, args.use_tagged_output
    )
    
    eval_dataset = None
    if args.val_file and Path(args.val_file).exists():
        eval_dataset = EnhancedPhi3Dataset(
            args.val_file, tokenizer, args.max_length, args.use_tagged_output
        )
        logger.info(f"Loaded validation dataset with {len(eval_dataset)} examples")
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=2,
        num_train_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        fp16=True,
        logging_steps=50,
        save_steps=args.save_steps,
        eval_steps=args.eval_steps if eval_dataset else args.save_steps,
        evaluation_strategy="steps" if eval_dataset else "no",
        save_strategy="steps",
        warmup_steps=args.warmup_steps,
        lr_scheduler_type="cosine",
        load_best_model_at_end=True if eval_dataset else False,
        metric_for_best_model="eval_loss" if eval_dataset else None,
        greater_is_better=False,
        report_to=["tensorboard"],
        run_name=f"phi3-enhanced-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        dataloader_pin_memory=False,  # Helps with memory issues
        remove_unused_columns=False,
        push_to_hub=False
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer
    )
    
    # Start training
    logger.info("Starting training...")
    trainer.train()
    
    # Save final model
    logger.info("Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)
    
    # Save training summary
    summary = {
        "training_completed": datetime.now().isoformat(),
        "final_train_loss": trainer.state.log_history[-1].get("train_loss", "N/A"),
        "total_steps": trainer.state.global_step,
        "epochs_completed": trainer.state.epoch,
        "model_name": args.model_name,
        "dataset_info": {
            "train_examples": len(train_dataset),
            "val_examples": len(eval_dataset) if eval_dataset else 0,
            "use_tagged_output": args.use_tagged_output
        }
    }
    
    summary_path = output_dir / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Training completed! Model saved to {args.output_dir}")
    logger.info(f"Training summary saved to {summary_path}")

if __name__ == "__main__":
    main()
