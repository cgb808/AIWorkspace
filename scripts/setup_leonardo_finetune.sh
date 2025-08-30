#!/bin/bash
# Leonardo Fine-Tuning Setup Script
# Prepares the environment for family context and educational fine-tuning

set -e

echo "🎓 Leonardo Fine-Tuning Setup"
echo "============================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
FINE_TUNE_DIR="$WORKSPACE_ROOT/model_finetune"
TRAINING_DATA_DIR="$FINE_TUNE_DIR/leonardo_training"
VENV_PATH="$WORKSPACE_ROOT/.venv"

# Create directory structure
echo "📁 Creating fine-tuning directory structure..."
mkdir -p "$FINE_TUNE_DIR"
mkdir -p "$TRAINING_DATA_DIR"
mkdir -p "$TRAINING_DATA_DIR/family_context"
mkdir -p "$TRAINING_DATA_DIR/educational_excellence"
mkdir -p "$TRAINING_DATA_DIR/validation"
mkdir -p "$FINE_TUNE_DIR/models"
mkdir -p "$FINE_TUNE_DIR/checkpoints"
mkdir -p "$FINE_TUNE_DIR/logs"

# Activate virtual environment
echo "🐍 Activating Python environment..."
source "$VENV_PATH/bin/activate"

# Install fine-tuning dependencies
echo "📦 Installing fine-tuning dependencies..."
pip install --quiet unsloth[colab-new] --upgrade
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install --quiet xformers transformers datasets accelerate peft bitsandbytes
pip install --quiet wandb tensorboard jupyter ipywidgets

echo "✅ Fine-tuning dependencies installed"

# Create training script template
cat > "$FINE_TUNE_DIR/leonardo_finetune.py" << 'EOF'
"""
Leonardo Fine-Tuning Script
Family Context & Educational Excellence Training
"""

import os
import json
import torch
from datetime import datetime
from datasets import Dataset
from transformers import TrainingArguments
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import wandb

# Configuration
MODEL_NAME = "unsloth/mistral-7b-v0.3-bnb-4bit"
MAX_SEQ_LENGTH = 2048
LOAD_IN_4BIT = True

def load_training_data(data_path):
    """Load and prepare training data from JSONL files"""
    data = []
    for file in os.listdir(data_path):
        if file.endswith('.jsonl'):
            with open(os.path.join(data_path, file), 'r') as f:
                for line in f:
                    data.append(json.loads(line))
    return data

def format_training_data(examples):
    """Format data for fine-tuning"""
    formatted = []
    for example in examples:
        conversation = [
            {"role": "user", "content": example["instruction"] + "\n" + example["input"]},
            {"role": "assistant", "content": example["output"]}
        ]
        formatted.append({"conversation": conversation})
    return formatted

def main():
    print("🎓 Starting Leonardo Fine-Tuning")
    
    # Initialize model and tokenizer
    print("📝 Loading base model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=LOAD_IN_4BIT,
    )
    
    # Configure LoRA
    print("⚙️ Configuring LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    
    # Set up chat template
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="mistral",
    )
    
    # Load training data
    epoch = input("Enter epoch number (1 for family context, 2 for educational excellence): ")
    data_path = f"leonardo_training/{'family_context' if epoch == '1' else 'educational_excellence'}"
    
    print(f"📚 Loading training data from {data_path}...")
    training_examples = load_training_data(data_path)
    formatted_data = format_training_data(training_examples)
    
    print(f"📊 Training examples loaded: {len(formatted_data)}")
    
    # Create dataset
    dataset = Dataset.from_list(formatted_data)
    
    # Training configuration
    training_args = TrainingArguments(
        output_dir=f"./checkpoints/leonardo_epoch_{epoch}",
        num_train_epochs=1,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        warmup_ratio=0.1,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        dataloader_pin_memory=True,
        remove_unused_columns=False,
    )
    
    # Initialize trainer
    from trl import SFTTrainer
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="conversation",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
    )
    
    # Start training
    print(f"🚀 Starting epoch {epoch} training...")
    trainer.train()
    
    # Save the model
    save_path = f"./models/leonardo_epoch_{epoch}"
    print(f"💾 Saving model to {save_path}...")
    trainer.save_model(save_path)
    
    print("✅ Training complete!")
    print(f"📁 Model saved to: {save_path}")

if __name__ == "__main__":
    main()
EOF

# Create data validation script
cat > "$FINE_TUNE_DIR/validate_training_data.py" << 'EOF'
"""
Training Data Validation Script
Ensures quality and consistency of family context training data
"""

import json
import os
from pathlib import Path

def validate_jsonl_file(file_path):
    """Validate JSONL training data file"""
    errors = []
    valid_count = 0
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                
                # Check required fields
                required_fields = ["instruction", "input", "output"]
                for field in required_fields:
                    if field not in data:
                        errors.append(f"Line {line_num}: Missing field '{field}'")
                        continue
                
                # Check content quality
                if len(data.get("output", "")) < 10:
                    errors.append(f"Line {line_num}: Output too short")
                
                if "family" not in data.get("output", "").lower() and "child" not in data.get("output", "").lower():
                    errors.append(f"Line {line_num}: Output lacks family context")
                
                valid_count += 1
                
            except json.JSONDecodeError:
                errors.append(f"Line {line_num}: Invalid JSON")
    
    return valid_count, errors

def main():
    print("🔍 Validating Leonardo Training Data")
    print("===================================")
    
    training_dir = Path("leonardo_training")
    if not training_dir.exists():
        print("❌ Training data directory not found")
        return
    
    total_valid = 0
    total_errors = []
    
    for jsonl_file in training_dir.rglob("*.jsonl"):
        print(f"\n📄 Validating {jsonl_file}")
        valid_count, errors = validate_jsonl_file(jsonl_file)
        
        total_valid += valid_count
        total_errors.extend([f"{jsonl_file}: {error}" for error in errors])
        
        print(f"   ✅ Valid examples: {valid_count}")
        if errors:
            print(f"   ⚠️  Errors: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"      - {error}")
            if len(errors) > 5:
                print(f"      ... and {len(errors) - 5} more")
    
    print(f"\n📊 Summary:")
    print(f"   Total valid examples: {total_valid}")
    print(f"   Total errors: {len(total_errors)}")
    
    if len(total_errors) == 0:
        print("✅ All training data validated successfully!")
    else:
        print("⚠️  Please fix errors before training")

if __name__ == "__main__":
    main()
EOF

# Create example training data templates
cat > "$TRAINING_DATA_DIR/family_context/example_data.jsonl" << 'EOF'
{"instruction": "Help [Child's Name] understand why they should try harder in math", "input": "Child is feeling discouraged about fraction problems", "output": "I understand fractions can feel tricky, [Child's Name]. Remember, in our family we believe that challenges help us grow stronger. You showed this same persistence when you learned to ride your bike - you kept trying even when it was hard. Let's break these fractions down into smaller pieces, just like how we solve puzzles together as a family."}
{"instruction": "Provide study guidance for [Child's Name] based on their learning style", "input": "Child needs help organizing their homework routine", "output": "Since you're a visual learner, [Child's Name], let's create a colorful study schedule that you can see clearly. Remember how we organized your room with labels and pictures? We can use the same approach for your homework. Your family values organization and taking care of responsibilities, so this will help you succeed."}
{"instruction": "Encourage [Child's Name] to persevere with a difficult reading assignment", "input": "Child wants to give up on a challenging book", "output": "I know this book feels overwhelming right now, [Child's Name]. But think about our family motto about never giving up. Remember the story Grandpa told us about [family story]? He didn't give up either. Let's try reading just one page at a time, and I'll help you understand the big words. You're braver than you think."}
EOF

cat > "$TRAINING_DATA_DIR/educational_excellence/example_data.jsonl" << 'EOF'
{"instruction": "Explain photosynthesis to a 3rd grader using engaging examples", "input": "Student wants to understand how plants make food", "output": "Imagine plants are like little chefs in green kitchens! Just like you help in our family kitchen, plants have special ingredients they need to cook their food. They use sunlight (like turning on the oven), water from their roots (like getting water from the tap), and air through their leaves (like opening windows for fresh air). When they mix it all together, they make sugar food for themselves and give us fresh oxygen to breathe!"}
{"instruction": "Help a student understand the main idea of a story", "input": "Student struggling to identify the theme in 'Charlotte's Web'", "output": "Let's think about what Charlotte and Wilbur's friendship teaches us. Just like in our family, true friends support each other even when it's hard. Charlotte used her special talents (web spinning) to help Wilbur, even though it was difficult for her. The main idea is that real friendship means caring about someone else's happiness as much as your own. Can you think of times when you've been a good friend like Charlotte?"}
{"instruction": "Teach multiplication using real-world examples", "input": "Student needs to understand 6 x 4", "output": "Let's use something you love - imagine you're setting up chairs for a family gathering! If you put 4 chairs around each table, and you have 6 tables, how many chairs do you need total? Let's count together: table 1 has 4 chairs, table 2 has 4 more (that's 8), table 3 has 4 more (that's 12)... Keep going! Or we can think of it as 6 groups of 4, which equals 24 chairs. Multiplication is just a faster way to add equal groups!"}
EOF

# Create monitoring script
cat > "$FINE_TUNE_DIR/monitor_training.py" << 'EOF'
"""
Training Monitor Script
Real-time monitoring of Leonardo fine-tuning progress
"""

import time
import psutil
import GPUtil
from pathlib import Path

def monitor_training():
    """Monitor training progress and system resources"""
    print("🖥️  Leonardo Training Monitor")
    print("============================")
    
    while True:
        try:
            # GPU monitoring
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Assuming RTX 3060 Ti is first GPU
                print(f"🎮 GPU Utilization: {gpu.load*100:.1f}%")
                print(f"🧠 GPU Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB ({gpu.memoryUtil*100:.1f}%)")
                print(f"🌡️  GPU Temperature: {gpu.temperature}°C")
            
            # CPU and RAM
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            print(f"💻 CPU Usage: {cpu_percent:.1f}%")
            print(f"🧠 RAM Usage: {memory.percent:.1f}% ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)")
            
            # Check for log files
            log_dir = Path("./logs")
            if log_dir.exists():
                recent_logs = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                if recent_logs:
                    print(f"📝 Latest log: {recent_logs[0].name}")
            
            print("-" * 50)
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_training()
EOF

# Create test validation script
cat > "$FINE_TUNE_DIR/test_leonardo.py" << 'EOF'
"""
Leonardo Testing Script
Validates fine-tuned model responses for family context and educational quality
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from unsloth import FastLanguageModel

def load_leonardo_model(model_path):
    """Load fine-tuned Leonardo model"""
    print(f"🤖 Loading Leonardo from {model_path}...")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def test_family_context(model, tokenizer):
    """Test family context understanding"""
    test_prompts = [
        "Help [Child's Name] with their math homework",
        "Encourage [Child's Name] who is feeling frustrated",
        "Explain why honesty is important in our family",
    ]
    
    print("👨‍👩‍👧‍👦 Testing Family Context Understanding:")
    print("=" * 50)
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        print(f"🤖 Leonardo: {response}")
        print("-" * 30)

def test_educational_quality(model, tokenizer):
    """Test educational instruction quality"""
    test_prompts = [
        "Explain photosynthesis to a 4th grader",
        "Help with understanding fractions",
        "What's the main idea in this story about friendship",
    ]
    
    print("\n🎓 Testing Educational Quality:")
    print("=" * 50)
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        print(f"🤖 Leonardo: {response}")
        print("-" * 30)

def main():
    print("🧪 Leonardo Model Testing")
    print("========================")
    
    # Test different model checkpoints
    model_options = [
        "./models/leonardo_epoch_1",  # Family context
        "./models/leonardo_epoch_2",  # Educational excellence
    ]
    
    for model_path in model_options:
        if Path(model_path).exists():
            print(f"\n🎯 Testing {model_path}")
            model, tokenizer = load_leonardo_model(model_path)
            
            test_family_context(model, tokenizer)
            test_educational_quality(model, tokenizer)
            
            # Cleanup
            del model, tokenizer
            torch.cuda.empty_cache()
        else:
            print(f"⚠️  Model not found: {model_path}")

if __name__ == "__main__":
    from pathlib import Path
    main()
EOF

# Make scripts executable
chmod +x "$FINE_TUNE_DIR"/*.py

# Create configuration file
cat > "$FINE_TUNE_DIR/leonardo_config.json" << EOF
{
  "fine_tuning": {
    "base_model": "unsloth/mistral-7b-v0.3-bnb-4bit",
    "max_seq_length": 2048,
    "epochs": {
      "family_context": 1,
      "educational_excellence": 1
    },
    "lora_config": {
      "r": 16,
      "alpha": 32,
      "dropout": 0.1,
      "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    },
    "training_args": {
      "learning_rate": 2e-4,
      "batch_size": 2,
      "gradient_accumulation_steps": 8,
      "warmup_ratio": 0.1
    }
  },
  "hardware": {
    "gpu": "RTX 3060 Ti",
    "vram": "8GB",
    "load_in_4bit": true
  },
  "data_requirements": {
    "family_context_examples": 500,
    "educational_examples": 1000,
    "validation_split": 0.1
  }
}
EOF

echo ""
echo "✅ Leonardo Fine-Tuning Setup Complete!"
echo ""
echo "📁 Directory structure created:"
echo "   $FINE_TUNE_DIR/leonardo_training/family_context/"
echo "   $FINE_TUNE_DIR/leonardo_training/educational_excellence/"
echo "   $FINE_TUNE_DIR/models/"
echo "   $FINE_TUNE_DIR/checkpoints/"
echo ""
echo "🔧 Scripts created:"
echo "   leonardo_finetune.py - Main fine-tuning script"
echo "   validate_training_data.py - Data validation"
echo "   monitor_training.py - Training monitoring"
echo "   test_leonardo.py - Model testing"
echo ""
echo "📚 Next steps:"
echo "   1. Fill out family context data using the template in docs/FAMILY_CONTEXT_TEMPLATE.md"
echo "   2. Create educational training examples"
echo "   3. Run: python validate_training_data.py"
echo "   4. Run: python leonardo_finetune.py"
echo ""
echo "🎯 Remember: This creates a personalized AI tutor specifically for your family!"
