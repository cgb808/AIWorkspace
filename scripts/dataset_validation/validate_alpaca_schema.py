#!/usr/bin/env python3
"""
Alpaca Schema Validation
Validates dataset format, separators, and content quality
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import hashlib
import re
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from dataset_validation.separator_specs import SeparatorSpec, RoleType

class AlpacaSchemaValidator:
    def __init__(self):
        self.required_keys = {"instruction", "input", "output", "meta"}
        self.required_meta_keys = {"role", "system_prompt", "separators_used", "instructional_format"}
        
        # Quality filters
        self.min_output_tokens = 10
        self.max_output_instruction_ratio = 10.0
        self.banned_phrases = [
            "As an AI language model",
            "I'm an AI",
            "I am an AI",
            "As an artificial intelligence",
            "I'm sorry, I can't",
            "I cannot provide",
            "I'm not able to"
        ]
        
        # Stats tracking
        self.stats = {
            "total_examples": 0,
            "valid_examples": 0,
            "errors": [],
            "role_distribution": {},
            "length_stats": {},
            "separator_coverage": {},
            "quality_issues": []
        }
    
    def count_tokens(self, text: str) -> int:
        """Simple token counting (rough approximation)"""
        return len(text.split())
    
    def validate_example(self, example: Dict[str, Any], line_num: int) -> Tuple[bool, List[str]]:
        """Validate a single example"""
        errors = []
        
        # Check required keys
        missing_keys = self.required_keys - set(example.keys())
        if missing_keys:
            errors.append(f"Missing required keys: {missing_keys}")
        
        # Check meta structure
        if "meta" in example:
            meta = example["meta"]
            missing_meta = self.required_meta_keys - set(meta.keys())
            if missing_meta:
                errors.append(f"Missing meta keys: {missing_meta}")
            
            # Validate role
            role = meta.get("role")
            if role:
                try:
                    RoleType(role)
                except ValueError:
                    errors.append(f"Invalid role: {role}")
                
                # Check separators match role
                expected_separators = SeparatorSpec.get_separators(role)
                actual_separators = meta.get("separators_used", [])
                
                if set(expected_separators) != set(actual_separators):
                    errors.append(f"Separator mismatch for role {role}")
        
        # Validate instruction format
        instruction = example.get("instruction", "")
        output = example.get("output", "")
        
        if not instruction:
            errors.append("Empty instruction")
        
        if not output:
            errors.append("Empty output")
        
        # Check for stray brackets in content
        role = example.get("meta", {}).get("role", "")
        if role:
            # Check instruction separators
            segments = SeparatorSpec.extract_segments(instruction, role)
            
            # Check output for stray brackets
            output_clean, violations = SeparatorSpec.validate_no_stray_brackets(output)
            if not output_clean:
                errors.append(f"Stray separators in output: {violations}")
        
        # Quality checks
        output_tokens = self.count_tokens(output)
        instruction_tokens = self.count_tokens(instruction)
        
        if output_tokens < self.min_output_tokens:
            errors.append(f"Output too short: {output_tokens} tokens")
        
        if instruction_tokens > 0:
            ratio = output_tokens / instruction_tokens
            if ratio > self.max_output_instruction_ratio:
                errors.append(f"Output/instruction ratio too high: {ratio:.2f}")
        
        # Check for banned phrases
        for phrase in self.banned_phrases:
            if phrase.lower() in output.lower():
                errors.append(f"Banned phrase detected: {phrase}")
        
        return len(errors) == 0, errors
    
    def validate_dataset(self, file_path: str) -> Dict[str, Any]:
        """Validate entire dataset"""
        print(f"Validating dataset: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    self.stats["total_examples"] += 1
                    
                    is_valid, errors = self.validate_example(example, line_num)
                    
                    if is_valid:
                        self.stats["valid_examples"] += 1
                        self._update_stats(example)
                    else:
                        self.stats["errors"].append({
                            "line": line_num,
                            "errors": errors
                        })
                
                except json.JSONDecodeError as e:
                    self.stats["errors"].append({
                        "line": line_num,
                        "errors": [f"JSON decode error: {e}"]
                    })
        
        # Calculate final statistics
        self._calculate_final_stats()
        
        return self.stats
    
    def _update_stats(self, example: Dict[str, Any]):
        """Update running statistics"""
        role = example.get("meta", {}).get("role", "unknown")
        
        # Role distribution
        self.stats["role_distribution"][role] = self.stats["role_distribution"].get(role, 0) + 1
        
        # Length statistics
        instruction_tokens = self.count_tokens(example.get("instruction", ""))
        output_tokens = self.count_tokens(example.get("output", ""))
        
        if role not in self.stats["length_stats"]:
            self.stats["length_stats"][role] = {
                "instruction_tokens": [],
                "output_tokens": [],
                "total_tokens": []
            }
        
        self.stats["length_stats"][role]["instruction_tokens"].append(instruction_tokens)
        self.stats["length_stats"][role]["output_tokens"].append(output_tokens)
        self.stats["length_stats"][role]["total_tokens"].append(instruction_tokens + output_tokens)
        
        # Separator coverage
        separators_used = example.get("meta", {}).get("separators_used", [])
        for sep in separators_used:
            self.stats["separator_coverage"][sep] = self.stats["separator_coverage"].get(sep, 0) + 1
    
    def _calculate_final_stats(self):
        """Calculate final aggregated statistics"""
        for role, lengths in self.stats["length_stats"].items():
            # Create a copy of the keys to avoid dictionary modification during iteration
            metrics_to_process = list(lengths.keys())
            for metric in metrics_to_process:
                if not metric.endswith('_avg') and not metric.endswith('_min') and not metric.endswith('_max') and not metric.endswith('_median'):
                    values = lengths[metric]
                    if values:
                        lengths[f"{metric}_avg"] = sum(values) / len(values)
                        lengths[f"{metric}_min"] = min(values)
                        lengths[f"{metric}_max"] = max(values)
                        lengths[f"{metric}_median"] = sorted(values)[len(values) // 2]
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("=" * 60)
        report.append("ALPACA SCHEMA VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Summary
        total = self.stats["total_examples"]
        valid = self.stats["valid_examples"]
        error_count = len(self.stats["errors"])
        
        report.append("SUMMARY:")
        report.append(f"  Total examples: {total}")
        report.append(f"  Valid examples: {valid}")
        report.append(f"  Invalid examples: {error_count}")
        report.append(f"  Success rate: {valid/total*100:.1f}%" if total > 0 else "  Success rate: 0%")
        report.append("")
        
        # Role distribution
        if self.stats["role_distribution"]:
            report.append("ROLE DISTRIBUTION:")
            total_valid = sum(self.stats["role_distribution"].values())
            
            # Target ratios for comparison
            target_ratios = {
                "general_assistant": 55,
                "family_tutor": 15, 
                "educational_expert": 15,
                "philosophical_guide": 10,
                "other": 5
            }
            
            for role, count in sorted(self.stats["role_distribution"].items()):
                percentage = count / total_valid * 100
                target = target_ratios.get(role, 0)
                status = "✓" if abs(percentage - target) < 5 else "⚠"
                report.append(f"  {role}: {count} ({percentage:.1f}%) {status} [target: {target}%]")
            report.append("")
        
        # Length statistics
        if self.stats["length_stats"]:
            report.append("LENGTH STATISTICS:")
            for role, stats in self.stats["length_stats"].items():
                report.append(f"  {role}:")
                report.append(f"    Instruction tokens: avg={stats.get('instruction_tokens_avg', 0):.1f}, "
                            f"min={stats.get('instruction_tokens_min', 0)}, "
                            f"max={stats.get('instruction_tokens_max', 0)}")
                report.append(f"    Output tokens: avg={stats.get('output_tokens_avg', 0):.1f}, "
                            f"min={stats.get('output_tokens_min', 0)}, "
                            f"max={stats.get('output_tokens_max', 0)}")
            report.append("")
        
        # Separator coverage
        if self.stats["separator_coverage"]:
            report.append("SEPARATOR COVERAGE:")
            for sep, count in sorted(self.stats["separator_coverage"].items()):
                report.append(f"  {sep}: {count} uses")
            report.append("")
        
        # Errors (first 10)
        if self.stats["errors"]:
            report.append("VALIDATION ERRORS (first 10):")
            for error in self.stats["errors"][:10]:
                report.append(f"  Line {error['line']}: {', '.join(error['errors'])}")
            
            if len(self.stats["errors"]) > 10:
                report.append(f"  ... and {len(self.stats['errors']) - 10} more errors")
            report.append("")
        
        return "\n".join(report)

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_alpaca_schema.py <dataset_file>")
        sys.exit(1)
    
    dataset_file = sys.argv[1]
    
    if not Path(dataset_file).exists():
        print(f"Error: File not found: {dataset_file}")
        sys.exit(1)
    
    validator = AlpacaSchemaValidator()
    stats = validator.validate_dataset(dataset_file)
    
    # Generate and save report
    report = validator.generate_report()
    print(report)
    
    # Save detailed stats
    stats_file = dataset_file.replace('.jsonl', '.validation_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed validation stats saved to: {stats_file}")
    
    # Exit with error code if validation failed
    if stats["valid_examples"] < stats["total_examples"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
