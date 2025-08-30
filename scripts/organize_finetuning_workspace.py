#!/usr/bin/env python3
"""
Fine-Tuning Workspace Organization Script
Creates clean, nested structure for all fine-tuning operations
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class FineTuningOrganizer:
    """Organize workspace into clean fine-tuning structure"""
    
    def __init__(self, workspace_root="/home/cgbowen/AIWorkspace"):
        self.workspace_root = Path(workspace_root)
        self.backup_dir = self.workspace_root / "backup_pre_organization"
        
        # Define the new clean structure
        self.new_structure = {
            "fine_tuning/": {
                "datasets/": {
                    "raw/": "Original, unprocessed datasets",
                    "processed/": "Cleaned and formatted datasets", 
                    "splits/": "Train/validation/test splits",
                    "manifests/": "Dataset metadata and statistics"
                },
                "models/": {
                    "base/": "Original base models (phi3, mistral, etc)",
                    "checkpoints/": "Training checkpoints and intermediate saves",
                    "fine_tuned/": "Completed fine-tuned models",
                    "configs/": "Model configuration files"
                },
                "training/": {
                    "scripts/": "Training and fine-tuning scripts",
                    "configs/": "Training configuration files", 
                    "logs/": "Training logs and metrics",
                    "experiments/": "Experimental training runs"
                },
                "validation/": {
                    "scripts/": "Model validation and testing scripts",
                    "results/": "Validation results and comparisons",
                    "benchmarks/": "Benchmark tests and scores"
                },
                "tooling/": {
                    "rag/": "RAG integration tools and scripts",
                    "audio/": "TTS/STT and audio processing tools",
                    "visual/": "Visualization and diagram generation",
                    "coordination/": "Multi-model coordination scripts"
                }
            },
            "documentation/": {
                "fine_tuning/": "Fine-tuning specific documentation",
                "architecture/": "System architecture documentation", 
                "tutorials/": "How-to guides and tutorials",
                "research/": "Research notes and findings"
            },
            "infrastructure/": {
                "docker/": "Docker configurations and compose files",
                "configs/": "System configuration files",
                "monitoring/": "System monitoring and health checks"
            }
        }
    
    def create_directory_structure(self):
        """Create the new organized directory structure"""
        
        print("🏗️  CREATING ORGANIZED FINE-TUNING STRUCTURE")
        print("=" * 60)
        
        def create_nested_dirs(base_path, structure_dict):
            """Recursively create nested directories"""
            for name, content in structure_dict.items():
                dir_path = base_path / name
                dir_path.mkdir(parents=True, exist_ok=True)
                
                if isinstance(content, dict):
                    create_nested_dirs(dir_path, content)
                else:
                    # Create README for leaf directories
                    readme_path = dir_path / "README.md"
                    if not readme_path.exists():
                        with open(readme_path, 'w') as f:
                            f.write(f"# {name.rstrip('/')}\n\n{content}\n")
                    print(f"📁 Created: {dir_path.relative_to(self.workspace_root)}")
        
        create_nested_dirs(self.workspace_root, self.new_structure)
        
        print(f"\n✅ Directory structure created successfully!")
    
    def identify_migration_plan(self):
        """Identify what needs to be moved where"""
        
        print(f"\n📋 IDENTIFYING MIGRATION PLAN")
        print("=" * 50)
        
        migration_plan = {
            # Datasets
            "data/": "fine_tuning/datasets/raw/",
            "data/hybrid/": "fine_tuning/datasets/processed/hybrid/",
            "data/next_epoch/": "fine_tuning/datasets/processed/next_epoch/", 
            "data/tutoring_datasets/": "fine_tuning/datasets/processed/tutoring/",
            "data/MANIFEST_*.json": "fine_tuning/datasets/manifests/",
            "data/SUMMARY_*.txt": "fine_tuning/datasets/manifests/",
            
            # Models
            "models/": "fine_tuning/models/base/",
            
            # Scripts - Training related
            "scripts/*trainer*.py": "fine_tuning/training/scripts/",
            "scripts/*epoch*.py": "fine_tuning/training/scripts/",
            "scripts/*finetune*.py": "fine_tuning/training/scripts/",
            "scripts/*hybrid*.py": "fine_tuning/training/scripts/",
            
            # Scripts - Validation related  
            "scripts/*comparison*.py": "fine_tuning/validation/scripts/",
            "scripts/*test*.py": "fine_tuning/validation/scripts/",
            
            # Scripts - Tooling
            "scripts/*rag*.py": "fine_tuning/tooling/rag/",
            "scripts/*audio*.py": "fine_tuning/tooling/audio/",
            "scripts/*visual*.py": "fine_tuning/tooling/visual/",
            "scripts/*ecosystem*.py": "fine_tuning/tooling/coordination/",
            
            # Documentation
            "docs/TUTORING_*.md": "documentation/fine_tuning/",
            "docs/LEONARDO_*.md": "documentation/architecture/",
            "docs/MIRA_*.md": "documentation/architecture/",
            "docs/HYBRID_*.md": "documentation/architecture/",
            "docs/EDUCATIONAL_*.md": "documentation/tutorials/",
            
            # Infrastructure
            "docker-compose.yml": "infrastructure/docker/",
            "Dockerfile": "infrastructure/docker/",
            "*.json": "infrastructure/configs/",
            "requirements*.txt": "infrastructure/configs/"
        }
        
        print("📦 Migration Plan:")
        for source, destination in migration_plan.items():
            print(f"   {source} → {destination}")
        
        return migration_plan
    
    def create_master_index(self):
        """Create master index files for navigation"""
        
        print(f"\n📚 CREATING MASTER INDEX FILES")
        print("=" * 50)
        
        # Main README for fine_tuning directory
        fine_tuning_readme = self.workspace_root / "fine_tuning" / "README.md"
        with open(fine_tuning_readme, 'w') as f:
            f.write("""# Fine-Tuning Operations Center

## Directory Structure

### 📊 Datasets
- `datasets/raw/` - Original, unprocessed datasets
- `datasets/processed/` - Cleaned and formatted datasets  
- `datasets/splits/` - Train/validation/test splits
- `datasets/manifests/` - Dataset metadata and statistics

### 🤖 Models
- `models/base/` - Original base models (phi3, mistral, etc)
- `models/checkpoints/` - Training checkpoints and intermediate saves
- `models/fine_tuned/` - Completed fine-tuned models
- `models/configs/` - Model configuration files

### 🚀 Training
- `training/scripts/` - Training and fine-tuning scripts
- `training/configs/` - Training configuration files
- `training/logs/` - Training logs and metrics
- `training/experiments/` - Experimental training runs

### ✅ Validation
- `validation/scripts/` - Model validation and testing scripts
- `validation/results/` - Validation results and comparisons
- `validation/benchmarks/` - Benchmark tests and scores

### 🛠️ Tooling
- `tooling/rag/` - RAG integration tools and scripts
- `tooling/audio/` - TTS/STT and audio processing tools
- `tooling/visual/` - Visualization and diagram generation
- `tooling/coordination/` - Multi-model coordination scripts

## Quick Start Commands

```bash
# Start training environment
cd fine_tuning/training/scripts
python hybrid_model_trainer.py

# Run validation tests
cd fine_tuning/validation/scripts
python ultimate_models_comparison.py

# Check dataset statistics
cd fine_tuning/datasets/manifests
cat latest_dataset_stats.json
```

## Current Status
- ✅ Hybrid methodology proven (46-point winner)
- ✅ 8-epoch calculative strategy established  
- ✅ 1,842 examples in balanced dataset
- 🔄 Personality integration in progress
- 🔄 Multi-model coordination development
""")
        
        # Create quick navigation script
        nav_script = self.workspace_root / "navigate_finetuning.py"
        with open(nav_script, 'w') as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Quick Navigation Script for Fine-Tuning Operations
\"\"\"

import os
import subprocess
from pathlib import Path

def main():
    base = Path("/home/cgbowen/AIWorkspace/fine_tuning")
    
    print("🧭 FINE-TUNING NAVIGATION")
    print("=" * 40)
    print("1. 📊 Datasets")
    print("2. 🤖 Models") 
    print("3. 🚀 Training")
    print("4. ✅ Validation")
    print("5. 🛠️ Tooling")
    print("6. 📚 Documentation")
    
    choice = input("\\nSelect area (1-6): ").strip()
    
    paths = {
        "1": base / "datasets",
        "2": base / "models", 
        "3": base / "training",
        "4": base / "validation",
        "5": base / "tooling",
        "6": Path("/home/cgbowen/AIWorkspace/documentation")
    }
    
    if choice in paths:
        target = paths[choice]
        print(f"\\n📁 Opening: {target}")
        os.chdir(target)
        subprocess.run(["ls", "-la"])
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
""")
        
        os.chmod(nav_script, 0o755)
        
        print("✅ Master index files created!")
    
    def create_organization_summary(self):
        """Create summary of the new organization"""
        
        summary = {
            "organization_date": datetime.now().isoformat(),
            "workspace_root": str(self.workspace_root),
            "structure_created": True,
            "key_directories": [
                "fine_tuning/datasets/",
                "fine_tuning/models/", 
                "fine_tuning/training/",
                "fine_tuning/validation/",
                "fine_tuning/tooling/",
                "documentation/",
                "infrastructure/"
            ],
            "navigation_tools": [
                "fine_tuning/README.md",
                "navigate_finetuning.py"
            ],
            "next_steps": [
                "Migrate existing files to new structure",
                "Update scripts with new paths",
                "Test training pipeline with new organization",
                "Integrate personality dataset when ready"
            ]
        }
        
        summary_file = self.workspace_root / "workspace_organization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    """Organize the fine-tuning workspace"""
    
    organizer = FineTuningOrganizer()
    
    print("🏗️  FINE-TUNING WORKSPACE ORGANIZATION")
    print("=" * 70)
    print("Goal: Create clean, nested structure for all fine-tuning operations")
    print("=" * 70)
    
    # Create directory structure
    organizer.create_directory_structure()
    
    # Identify what needs to be moved
    migration_plan = organizer.identify_migration_plan()
    
    # Create master index files
    organizer.create_master_index()
    
    # Create summary
    summary = organizer.create_organization_summary()
    
    print(f"\n🎉 WORKSPACE ORGANIZATION COMPLETE!")
    print("=" * 50)
    print("✅ Clean directory structure created")
    print("✅ Migration plan identified")
    print("✅ Master index files created")
    print("✅ Navigation tools ready")
    print(f"\n📁 Use: python navigate_finetuning.py")
    print(f"📚 Check: fine_tuning/README.md")
    print(f"\n🎯 Ready for your personality dataset integration!")

if __name__ == "__main__":
    main()
