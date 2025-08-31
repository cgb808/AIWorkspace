#!/usr/bin/env python3
"""
Standard Dataset Preparation for Calculative Fine-tuning
Prepares subject-specific datasets according to the standard methodology
"""

import json
import os
from pathlib import Path


class StandardDatasetPreparator:
    """Prepares datasets for the standard calculative fine-tuning pipeline"""

    def __init__(self, subject):
        self.subject = subject
        self.SUBJECT_MAPPINGS = {
            "mathematics": [
                "microsoft_orca-math-word-problems-200k_instructional.jsonl",
                "MARIO-Math-Reasoning_AlphaMath-Trainset_instructional.jsonl",
            ],
            "english": [
                "euclaise_writingprompts_instructional.jsonl",
                "Gryphe_Opus-WritingPrompts_instructional.jsonl",
                "rajpurkar_squad_instructional.jsonl",
                "ehovy_race_middle_instructional.jsonl",
                "deepmind_narrativeqa_instructional.jsonl",
            ],
            "science": [
                "abhi26_dpo-scientific-reasoning_instructional.jsonl",
                "zeroshot_arxiv-biology_instructional.jsonl",
            ],
        }

    def create_combined_dataset(
        self, download_dir="data/downloaded", output_dir="data/standard"
    ):
        """Create combined dataset for the subject"""
        os.makedirs(output_dir, exist_ok=True)

        print(f"📚 Preparing STANDARD {self.subject.upper()} dataset...")

        combined_data = []
        stats = {}

        for filename in self.SUBJECT_MAPPINGS[self.subject]:
            filepath = Path(download_dir) / filename

            if filepath.exists():
                with open(filepath, "r") as f:
                    examples = [json.loads(line) for line in f if line.strip()]
                    combined_data.extend(examples)
                    stats[filename] = len(examples)
                    print(f"  ✅ {filename}: {len(examples)} examples")
            else:
                print(f"  ⚠️  {filename}: Not found")
                stats[filename] = 0

        # Shuffle and split if needed
        import random

        random.shuffle(combined_data)

        # Save combined dataset
        output_file = Path(output_dir) / f"{self.subject}_standard_dataset.jsonl"
        with open(output_file, "w") as f:
            for example in combined_data:
                f.write(json.dumps(example) + "\n")

        # Save statistics
        stats_file = Path(output_dir) / f"{self.subject}_dataset_stats.json"
        total_stats = {
            "subject": self.subject,
            "total_examples": len(combined_data),
            "source_files": stats,
            "output_file": str(output_file),
            "recommended_phases": "5-phase calculative training",
        }

        with open(stats_file, "w") as f:
            json.dump(total_stats, f, indent=2)

        print(f"\n✅ STANDARD {self.subject.upper()} DATASET PREPARED:")
        print(f"   📊 Total examples: {len(combined_data):,}")
        print(f"   📄 Dataset file: {output_file}")
        print(f"   📈 Stats file: {stats_file}")

        return str(output_file), len(combined_data)


def main():
    """Prepare all standard datasets"""
    subjects = ["mathematics", "english", "science"]

    print("🎯 PREPARING ALL STANDARD DATASETS")
    print("=" * 50)

    for subject in subjects:
        preparator = StandardDatasetPreparator(subject)
        dataset_file, count = preparator.create_combined_dataset()
        print()

    print("✅ ALL STANDARD DATASETS PREPARED!")
    print("\nUsage examples:")
    print(
        "  python3 scripts/standard_calculative_finetune.py --train-file data/standard/mathematics_standard_dataset.jsonl --subject mathematics --output-dir models/"
    )
    print(
        "  python3 scripts/standard_calculative_finetune.py --train-file data/standard/english_standard_dataset.jsonl --subject english --output-dir models/"
    )


if __name__ == "__main__":
    main()
