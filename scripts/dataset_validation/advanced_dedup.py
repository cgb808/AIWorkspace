#!/usr/bin/env python3
"""
Advanced Deduplication and Quality Control
Implements exact hash + MinHash signature deduplication
Includes safety and leakage detection
"""

import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from datasketch import MinHash, MinHashLSH

    MINHASH_AVAILABLE = True
except ImportError:
    print("Warning: datasketch not available. Using exact hash only.")
    MINHASH_AVAILABLE = False

    # Define dummy classes to avoid NameError
    class MinHash:
        def __init__(self, **kwargs):
            pass

        def update(self, data):
            pass

    class MinHashLSH:
        def __init__(self, **kwargs):
            pass

        def insert(self, key, minhash):
            pass

        def query(self, minhash):
            return []


class AdvancedDeduplicator:
    def __init__(
        self,
        threshold=0.8,
        num_perm=128,
        min_output_tokens=10,
        max_output_instruction_ratio=10.0,
    ):
        self.threshold = threshold
        self.num_perm = num_perm
        self.min_output_tokens = min_output_tokens
        self.max_output_instruction_ratio = max_output_instruction_ratio

        # Initialize MinHash LSH if available
        if MINHASH_AVAILABLE:
            self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        else:
            self.lsh = None

        # Quality filters
        self.banned_phrases = [
            "As an AI language model",
            "I'm an AI",
            "I am an AI",
            "As an artificial intelligence",
            "I'm sorry, I can't",
            "I cannot provide",
            "I'm not able to",
            "I don't have the ability",
            "I'm just an AI",
            "As a language model",
        ]

        # Leakage detection patterns
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.phone_pattern = re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
        )
        self.ssn_pattern = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")

        # Common names pattern (simplified)
        self.name_patterns = [
            re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),  # First Last
            re.compile(r"\bMr\.|Mrs\.|Ms\.|Dr\."),  # Titles
        ]

        # Location patterns (simplified)
        self.location_patterns = [
            re.compile(
                r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)\b"
            ),
            re.compile(r"\b[A-Z][a-z]+,\s*[A-Z]{2}\s+\d{5}\b"),  # City, ST ZIP
        ]

        # Statistics
        self.stats = {
            "total_processed": 0,
            "exact_duplicates": 0,
            "near_duplicates": 0,
            "quality_filtered": 0,
            "leakage_detected": 0,
            "safety_issues": 0,
            "final_count": 0,
            "role_stats": defaultdict(dict),
        }

    def count_tokens(self, text: str) -> int:
        """Simple token counting"""
        return len(text.split())

    def get_minhash(self, text: str) -> MinHash:
        """Generate MinHash signature for text"""
        if not MINHASH_AVAILABLE:
            return None

        # Tokenize and create shingles
        tokens = text.lower().split()
        shingles = []

        # Create 3-grams
        for i in range(len(tokens) - 2):
            shingle = " ".join(tokens[i : i + 3])
            shingles.append(shingle)

        # Create MinHash
        minhash = MinHash(num_perm=self.num_perm)
        for shingle in shingles:
            minhash.update(shingle.encode("utf-8"))

        return minhash

    def exact_hash(self, instruction: str, output: str) -> str:
        """Generate exact hash for instruction + output"""
        combined = instruction.strip() + "|||" + output.strip()
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def check_quality_filters(self, example: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Apply quality filters"""
        issues = []

        instruction = example.get("instruction", "")
        output = example.get("output", "")

        # Token count checks
        output_tokens = self.count_tokens(output)
        instruction_tokens = self.count_tokens(instruction)

        if output_tokens < self.min_output_tokens:
            issues.append(f"output_too_short: {output_tokens} tokens")

        if instruction_tokens > 0:
            ratio = output_tokens / instruction_tokens
            if ratio > self.max_output_instruction_ratio:
                issues.append(f"ratio_too_high: {ratio:.2f}")

        # Banned phrases
        for phrase in self.banned_phrases:
            if phrase.lower() in output.lower():
                issues.append(f"banned_phrase: {phrase}")

        return len(issues) == 0, issues

    def check_leakage(self, text: str) -> Tuple[bool, List[str]]:
        """Check for personal information leakage"""
        issues = []

        # Email addresses
        if self.email_pattern.search(text):
            issues.append("email_detected")

        # Phone numbers
        if self.phone_pattern.search(text):
            issues.append("phone_detected")

        # SSN patterns
        if self.ssn_pattern.search(text):
            issues.append("ssn_detected")

        # Names (simplified check)
        for pattern in self.name_patterns:
            if pattern.search(text):
                issues.append("name_pattern_detected")
                break

        # Addresses (simplified check)
        for pattern in self.location_patterns:
            if pattern.search(text):
                issues.append("address_pattern_detected")
                break

        return len(issues) == 0, issues

    def check_large_tutor_excess(
        self, example: Dict[str, Any], role_medians: Dict[str, float]
    ) -> bool:
        """Check if response is excessively large for the role"""
        role = example.get("meta", {}).get("role", "unknown")
        output = example.get("output", "")
        output_tokens = self.count_tokens(output)

        if role in role_medians:
            median = role_medians[role]
            if median > 0 and output_tokens > 3 * median:
                return True

        return False

    def deduplicate_dataset(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Main deduplication and quality control pipeline"""
        print(f"Processing: {input_file}")

        # First pass: collect all examples and calculate role medians
        examples = []
        role_tokens = defaultdict(list)

        with open(input_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    examples.append(example)

                    role = example.get("meta", {}).get("role", "unknown")
                    output_tokens = self.count_tokens(example.get("output", ""))
                    role_tokens[role].append(output_tokens)

                except json.JSONDecodeError:
                    continue

        # Calculate role medians
        role_medians = {}
        for role, tokens in role_tokens.items():
            if tokens:
                role_medians[role] = statistics.median(tokens)

        # Second pass: deduplication and filtering
        exact_hashes = set()
        minhash_to_id = {}
        kept_examples = []

        for i, example in enumerate(examples):
            self.stats["total_processed"] += 1

            instruction = example.get("instruction", "")
            output = example.get("output", "")
            role = example.get("meta", {}).get("role", "unknown")

            # Exact deduplication
            exact_hash = self.exact_hash(instruction, output)
            if exact_hash in exact_hashes:
                self.stats["exact_duplicates"] += 1
                continue
            exact_hashes.add(exact_hash)

            # Near deduplication (if MinHash available)
            skip_near_dup = False
            if MINHASH_AVAILABLE and self.lsh is not None:
                combined_text = instruction + " " + output
                minhash = self.get_minhash(combined_text)

                # Check for near duplicates
                similar_ids = self.lsh.query(minhash)
                if similar_ids:
                    self.stats["near_duplicates"] += 1
                    skip_near_dup = True
                else:
                    # Add to LSH index
                    self.lsh.insert(f"example_{i}", minhash)

            if skip_near_dup:
                continue

            # Quality filters
            quality_ok, quality_issues = self.check_quality_filters(example)
            if not quality_ok:
                self.stats["quality_filtered"] += 1
                continue

            # Leakage detection
            combined_text = instruction + " " + output
            leakage_ok, leakage_issues = self.check_leakage(combined_text)
            if not leakage_ok:
                self.stats["leakage_detected"] += 1
                # For now, just flag but don't remove
                example["meta"]["leakage_flags"] = leakage_issues

            # Large tutor excess check
            if self.check_large_tutor_excess(example, role_medians):
                example["meta"]["large_response_flag"] = True

            # Update role stats
            if role not in self.stats["role_stats"]:
                self.stats["role_stats"][role] = {
                    "count": 0,
                    "avg_tokens": 0,
                    "total_tokens": 0,
                }

            tokens = self.count_tokens(instruction) + self.count_tokens(output)
            self.stats["role_stats"][role]["count"] += 1
            self.stats["role_stats"][role]["total_tokens"] += tokens

            kept_examples.append(example)

        # Calculate final role averages
        for role, stats in self.stats["role_stats"].items():
            if stats["count"] > 0:
                stats["avg_tokens"] = stats["total_tokens"] / stats["count"]

        self.stats["final_count"] = len(kept_examples)

        # Save deduplicated dataset
        with open(output_file, "w", encoding="utf-8") as f:
            for example in kept_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        print(f"Deduplicated dataset saved to: {output_file}")
        return self.stats

    def generate_report(self) -> str:
        """Generate deduplication report"""
        lines = []
        lines.append("=" * 60)
        lines.append("ADVANCED DEDUPLICATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Summary
        total = self.stats["total_processed"]
        final = self.stats["final_count"]

        lines.append("SUMMARY:")
        lines.append(f"  Total processed: {total:,}")
        lines.append(f"  Final count: {final:,}")
        lines.append(f"  Reduction: {total - final:,} ({(total-final)/total*100:.1f}%)")
        lines.append("")

        lines.append("FILTERING BREAKDOWN:")
        lines.append(f"  Exact duplicates: {self.stats['exact_duplicates']:,}")
        if MINHASH_AVAILABLE:
            lines.append(f"  Near duplicates: {self.stats['near_duplicates']:,}")
        lines.append(f"  Quality filtered: {self.stats['quality_filtered']:,}")
        lines.append(f"  Leakage detected: {self.stats['leakage_detected']:,}")
        lines.append("")

        # Role distribution
        lines.append("FINAL ROLE DISTRIBUTION:")
        for role, stats in sorted(self.stats["role_stats"].items()):
            percentage = stats["count"] / final * 100 if final > 0 else 0
            lines.append(
                f"  {role}: {stats['count']:,} ({percentage:.1f}%) - avg {stats['avg_tokens']:.1f} tokens"
            )

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python advanced_dedup.py <input_file> <output_file> [threshold]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    deduplicator = AdvancedDeduplicator(threshold=threshold)
    stats = deduplicator.deduplicate_dataset(input_file, output_file)

    # Generate and save report
    report = deduplicator.generate_report()
    print("\n" + report)

    # Save detailed stats
    stats_file = output_file.replace(".jsonl", ".dedup_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed stats saved to: {stats_file}")


if __name__ == "__main__":
    main()
