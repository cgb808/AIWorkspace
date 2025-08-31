#!/usr/bin/env python3
"""
Migration Script - Move existing files to organized structure
"""

import shutil
from pathlib import Path


def migrate_files():
    """Actually move files to the new organized structure"""

    workspace = Path("/home/cgbowen/AIWorkspace")

    print("🚚 MIGRATING FILES TO ORGANIZED STRUCTURE")
    print("=" * 60)

    # Create a migration log
    migration_log = []

    def safe_move(source, destination, description):
        """Safely move files with logging"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if source_path.exists():
                # Create destination directory if it doesn't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the file/directory
                shutil.move(str(source_path), str(dest_path))
                print(
                    f"✅ Moved: {source_path.name} → {dest_path.relative_to(workspace)}"
                )
                migration_log.append(f"SUCCESS: {source} → {destination}")
                return True
            else:
                print(f"⚠️  Not found: {source}")
                migration_log.append(f"NOT_FOUND: {source}")
                return False
        except Exception as e:
            print(f"❌ Error moving {source}: {e}")
            migration_log.append(f"ERROR: {source} - {e}")
            return False

    # 1. Migrate Training Scripts
    print("\n🚀 Migrating Training Scripts...")
    training_scripts = [
        "scripts/hybrid_model_trainer.py",
        "scripts/calculative_epoch_strategy.py",
        "scripts/create_hybrid_dataset.py",
        "scripts/final_epoch_calculation.py",
        "scripts/hybrid_epoch_visualization.py",
    ]

    for script in training_scripts:
        source = workspace / script
        dest = workspace / "fine_tuning/training/scripts" / Path(script).name
        safe_move(source, dest, "Training script")

    # 2. Migrate Validation Scripts
    print("\n✅ Migrating Validation Scripts...")
    validation_scripts = [
        "scripts/ultimate_models_comparison.py",
        "scripts/test_tutoring_model.py",
    ]

    for script in validation_scripts:
        source = workspace / script
        dest = workspace / "fine_tuning/validation/scripts" / Path(script).name
        safe_move(source, dest, "Validation script")

    # 3. Migrate Tooling Scripts
    print("\n🛠️ Migrating Tooling Scripts...")
    tooling_migrations = {
        "scripts/tutoring_ecosystem_tooling_analysis.py": "fine_tuning/tooling/coordination/",
        "scripts/memory_rag_bridge.py": "fine_tuning/tooling/rag/",
    }

    for script, dest_dir in tooling_migrations.items():
        source = workspace / script
        dest = workspace / dest_dir / Path(script).name
        safe_move(source, dest, "Tooling script")

    # 4. Migrate Dataset Manifests
    print("\n📊 Migrating Dataset Manifests...")
    manifest_files = list(workspace.glob("data/MANIFEST_*.json")) + list(
        workspace.glob("data/SUMMARY_*.txt")
    )

    for manifest in manifest_files:
        dest = workspace / "fine_tuning/datasets/manifests" / manifest.name
        safe_move(manifest, dest, "Dataset manifest")

    # 5. Migrate Documentation
    print("\n📚 Migrating Documentation...")
    doc_migrations = {
        "docs/TUTORING_CALCULATIVE_IMPLEMENTATION.md": "documentation/fine_tuning/",
        "docs/LEONARDO_RAG_INTEGRATION.md": "documentation/architecture/",
        "docs/LEONARDO_FINE_TUNING.md": "documentation/architecture/",
        "docs/MIRA_AVATAR_INTEGRATION.md": "documentation/architecture/",
        "docs/HYBRID_RETRIEVAL_ARCHITECTURE.md": "documentation/architecture/",
        "docs/EDUCATIONAL_EXCELLENCE_EXAMPLES.md": "documentation/tutorials/",
    }

    for doc, dest_dir in doc_migrations.items():
        source = workspace / doc
        dest = workspace / dest_dir / Path(doc).name
        safe_move(source, dest, "Documentation")

    # 6. Migrate Infrastructure
    print("\n🏗️ Migrating Infrastructure...")
    infra_migrations = {
        "docker-compose.yml": "infrastructure/docker/",
        "Dockerfile": "infrastructure/docker/",
        "requirements.txt": "infrastructure/configs/",
        "requirements-dev.txt": "infrastructure/configs/",
        "pyproject.toml": "infrastructure/configs/",
        "pyrightconfig.json": "infrastructure/configs/",
    }

    for file, dest_dir in infra_migrations.items():
        source = workspace / file
        dest = workspace / dest_dir / file
        safe_move(source, dest, "Infrastructure file")

    # 7. Copy (don't move) critical datasets to preserve existing structure temporarily
    print("\n📦 Copying Critical Datasets...")

    # Copy key datasets to new structure while keeping originals
    dataset_copies = {
        "data/hybrid/hybrid_methodology_math_dataset.jsonl": "fine_tuning/datasets/processed/hybrid/",
        "data/next_epoch/final_balanced_dataset.jsonl": "fine_tuning/datasets/processed/next_epoch/",
        "data/tutoring_datasets/": "fine_tuning/datasets/processed/tutoring/",
    }

    for source_path, dest_dir in dataset_copies.items():
        source = workspace / source_path
        dest_base = workspace / dest_dir

        if source.exists():
            dest_base.mkdir(parents=True, exist_ok=True)

            if source.is_file():
                dest = dest_base / source.name
                shutil.copy2(source, dest)
                print(f"📋 Copied: {source.name} → {dest.relative_to(workspace)}")
            elif source.is_dir():
                dest = dest_base / source.name
                if not dest.exists():
                    shutil.copytree(source, dest)
                    print(f"📋 Copied: {source.name}/ → {dest.relative_to(workspace)}")

    # Save migration log
    log_file = workspace / "fine_tuning/migration_log.txt"
    with open(log_file, "w") as f:
        f.write("FINE-TUNING WORKSPACE MIGRATION LOG\n")
        f.write("=" * 50 + "\n\n")
        for entry in migration_log:
            f.write(f"{entry}\n")

    print(f"\n📝 Migration log saved: {log_file.relative_to(workspace)}")

    return migration_log


def main():
    """Execute the migration"""

    print("🏗️  EXECUTING WORKSPACE MIGRATION")
    print("=" * 50)

    migration_log = migrate_files()

    print("\n🎉 MIGRATION COMPLETE!")
    print("=" * 40)
    print("✅ Files migrated to organized structure")
    print(f"📝 {len(migration_log)} operations logged")
    print("\n🧭 Next: python navigate_finetuning.py")


if __name__ == "__main__":
    main()
