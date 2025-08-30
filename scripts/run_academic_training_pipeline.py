#!/usr/bin/env python3
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
        print(f"\n🚀 Starting: {description}")
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
                print(f"\n⚠️  Training pipeline stopped at: {description}")
                break
        
        total_duration = time.time() - total_start
        
        print(f"\n🎉 Training Pipeline Complete!")
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
