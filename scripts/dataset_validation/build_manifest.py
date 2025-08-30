#!/usr/bin/env python3
"""
Dataset Manifest Generation
Creates comprehensive manifest with counts, hashes, and metadata
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import statistics

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from dataset_validation.separator_specs import SeparatorSpec, RoleType

class DatasetManifestBuilder:
    def __init__(self):
        self.manifest = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "separator_spec_version": SeparatorSpec.SPEC_VERSION,
                "schema_version": "alpaca-1.0"
            },
            "dataset": {},
            "roles": {},
            "quality_metrics": {},
            "separators": {},
            "checksums": {}
        }
    
    def count_tokens(self, text: str) -> int:
        """Simple token counting"""
        return len(text.split())
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def calculate_content_hash(self, instruction: str, output: str) -> str:
        """Calculate hash of instruction+output content"""
        content = instruction + output
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def analyze_dataset(self, file_path: str) -> Dict[str, Any]:
        """Analyze dataset and build manifest"""
        print(f"Analyzing dataset: {file_path}")
        
        # File-level information
        file_path_obj = Path(file_path)
        self.manifest["dataset"] = {
            "file_path": str(file_path_obj.absolute()),
            "file_name": file_path_obj.name,
            "file_size_bytes": file_path_obj.stat().st_size,
            "sha256": self.calculate_file_hash(file_path)
        }
        
        # Initialize role tracking
        role_stats = {}
        separator_usage = {}
        content_hashes = set()
        all_examples = []
        
        # Process each example
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    all_examples.append(example)
                    
                    # Extract basic info
                    role = example.get("meta", {}).get("role", "unknown")
                    instruction = example.get("instruction", "")
                    output = example.get("output", "")
                    separators_used = example.get("meta", {}).get("separators_used", [])
                    
                    # Count tokens
                    instruction_tokens = self.count_tokens(instruction)
                    output_tokens = self.count_tokens(output)
                    total_tokens = instruction_tokens + output_tokens
                    
                    # Track role statistics
                    if role not in role_stats:
                        role_stats[role] = {
                            "count": 0,
                            "instruction_tokens": [],
                            "output_tokens": [],
                            "total_tokens": [],
                            "separators": set()
                        }
                    
                    role_stats[role]["count"] += 1
                    role_stats[role]["instruction_tokens"].append(instruction_tokens)
                    role_stats[role]["output_tokens"].append(output_tokens)
                    role_stats[role]["total_tokens"].append(total_tokens)
                    role_stats[role]["separators"].update(separators_used)
                    
                    # Track separator usage
                    for sep in separators_used:
                        separator_usage[sep] = separator_usage.get(sep, 0) + 1
                    
                    # Track content hashes for deduplication analysis
                    content_hash = self.calculate_content_hash(instruction, output)
                    content_hashes.add(content_hash)
                
                except json.JSONDecodeError as e:
                    print(f"JSON error on line {line_num}: {e}")
                    continue
        
        # Calculate aggregated statistics
        total_examples = len(all_examples)
        unique_content = len(content_hashes)
        
        # Role statistics with averages
        for role, stats in role_stats.items():
            # Convert sets to lists for JSON serialization
            stats["separators"] = list(stats["separators"])
            
            # Calculate averages
            for metric in ["instruction_tokens", "output_tokens", "total_tokens"]:
                values = stats[metric]
                if values:
                    stats[f"avg_{metric}"] = statistics.mean(values)
                    stats[f"median_{metric}"] = statistics.median(values)
                    stats[f"min_{metric}"] = min(values)
                    stats[f"max_{metric}"] = max(values)
                    stats[f"std_{metric}"] = statistics.stdev(values) if len(values) > 1 else 0
                # Keep raw values for now, remove them later if needed
        
        # Update manifest
        self.manifest["dataset"]["total_examples"] = total_examples
        self.manifest["dataset"]["unique_content_hashes"] = unique_content
        self.manifest["dataset"]["duplication_rate"] = (total_examples - unique_content) / total_examples if total_examples > 0 else 0
        
        self.manifest["roles"] = role_stats
        
        self.manifest["separators"] = {
            "usage_counts": separator_usage,
            "total_unique_separators": len(separator_usage),
            "expected_separators": {
                role.value: SeparatorSpec.get_separators(role.value) 
                for role in [RoleType.FAMILY_TUTOR, 
                           RoleType.PHILOSOPHICAL_GUIDE,
                           RoleType.GENERAL_ASSISTANT,
                           RoleType.EDUCATIONAL_EXPERT]
            }
        }
        
        # Quality metrics
        all_instruction_tokens = []
        all_output_tokens = []
        all_total_tokens = []
        
        for stats in role_stats.values():
            all_instruction_tokens.extend(stats["instruction_tokens"])
            all_output_tokens.extend(stats["output_tokens"])
            all_total_tokens.extend(stats["total_tokens"])
        
        self.manifest["quality_metrics"] = {
            "overall_avg_instruction_tokens": statistics.mean(all_instruction_tokens) if all_instruction_tokens else 0,
            "overall_avg_output_tokens": statistics.mean(all_output_tokens) if all_output_tokens else 0,
            "overall_avg_total_tokens": statistics.mean(all_total_tokens) if all_total_tokens else 0,
            "overall_median_total_tokens": statistics.median(all_total_tokens) if all_total_tokens else 0,
            "token_distribution": {
                "p25": statistics.quantiles(all_total_tokens, n=4)[0] if all_total_tokens else 0,
                "p50": statistics.median(all_total_tokens) if all_total_tokens else 0,
                "p75": statistics.quantiles(all_total_tokens, n=4)[2] if all_total_tokens else 0,
                "p90": statistics.quantiles(all_total_tokens, n=10)[8] if all_total_tokens else 0,
                "p95": statistics.quantiles(all_total_tokens, n=20)[18] if all_total_tokens else 0
            }
        }
        
        return self.manifest
    
    def save_manifest(self, output_path: str):
        """Save manifest to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        
        print(f"Manifest saved to: {output_path}")
    
    def generate_summary_table(self) -> str:
        """Generate human-readable summary table"""
        lines = []
        lines.append("=" * 80)
        lines.append("DATASET MANIFEST SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.manifest['metadata']['created_at']}")
        lines.append(f"File: {self.manifest['dataset']['file_name']}")
        lines.append(f"SHA256: {self.manifest['dataset']['sha256'][:16]}...")
        lines.append("")
        
        # Dataset overview
        dataset = self.manifest["dataset"]
        lines.append("DATASET OVERVIEW:")
        lines.append(f"  Total examples: {dataset['total_examples']:,}")
        lines.append(f"  Unique content: {dataset['unique_content_hashes']:,}")
        lines.append(f"  Duplication rate: {dataset['duplication_rate']:.3f}")
        lines.append(f"  File size: {dataset['file_size_bytes']:,} bytes")
        lines.append("")
        
        # Role distribution
        lines.append("ROLE DISTRIBUTION:")
        total_examples = dataset['total_examples']
        
        for role, stats in sorted(self.manifest["roles"].items()):
            count = stats["count"]
            percentage = count / total_examples * 100 if total_examples > 0 else 0
            avg_tokens = stats.get("avg_total_tokens", 0)
            
            lines.append(f"  {role}:")
            lines.append(f"    Count: {count:,} ({percentage:.1f}%)")
            lines.append(f"    Avg tokens: {avg_tokens:.1f}")
            lines.append(f"    Token range: {stats.get('min_total_tokens', 0)}-{stats.get('max_total_tokens', 0)}")
        lines.append("")
        
        # Quality metrics
        quality = self.manifest["quality_metrics"]
        lines.append("QUALITY METRICS:")
        lines.append(f"  Avg instruction tokens: {quality['overall_avg_instruction_tokens']:.1f}")
        lines.append(f"  Avg output tokens: {quality['overall_avg_output_tokens']:.1f}")
        lines.append(f"  Avg total tokens: {quality['overall_avg_total_tokens']:.1f}")
        lines.append("")
        
        lines.append("TOKEN DISTRIBUTION:")
        dist = quality["token_distribution"]
        lines.append(f"  P25: {dist['p25']:.0f}")
        lines.append(f"  P50: {dist['p50']:.0f}")
        lines.append(f"  P75: {dist['p75']:.0f}")
        lines.append(f"  P90: {dist['p90']:.0f}")
        lines.append(f"  P95: {dist['p95']:.0f}")
        lines.append("")
        
        # Separator coverage
        lines.append("SEPARATOR COVERAGE:")
        for sep, count in sorted(self.manifest["separators"]["usage_counts"].items()):
            lines.append(f"  {sep}: {count:,} uses")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print("Usage: python build_manifest.py <dataset_file>")
        sys.exit(1)
    
    dataset_file = sys.argv[1]
    
    if not Path(dataset_file).exists():
        print(f"Error: File not found: {dataset_file}")
        sys.exit(1)
    
    builder = DatasetManifestBuilder()
    manifest = builder.analyze_dataset(dataset_file)
    
    # Generate output paths
    base_name = Path(dataset_file).stem
    manifest_path = f"data/MANIFEST_NEXT_EPOCH_{base_name}.json"
    summary_path = f"data/SUMMARY_NEXT_EPOCH_{base_name}.txt"
    
    # Save manifest
    builder.save_manifest(manifest_path)
    
    # Generate and save summary
    summary = builder.generate_summary_table()
    print("\n" + summary)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\nSummary saved to: {summary_path}")

if __name__ == "__main__":
    main()
