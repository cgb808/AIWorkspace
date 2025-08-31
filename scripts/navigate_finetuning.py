#!/usr/bin/env python3
"""
Quick Navigation Script for Fine-Tuning Operations
"""

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

    choice = input("\nSelect area (1-6): ").strip()

    paths = {
        "1": base / "datasets",
        "2": base / "models",
        "3": base / "training",
        "4": base / "validation",
        "5": base / "tooling",
        "6": Path("/home/cgbowen/AIWorkspace/documentation"),
    }

    if choice in paths:
        target = paths[choice]
        print(f"\n📁 Opening: {target}")
        os.chdir(target)
        subprocess.run(["ls", "-la"])
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
