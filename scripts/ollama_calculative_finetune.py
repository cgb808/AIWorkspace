#!/usr/bin/env python3
"""
Ollama-Based Calculative Fine-tuning Pipeline
Uses local Ollama models for calculative fine-tuning methodology
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime
import time
import random

class OllamaCalculativeFineTuner:
    """Calculative fine-tuning using local Ollama models"""
    
    def __init__(self, model_name="phi3:mini", subject="mathematics"):
        self.model_name = model_name
        self.subject = subject
        self.ollama_url = "http://localhost:11435"  # Docker-compose exposed port
        self.output_base = f"models/ollama_{subject}_phi3"
        
        # Phase configuration for calculative training
        self.PHASE_CONFIG = {
            "phase_1": {
                "name": "Subject Matter Expertise",
                "focus": "Core knowledge building",
                "examples_per_phase": 500,
                "description": "Establish foundational subject expertise"
            },
            "phase_2": {
                "name": "Teaching Methodology", 
                "focus": "Instructional skill development",
                "examples_per_phase": 300,
                "description": "Develop teaching and explanation capabilities"
            },
            "phase_3": {
                "name": "Communication Refinement",
                "focus": "Response style and clarity",
                "examples_per_phase": 200,
                "description": "Refine communication patterns and style"
            }
        }
    
    def check_ollama_connection(self):
        """Verify Ollama is accessible and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                print(f"❌ Ollama not accessible at {self.ollama_url}")
                return False
            
            # Check if our model is available
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if self.model_name not in model_names:
                print(f"❌ Model {self.model_name} not found. Available: {model_names}")
                return False
                
            print(f"✅ Ollama connected - Model {self.model_name} available")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            return False
    
    def test_model_response(self, test_prompt):
        """Test model response to ensure it's working"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response')
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Exception: {e}"
    
    def simulate_calculative_training(self, dataset_file):
        """Simulate calculative training phases with the dataset"""
        print("🎯 OLLAMA CALCULATIVE FINE-TUNING SIMULATION")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Subject: {self.subject}")
        print(f"Dataset: {dataset_file}")
        print(f"Output: {self.output_base}")
        
        # Load dataset
        with open(dataset_file, 'r') as f:
            examples = [json.loads(line) for line in f if line.strip()]
        
        print(f"📊 Total examples available: {len(examples):,}")
        
        # Test initial model capability
        test_prompt = f"Solve this {self.subject} problem: What is 2+2?"
        initial_response = self.test_model_response(test_prompt)
        print(f"🧪 Initial model test: '{test_prompt}' -> '{initial_response[:100]}...'")
        
        # Execute training phases
        trained_examples = 0
        phase_results = {}
        
        for phase_name, phase_config in self.PHASE_CONFIG.items():
            print(f"\n📚 PHASE: {phase_config['name']}")
            print(f"   Focus: {phase_config['focus']}")
            print(f"   Target Examples: {phase_config['examples_per_phase']}")
            
            # Select examples for this phase
            phase_examples = examples[trained_examples:trained_examples + phase_config['examples_per_phase']]
            actual_examples = len(phase_examples)
            
            # Simulate training on examples
            print(f"   🔄 Processing {actual_examples} examples...")
            
            # Sample a few examples to test with
            sample_examples = random.sample(phase_examples, min(3, len(phase_examples)))
            
            phase_responses = []
            for i, example in enumerate(sample_examples):
                prompt = example.get('instruction', '')
                if prompt:
                    print(f"      Testing example {i+1}: {prompt[:80]}...")
                    response = self.test_model_response(prompt)
                    phase_responses.append({
                        'prompt': prompt[:200],
                        'expected': example.get('output', ''),
                        'model_response': response[:200]
                    })
                    time.sleep(0.5)  # Rate limiting
            
            # Save phase results
            phase_results[phase_name] = {
                'config': phase_config,
                'examples_processed': actual_examples,
                'sample_responses': phase_responses,
                'timestamp': datetime.now().isoformat()
            }
            
            trained_examples += actual_examples
            print(f"   ✅ Phase completed - {actual_examples} examples processed")
        
        # Create output directory and save results
        os.makedirs(self.output_base, exist_ok=True)
        
        # Save comprehensive training log
        training_log = {
            'model': self.model_name,
            'subject': self.subject,
            'methodology': 'calculative_phases',
            'total_examples_processed': trained_examples,
            'phases': phase_results,
            'initial_test': {
                'prompt': test_prompt,
                'response': initial_response
            },
            'completion_time': datetime.now().isoformat(),
            'status': 'simulation_completed'
        }
        
        log_file = Path(self.output_base) / f"calculative_training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(training_log, f, indent=2)
        
        print(f"\n🎉 CALCULATIVE TRAINING SIMULATION COMPLETED!")
        print(f"   📊 Total Examples Processed: {trained_examples:,}")
        print(f"   📋 Phases Completed: {len(phase_results)}")
        print(f"   📁 Results Saved: {log_file}")
        print(f"   🔬 Model: {self.model_name} (via Ollama)")
        
        return log_file

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Calculative Fine-tuning")
    parser.add_argument("--dataset", required=True, help="Path to training dataset")
    parser.add_argument("--subject", default="mathematics", help="Subject specialization")
    parser.add_argument("--model", default="phi3:mini", help="Ollama model name")
    
    args = parser.parse_args()
    
    # Create tuner and verify setup
    tuner = OllamaCalculativeFineTuner(
        model_name=args.model,
        subject=args.subject
    )
    
    # Check Ollama connection
    if not tuner.check_ollama_connection():
        print("❌ Please ensure Ollama is running and the model is available")
        print("   Run: docker exec ollama ollama list")
        return
    
    # Execute calculative training simulation
    log_file = tuner.simulate_calculative_training(args.dataset)
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Review training simulation results in {log_file}")
    print(f"   2. Analyze model responses across phases")
    print(f"   3. Consider actual fine-tuning implementation")
    print(f"   4. Deploy specialized {args.subject} model")

if __name__ == "__main__":
    main()
