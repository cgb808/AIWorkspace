#!/usr/bin/env python3
"""
Dataset Balancing and Mixing
Implements stratified sampling to achieve target role distributions
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class DatasetBalancer:
    def __init__(self):
        # Target role percentages
        self.target_ratios = {
            "general_assistant": 55,
            "family_tutor": 15,
            "educational_expert": 15,
            "philosophical_guide": 10,
            "other": 5,  # catch-all for any other roles
        }

        self.stats = {
            "input_distribution": {},
            "target_distribution": {},
            "final_distribution": {},
            "sampling_actions": {},
        }

    def analyze_current_distribution(
        self, examples: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Analyze current role distribution"""
        distribution = defaultdict(int)

        for example in examples:
            role = example.get("meta", {}).get("role", "unknown")
            # Map unknown roles to 'other'
            if role not in self.target_ratios:
                role = "other"
            distribution[role] += 1

        return dict(distribution)

    def calculate_target_counts(self, total_examples: int) -> Dict[str, int]:
        """Calculate target counts for each role"""
        targets = {}

        for role, percentage in self.target_ratios.items():
            targets[role] = int(total_examples * percentage / 100)

        # Ensure we don't exceed total due to rounding
        actual_total = sum(targets.values())
        if actual_total != total_examples:
            # Adjust the largest category
            largest_role = max(targets.keys(), key=lambda k: targets[k])
            targets[largest_role] += total_examples - actual_total

        return targets

    def stratified_sample(
        self,
        examples_by_role: Dict[str, List[Dict[str, Any]]],
        target_counts: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        """Perform stratified sampling to achieve target distribution"""
        balanced_examples = []

        for role, target_count in target_counts.items():
            available_examples = examples_by_role.get(role, [])
            current_count = len(available_examples)

            if current_count == 0:
                print(f"Warning: No examples available for role '{role}'")
                self.stats["sampling_actions"][role] = "no_examples"
                continue

            if current_count <= target_count:
                # Use all available examples (undersample)
                selected = available_examples

                # If we need more, we could implement upsampling here
                if current_count < target_count:
                    print(
                        f"Note: Role '{role}' has {current_count} examples, need {target_count}"
                    )
                    # Simple upsampling by repeating examples
                    while len(selected) < target_count:
                        # Add random examples until we reach target
                        selected.append(random.choice(available_examples))

                    self.stats["sampling_actions"][
                        role
                    ] = f"upsampled_from_{current_count}_to_{target_count}"
                else:
                    self.stats["sampling_actions"][role] = f"used_all_{current_count}"
            else:
                # Downsample to target count
                selected = random.sample(available_examples, target_count)
                self.stats["sampling_actions"][
                    role
                ] = f"downsampled_from_{current_count}_to_{target_count}"

            balanced_examples.extend(selected)

        return balanced_examples

    def balance_dataset(
        self, input_file: str, output_file: str, target_size: int | None = None
    ) -> Dict[str, Any]:
        """Main balancing function"""
        print(f"Balancing dataset: {input_file}")

        # Load all examples
        examples = []
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    example = json.loads(line.strip())
                    examples.append(example)
                except json.JSONDecodeError:
                    continue

        original_size = len(examples)
        print(f"Loaded {original_size} examples")

        # Use provided target size or current size
        if target_size is None:
            target_size = original_size

        # Analyze current distribution
        current_dist = self.analyze_current_distribution(examples)
        self.stats["input_distribution"] = current_dist

        print("Current distribution:")
        for role, count in sorted(current_dist.items()):
            percentage = count / original_size * 100
            print(f"  {role}: {count} ({percentage:.1f}%)")

        # Calculate targets
        target_counts = self.calculate_target_counts(target_size)
        self.stats["target_distribution"] = target_counts

        print(f"\nTarget distribution (total: {target_size}):")
        for role, count in sorted(target_counts.items()):
            percentage = count / target_size * 100
            print(f"  {role}: {count} ({percentage:.1f}%)")

        # Group examples by role
        examples_by_role = defaultdict(list)
        for example in examples:
            role = example.get("meta", {}).get("role", "unknown")
            if role not in self.target_ratios:
                role = "other"
            examples_by_role[role].append(example)

        # Perform stratified sampling
        balanced_examples = self.stratified_sample(examples_by_role, target_counts)

        # Shuffle to mix roles
        random.shuffle(balanced_examples)

        # Calculate final distribution
        final_dist = self.analyze_current_distribution(balanced_examples)
        self.stats["final_distribution"] = final_dist

        print(f"\nFinal distribution (total: {len(balanced_examples)}):")
        for role, count in sorted(final_dist.items()):
            percentage = (
                count / len(balanced_examples) * 100 if balanced_examples else 0
            )
            print(f"  {role}: {count} ({percentage:.1f}%)")

        # Save balanced dataset
        with open(output_file, "w", encoding="utf-8") as f:
            for example in balanced_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        print(f"\nBalanced dataset saved to: {output_file}")

        return self.stats

    def create_train_val_split(
        self, input_file: str, train_file: str, val_file: str, val_ratio: float = 0.1
    ) -> Dict[str, Any]:
        """Create stratified train/validation split"""
        print(f"Creating train/val split from: {input_file}")

        # Load examples
        examples = []
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    example = json.loads(line.strip())
                    examples.append(example)
                except json.JSONDecodeError:
                    continue

        # Group by role for stratified split
        examples_by_role = defaultdict(list)
        for example in examples:
            role = example.get("meta", {}).get("role", "unknown")
            examples_by_role[role].append(example)

        train_examples = []
        val_examples = []

        # Stratified split for each role
        for role, role_examples in examples_by_role.items():
            random.shuffle(role_examples)

            val_count = max(1, int(len(role_examples) * val_ratio))
            train_count = len(role_examples) - val_count

            train_examples.extend(role_examples[:train_count])
            val_examples.extend(role_examples[train_count:])

        # Shuffle final splits
        random.shuffle(train_examples)
        random.shuffle(val_examples)

        # Save splits
        with open(train_file, "w", encoding="utf-8") as f:
            for example in train_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        with open(val_file, "w", encoding="utf-8") as f:
            for example in val_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        split_stats = {
            "total_examples": len(examples),
            "train_examples": len(train_examples),
            "val_examples": len(val_examples),
            "val_ratio": len(val_examples) / len(examples),
            "role_splits": {},
        }

        # Calculate role-wise split stats
        for role in examples_by_role.keys():
            train_role_count = sum(
                1 for ex in train_examples if ex.get("meta", {}).get("role") == role
            )
            val_role_count = sum(
                1 for ex in val_examples if ex.get("meta", {}).get("role") == role
            )

            split_stats["role_splits"][role] = {
                "train": train_role_count,
                "val": val_role_count,
                "total": len(examples_by_role[role]),
            }

        print(f"Train examples: {len(train_examples)}")
        print(f"Val examples: {len(val_examples)}")
        print(f"Val ratio: {len(val_examples) / len(examples):.3f}")

        return split_stats


def main():
    if len(sys.argv) < 3:
        print("Usage: python assemble_mix.py <input_file> <output_file> [target_size]")
        print(
            "   or: python assemble_mix.py --split <input_file> <train_file> <val_file> [val_ratio]"
        )
        sys.exit(1)

    if sys.argv[1] == "--split":
        if len(sys.argv) < 5:
            print(
                "Usage for split: python assemble_mix.py --split <input_file> <train_file> <val_file> [val_ratio]"
            )
            sys.exit(1)

        input_file = sys.argv[2]
        train_file = sys.argv[3]
        val_file = sys.argv[4]
        val_ratio = float(sys.argv[5]) if len(sys.argv) > 5 else 0.1

        if not Path(input_file).exists():
            print(f"Error: Input file not found: {input_file}")
            sys.exit(1)

        balancer = DatasetBalancer()
        split_stats = balancer.create_train_val_split(
            input_file, train_file, val_file, val_ratio
        )

        # Save split stats
        stats_file = input_file.replace(".jsonl", ".split_stats.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(split_stats, f, indent=2, ensure_ascii=False)

        print(f"Split stats saved to: {stats_file}")

    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        target_size = int(sys.argv[3]) if len(sys.argv) > 3 else None

        if not Path(input_file).exists():
            print(f"Error: Input file not found: {input_file}")
            sys.exit(1)

        # Set random seed for reproducibility
        random.seed(42)

        balancer = DatasetBalancer()
        stats = balancer.balance_dataset(input_file, output_file, target_size)

        # Save stats
        stats_file = output_file.replace(".jsonl", ".balance_stats.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"Balance stats saved to: {stats_file}")


if __name__ == "__main__":
    main()
