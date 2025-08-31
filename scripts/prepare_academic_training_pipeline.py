#!/usr/bin/env python3
"""
Academic Domain Training Pipeline
Trains the tiny tool controller and domain-specific Phi-3 specialists.
"""

import json
from pathlib import Path
from typing import Dict


class AcademicTrainingPipeline:
    def __init__(self, base_path: str = "/home/cgbowen/AIWorkspace"):
        self.base_path = Path(base_path)
        self.academic_path = (
            self.base_path / "fine_tuning" / "datasets" / "academic_domains"
        )
        self.models_path = self.base_path / "models"
        self.vendor_path = self.base_path / "vendor"

        # Model configurations
        self.tiny_model_config = {
            "base_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "output_name": "tiny_tool_controller",
            "max_tokens": 512,
            "specialization": "tool_classification",
            "target_latency": "< 100ms",
        }

        self.phi3_configs = {
            "mathematics": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_mathematics_tutor",
                "specialization": "mathematics_education",
            },
            "science": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_science_tutor",
                "specialization": "science_education",
            },
            "english": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_english_tutor",
                "specialization": "english_education",
            },
            "history": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_history_tutor",
                "specialization": "history_education",
            },
            "art": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_art_tutor",
                "specialization": "art_education",
            },
            "foreign_language": {
                "base_model": "microsoft/Phi-3-mini-4k-instruct",
                "output_name": "phi3_language_tutor",
                "specialization": "language_education",
            },
        }

    def prepare_tool_control_training(self):
        """Prepare consolidated tool control training data."""
        print("🔧 Preparing tool control training data...")

        tool_control_path = self.base_path / "fine_tuning" / "datasets" / "tool_control"
        consolidated_file = tool_control_path / "consolidated_tool_control.jsonl"

        # Read existing tool control data
        tool_examples = []
        for jsonl_file in tool_control_path.glob("*.jsonl"):
            if jsonl_file.name != "consolidated_tool_control.jsonl":
                try:
                    with open(jsonl_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                tool_examples.append(json.loads(line))
                except Exception as e:
                    print(f"Warning: Could not read {jsonl_file}: {e}")

        print(f"📊 Found {len(tool_examples)} tool control examples")

        # Add domain awareness to tool control examples
        domain_aware_examples = []
        for example in tool_examples:
            # Add domain context to tool control
            if "mathematics" in str(example).lower() or "math" in str(example).lower():
                example["domain_hint"] = "mathematics"
            elif "science" in str(example).lower():
                example["domain_hint"] = "science"
            elif "english" in str(example).lower() or "writing" in str(example).lower():
                example["domain_hint"] = "english"
            else:
                example["domain_hint"] = "general"

            domain_aware_examples.append(example)

        # Write consolidated data
        with open(consolidated_file, "w", encoding="utf-8") as f:
            for example in domain_aware_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        print(f"✅ Consolidated tool control data: {consolidated_file}")
        return consolidated_file

    def create_tiny_model_training_script(self, training_file: Path):
        """Create training script for tiny tool controller."""
        script_content = f'''#!/usr/bin/env python3
"""
Train the tiny tool controller model for fast tool classification.
"""

import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import json
from typing import List, Dict

class TinyToolControllerTrainer:
    def __init__(self):
        self.model_name = "{self.tiny_model_config['base_model']}"
        self.output_dir = "{self.models_path / self.tiny_model_config['output_name']}"
        self.max_length = 512
        
    def load_training_data(self, file_path: str) -> Dataset:
        """Load and prepare training data."""
        examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
        
        # Format for tool classification
        formatted_examples = []
        for example in examples:
            if "tool_category" in example:
                text = f"Classify tool needed: {{example.get('instruction', '')}}\\nUser input: {{example.get('input', '')}}\\nTool category: {{example['tool_category']}}"
                formatted_examples.append({{"text": text}})
        
        return Dataset.from_list(formatted_examples)
    
    def train(self, training_file: str):
        """Train the tiny tool controller."""
        print("🚀 Training tiny tool controller...")
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Load and tokenize data
        dataset = self.load_training_data(training_file)
        
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=self.max_length
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
            logging_dir=f"{{self.output_dir}}/logs",
            logging_steps=50,
            save_steps=500,
            evaluation_strategy="no",
            save_total_limit=2,
            load_best_model_at_end=False,
            metric_for_best_model="loss",
            greater_is_better=False,
            fp16=True,  # Speed optimization
            dataloader_num_workers=4,
            remove_unused_columns=False
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
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
        
        print(f"✅ Tiny tool controller saved to: {{self.output_dir}}")

if __name__ == "__main__":
    trainer = TinyToolControllerTrainer()
    trainer.train("{training_file}")
'''

        script_file = self.base_path / "scripts" / "train_tiny_tool_controller.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        return script_file

    def create_phi3_training_script(self, domain: str, config: Dict):
        """Create domain-specific Phi-3 training script."""
        script_content = f'''#!/usr/bin/env python3
"""
Train domain-specific Phi-3 specialist for {domain}.
"""

import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import json
from pathlib import Path

class Phi3DomainTrainer:
    def __init__(self):
        self.model_name = "{config['base_model']}"
        self.output_dir = "{self.models_path / config['output_name']}"
        self.domain = "{domain}"
        self.max_length = 2048
        
    def load_domain_data(self) -> Dataset:
        """Load domain-specific training data."""
        domain_path = Path("{self.academic_path / domain}")
        examples = []
        
        # Load all JSONL files in domain folder
        for jsonl_file in domain_path.glob("*.jsonl"):
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            example = json.loads(line)
                            examples.append(example)
            except Exception as e:
                print(f"Warning: Could not read {{jsonl_file}}: {{e}}")
        
        print(f"📊 Loaded {{len(examples)}} examples for {{self.domain}}")
        
        # Format for instruction following
        formatted_examples = []
        for example in examples:
            if "instruction" in example and "output" in example:
                text = f"<|user|>\\n{{example['instruction']}}\\n<|end|>\\n<|assistant|>\\n{{example['output']}}\\n<|end|>"
                formatted_examples.append({{"text": text}})
        
        return Dataset.from_list(formatted_examples)
    
    def train(self):
        """Train the domain specialist."""
        print(f"🚀 Training {{self.domain}} specialist...")
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load and tokenize data
        dataset = self.load_domain_data()
        
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=self.max_length
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
            logging_dir=f"{{self.output_dir}}/logs",
            logging_steps=100,
            save_steps=1000,
            evaluation_strategy="no",
            save_total_limit=3,
            load_best_model_at_end=False,
            fp16=True,
            dataloader_num_workers=2,
            remove_unused_columns=False,
            report_to="none"  # Disable wandb
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
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
        
        print(f"✅ {{self.domain}} specialist saved to: {{self.output_dir}}")

if __name__ == "__main__":
    trainer = Phi3DomainTrainer()
    trainer.train()
'''

        script_file = self.base_path / "scripts" / f"train_phi3_{domain}_specialist.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        return script_file

    def create_training_orchestrator(self):
        """Create orchestrator script to manage all training."""
        orchestrator_content = '''#!/usr/bin/env python3
"""
Training Orchestrator - Manages the complete academic training pipeline.
"""

import subprocess
import time
import sys
from pathlib import Path

class TrainingOrchestrator:
    def __init__(self):
        self.base_path = Path("/home/cgbowen/AIWorkspace")
        self.scripts_path = self.base_path / "scripts"
        
    def run_training_step(self, script_name: str, description: str):
        """Run a training step with monitoring."""
        print(f"\\n🚀 Starting: {description}")
        print("=" * 60)
        
        script_path = self.scripts_path / script_name
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ Completed: {description}")
                print(f"⏱️  Duration: {duration:.1f} seconds")
                if result.stdout:
                    print("Output:", result.stdout[-500:])  # Last 500 chars
            else:
                print(f"❌ Failed: {description}")
                print("Error:", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: {description} exceeded 1 hour")
            return False
        except Exception as e:
            print(f"💥 Exception in {description}: {e}")
            return False
            
        return True
    
    def run_full_pipeline(self):
        """Run the complete training pipeline."""
        print("🎓 Academic Domain Training Pipeline")
        print("=" * 60)
        
        pipeline_steps = [
            ("train_tiny_tool_controller.py", "Tiny Tool Controller Training"),
            ("train_phi3_mathematics_specialist.py", "Mathematics Specialist Training"),
            ("train_phi3_science_specialist.py", "Science Specialist Training"),
            ("train_phi3_english_specialist.py", "English Specialist Training"),
            ("train_phi3_history_specialist.py", "History Specialist Training"),
            ("train_phi3_art_specialist.py", "Art Specialist Training"),
            ("train_phi3_foreign_language_specialist.py", "Foreign Language Specialist Training"),
        ]
        
        successful_steps = 0
        total_start = time.time()
        
        for script_name, description in pipeline_steps:
            if self.run_training_step(script_name, description):
                successful_steps += 1
            else:
                print(f"\\n⚠️  Training pipeline stopped at: {description}")
                break
        
        total_duration = time.time() - total_start
        
        print(f"\\n🎉 Training Pipeline Complete!")
        print(f"✅ Successful steps: {successful_steps}/{len(pipeline_steps)}")
        print(f"⏱️  Total duration: {total_duration/3600:.1f} hours")
        
        if successful_steps == len(pipeline_steps):
            print("🚀 All academic specialists trained successfully!")
            self.create_deployment_config()
        else:
            print("⚠️  Some training steps failed. Check logs above.")
    
    def create_deployment_config(self):
        """Create deployment configuration for trained models."""
        config = {
            "tiny_tool_controller": {
                "model_path": "models/tiny_tool_controller",
                "purpose": "Fast tool classification (<100ms)",
                "input_format": "raw_text",
                "output_format": "tool_category"
            },
            "phi3_specialists": {
                "mathematics": {
                    "model_path": "models/phi3_mathematics_tutor",
                    "domains": ["algebra", "geometry", "trigonometry", "calculus"],
                    "tools": ["calculator", "graphing", "latex_renderer", "equation_solver"]
                },
                "science": {
                    "model_path": "models/phi3_science_tutor", 
                    "domains": ["physics", "chemistry", "biology", "earth_science"],
                    "tools": ["data_analyzer", "simulation_runner", "lab_guide"]
                },
                "english": {
                    "model_path": "models/phi3_english_tutor",
                    "domains": ["creative_writing", "literature", "reading_comprehension"],
                    "tools": ["text_analyzer", "writing_assistant", "literature_database"]
                }
                # Additional specialists...
            }
        }
        
        import json
        config_file = self.base_path / "models" / "deployment_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"📋 Deployment config saved: {config_file}")

if __name__ == "__main__":
    orchestrator = TrainingOrchestrator()
    orchestrator.run_full_pipeline()
'''

        orchestrator_file = (
            self.base_path / "scripts" / "run_academic_training_pipeline.py"
        )
        with open(orchestrator_file, "w", encoding="utf-8") as f:
            f.write(orchestrator_content)

        return orchestrator_file

    def prepare_training_pipeline(self):
        """Prepare the complete training pipeline."""
        print("🎯 Preparing Academic Training Pipeline...")

        # 1. Prepare tool control training
        tool_training_file = self.prepare_tool_control_training()

        # 2. Create tiny model training script
        tiny_script = self.create_tiny_model_training_script(tool_training_file)
        print(f"✅ Created tiny controller training script: {tiny_script.name}")

        # 3. Create Phi-3 specialist training scripts
        for domain, config in self.phi3_configs.items():
            specialist_script = self.create_phi3_training_script(domain, config)
            print(
                f"✅ Created {domain} specialist training script: {specialist_script.name}"
            )

        # 4. Create training orchestrator
        orchestrator_script = self.create_training_orchestrator()
        print(f"✅ Created training orchestrator: {orchestrator_script.name}")

        # 5. Create summary
        self.create_training_summary()

        print("\\n🎉 Academic Training Pipeline Ready!")
        print("🚀 Run: python scripts/run_academic_training_pipeline.py")

    def create_training_summary(self):
        """Create a summary of the training pipeline."""
        summary = {
            "pipeline_overview": {
                "tiny_tool_controller": {
                    "model": self.tiny_model_config["base_model"],
                    "purpose": "Fast tool classification",
                    "target_latency": self.tiny_model_config["target_latency"],
                    "training_data": "consolidated_tool_control.jsonl",
                },
                "phi3_specialists": {},
            },
            "training_sequence": [
                "1. Train tiny tool controller for fast classification",
                "2. Train domain-specific Phi-3 specialists",
                "3. Create deployment configuration",
                "4. Test integrated pipeline",
            ],
            "data_distribution": {},
            "expected_outcomes": {
                "tiny_controller": "Sub-100ms tool classification",
                "phi3_specialists": "Domain-aware educational responses",
                "integration": "Seamless audio → tool → specialist pipeline",
            },
        }

        # Add specialist details
        for domain, config in self.phi3_configs.items():
            summary["pipeline_overview"]["phi3_specialists"][domain] = {
                "model": config["base_model"],
                "specialization": config["specialization"],
                "output_name": config["output_name"],
            }

        # Read training manifest for data distribution
        try:
            manifest_file = self.academic_path / "training_manifest.json"
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
                summary["data_distribution"] = {
                    domain: info["example_count"]
                    for domain, info in manifest["academic_domains"].items()
                }
        except Exception as e:
            print(f"Warning: Could not read training manifest: {e}")

        # Save summary
        summary_file = self.base_path / "docs" / "ACADEMIC_TRAINING_SUMMARY.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("# Academic Training Pipeline Summary\\n\\n")
            f.write(json.dumps(summary, indent=2))

        print(f"📋 Training summary saved: {summary_file}")


def main():
    print("🎓 Academic Domain Training Pipeline Setup")
    print("=" * 50)

    pipeline = AcademicTrainingPipeline()
    pipeline.prepare_training_pipeline()


if __name__ == "__main__":
    main()
