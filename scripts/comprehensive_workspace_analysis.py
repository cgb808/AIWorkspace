#!/usr/bin/env python3
"""
Comprehensive Workspace Analysis and Organization Script
Analyzes entire workspace for duplicates, relevance, age, empty files, and unused components.
Creates structure for Mistral 7B central control system.
"""

import os
import json
import hashlib
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import stat

class WorkspaceAnalyzer:
    def __init__(self, base_path: str = "/home/cgbowen/AIWorkspace"):
        self.base_path = Path(base_path)
        self.analysis_results = {
            "duplicates": {},
            "empty_files": [],
            "unused_files": [],
            "old_files": [],
            "relevance_scores": {},
            "structure_recommendations": {},
            "mistral_7b_requirements": {}
        }
        
        # File categories for analysis
        self.code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h'}
        self.config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}
        self.doc_extensions = {'.md', '.txt', '.rst', '.doc', '.docx'}
        self.data_extensions = {'.jsonl', '.csv', '.tsv', '.parquet', '.feather'}
        self.ignore_dirs = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 'vendor'}
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "ERROR_READING_FILE"
    
    def analyze_duplicates(self) -> Dict[str, List[str]]:
        """Find duplicate files by content hash."""
        print("🔍 Analyzing duplicate files...")
        hash_to_files = defaultdict(list)
        
        for file_path in self.get_all_files():
            if file_path.is_file():
                file_hash = self.calculate_file_hash(file_path)
                hash_to_files[file_hash].append(str(file_path))
        
        # Only keep hashes with duplicates
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        self.analysis_results["duplicates"] = duplicates
        
        print(f"   Found {len(duplicates)} groups of duplicate files")
        return duplicates
    
    def find_empty_files(self) -> List[str]:
        """Find all empty files."""
        print("📭 Finding empty files...")
        empty_files = []
        
        for file_path in self.get_all_files():
            if file_path.is_file() and file_path.stat().st_size == 0:
                empty_files.append(str(file_path))
        
        self.analysis_results["empty_files"] = empty_files
        print(f"   Found {len(empty_files)} empty files")
        return empty_files
    
    def analyze_file_age(self, days_threshold: int = 30) -> List[str]:
        """Find files older than threshold."""
        print(f"📅 Finding files older than {days_threshold} days...")
        old_files = []
        current_time = time.time()
        threshold_seconds = days_threshold * 24 * 60 * 60
        
        for file_path in self.get_all_files():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > threshold_seconds:
                    old_files.append({
                        "path": str(file_path),
                        "age_days": int(file_age / (24 * 60 * 60)),
                        "last_modified": time.ctime(file_path.stat().st_mtime)
                    })
        
        self.analysis_results["old_files"] = old_files
        print(f"   Found {len(old_files)} files older than {days_threshold} days")
        return old_files
    
    def calculate_relevance_scores(self) -> Dict[str, float]:
        """Calculate relevance scores based on multiple factors."""
        print("🎯 Calculating relevance scores...")
        relevance_scores = {}
        
        for file_path in self.get_all_files():
            if file_path.is_file():
                score = self._calculate_file_relevance(file_path)
                relevance_scores[str(file_path)] = score
        
        self.analysis_results["relevance_scores"] = relevance_scores
        print(f"   Calculated relevance for {len(relevance_scores)} files")
        return relevance_scores
    
    def _calculate_file_relevance(self, file_path: Path) -> float:
        """Calculate relevance score for individual file."""
        score = 0.5  # Base score
        
        # File type relevance
        if file_path.suffix in self.code_extensions:
            score += 0.3
        elif file_path.suffix in self.config_extensions:
            score += 0.2
        elif file_path.suffix in self.data_extensions:
            score += 0.25
        
        # Path relevance
        path_str = str(file_path).lower()
        
        # High relevance keywords
        high_relevance = ['main', 'core', 'api', 'server', 'app', 'model', 'trainer', 'pipeline']
        if any(keyword in path_str for keyword in high_relevance):
            score += 0.2
        
        # Academic domain relevance
        academic_keywords = ['academic', 'domain', 'specialist', 'tutor', 'education']
        if any(keyword in path_str for keyword in academic_keywords):
            score += 0.3
        
        # Tool control relevance
        tool_keywords = ['tool', 'control', 'classification', 'mistral', 'phi3']
        if any(keyword in path_str for keyword in tool_keywords):
            score += 0.25
        
        # Reduce score for duplicates and old files
        if 'copy' in path_str or 'backup' in path_str or 'old' in path_str:
            score -= 0.3
        
        # File size consideration (very large or very small files)
        try:
            size = file_path.stat().st_size
            if size == 0:
                score -= 0.4
            elif size > 100_000_000:  # >100MB
                score -= 0.1
        except:
            pass
        
        return max(0.0, min(1.0, score))
    
    def get_all_files(self):
        """Generator for all files, excluding ignored directories."""
        for root, dirs, files in os.walk(self.base_path):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                yield Path(root) / file
    
    def analyze_mistral_7b_requirements(self) -> Dict[str, Any]:
        """Analyze requirements for Mistral 7B central control system."""
        print("🧠 Analyzing Mistral 7B central control requirements...")
        
        requirements = {
            "central_control": {
                "model": "mistral-7b-instruct",
                "purpose": "Central orchestration and routing",
                "download_required": True,
                "config_files": []
            },
            "data_analyzer": {
                "purpose": "Data analysis and insights",
                "integration_points": ["academic_domains", "tool_control"],
                "required_models": ["data analysis specialist"]
            },
            "router_controller": {
                "purpose": "Route requests to appropriate specialists",
                "integration": "tiny_tool_controller + mistral_coordination",
                "latency_target": "<150ms"
            },
            "tool_usage_director": {
                "purpose": "Coordinate tool usage across domains",
                "tools_managed": ["calculator", "graphing", "lab_guide", "writing_assistant"],
                "coordination_strategy": "centralized_dispatch"
            },
            "required_configs": [
                "mistral_7b_config.json",
                "central_router_config.json", 
                "tool_director_config.json",
                "data_analyzer_config.json"
            ]
        }
        
        self.analysis_results["mistral_7b_requirements"] = requirements
        return requirements
    
    def create_recommended_structure(self) -> Dict[str, Any]:
        """Create recommended folder structure."""
        print("📁 Creating recommended folder structure...")
        
        structure = {
            "models/": {
                "central_control/": {
                    "mistral_7b/": "Central orchestration model",
                    "router_controller/": "Request routing model", 
                    "data_analyzer/": "Data analysis specialist",
                    "tool_director/": "Tool usage coordination"
                },
                "specialists/": {
                    "tiny_tool_controller/": "Fast classification",
                    "phi3_mathematics_tutor/": "Math specialist",
                    "phi3_science_tutor/": "Science specialist",
                    "phi3_english_tutor/": "English specialist",
                    "phi3_history_tutor/": "History specialist", 
                    "phi3_art_tutor/": "Art specialist",
                    "phi3_language_tutor/": "Language specialist"
                }
            },
            "infrastructure/": {
                "configs/": "Configuration files",
                "docker/": "Container definitions",
                "monitoring/": "Observability setup"
            },
            "fine_tuning/": {
                "datasets/": {
                    "academic_domains/": "Domain-specific training data",
                    "tool_control/": "Tool classification data",
                    "central_control/": "Mistral 7B training data"
                },
                "training/": {
                    "scripts/": "Training automation",
                    "configs/": "Training configurations", 
                    "logs/": "Training logs"
                },
                "tooling/": {
                    "coordination/": "Multi-model coordination",
                    "rag/": "RAG integration",
                    "audio/": "Audio processing",
                    "visual/": "Visual processing"
                }
            },
            "app/": {
                "central_control/": "Mistral 7B orchestration",
                "audio/": "Audio pipeline",
                "core/": "Core functionality",
                "api/": "API endpoints"
            },
            "archive/": "Deprecated/unused files",
            "docs/": "Documentation",
            "scripts/": "Utility scripts",
            "tests/": "Test suites"
        }
        
        self.analysis_results["structure_recommendations"] = structure
        return structure
    
    def generate_cleanup_recommendations(self) -> Dict[str, List[str]]:
        """Generate specific cleanup recommendations."""
        print("🧹 Generating cleanup recommendations...")
        
        recommendations = {
            "delete_empty": [],
            "archive_duplicates": [],
            "remove_unused": [],
            "consolidate_configs": [],
            "rename_for_clarity": []
        }
        
        # Empty files to delete
        recommendations["delete_empty"] = self.analysis_results.get("empty_files", [])
        
        # Duplicates to archive (keep one, archive others)
        for file_hash, duplicate_files in self.analysis_results.get("duplicates", {}).items():
            if len(duplicate_files) > 1:
                # Keep the one with highest relevance score
                scores = [(f, self.analysis_results["relevance_scores"].get(f, 0)) for f in duplicate_files]
                scores.sort(key=lambda x: x[1], reverse=True)
                recommendations["archive_duplicates"].extend([f[0] for f in scores[1:]])
        
        # Low relevance files to remove/archive
        for file_path, score in self.analysis_results.get("relevance_scores", {}).items():
            if score < 0.3:
                recommendations["remove_unused"].append(file_path)
        
        return recommendations
    
    def create_mistral_7b_structure(self):
        """Create the folder structure for Mistral 7B central control."""
        print("🏗️ Creating Mistral 7B central control structure...")
        
        structure_paths = [
            "models/central_control/mistral_7b",
            "models/central_control/router_controller", 
            "models/central_control/data_analyzer",
            "models/central_control/tool_director",
            "app/central_control",
            "fine_tuning/datasets/central_control",
            "infrastructure/configs/central_control",
            "scripts/central_control"
        ]
        
        created_dirs = []
        for path in structure_paths:
            full_path = self.base_path / path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
            except Exception as e:
                print(f"   ❌ Failed to create {path}: {e}")
        
        print(f"   ✅ Created {len(created_dirs)} directories")
        return created_dirs
    
    def save_analysis_report(self):
        """Save comprehensive analysis report."""
        report_file = self.base_path / "workspace_analysis_report.json"
        
        # Add summary statistics
        self.analysis_results["summary"] = {
            "total_files_analyzed": len(self.analysis_results.get("relevance_scores", {})),
            "duplicate_groups": len(self.analysis_results.get("duplicates", {})),
            "empty_files_count": len(self.analysis_results.get("empty_files", [])),
            "old_files_count": len(self.analysis_results.get("old_files", [])),
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Analysis report saved to: {report_file}")
        return report_file
    
    def run_full_analysis(self):
        """Run complete workspace analysis."""
        print("🚀 Starting comprehensive workspace analysis...")
        print("=" * 60)
        
        # Run all analysis steps
        self.analyze_duplicates()
        self.find_empty_files()
        self.analyze_file_age()
        self.calculate_relevance_scores()
        self.analyze_mistral_7b_requirements()
        self.create_recommended_structure()
        
        # Generate recommendations
        cleanup_recs = self.generate_cleanup_recommendations()
        self.analysis_results["cleanup_recommendations"] = cleanup_recs
        
        # Create Mistral 7B structure
        self.create_mistral_7b_structure()
        
        # Save comprehensive report
        report_file = self.save_analysis_report()
        
        # Print summary
        self.print_analysis_summary()
        
        return self.analysis_results
    
    def print_analysis_summary(self):
        """Print analysis summary."""
        print("\n📊 Workspace Analysis Summary")
        print("=" * 40)
        
        summary = self.analysis_results.get("summary", {})
        print(f"📁 Total files analyzed: {summary.get('total_files_analyzed', 0):,}")
        print(f"👥 Duplicate file groups: {summary.get('duplicate_groups', 0)}")
        print(f"📭 Empty files: {summary.get('empty_files_count', 0)}")
        print(f"📅 Old files (>30 days): {summary.get('old_files_count', 0)}")
        
        # Show most relevant files
        print(f"\n🎯 Top 10 Most Relevant Files:")
        relevance_scores = self.analysis_results.get("relevance_scores", {})
        top_files = sorted(relevance_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (file_path, score) in enumerate(top_files, 1):
            short_path = file_path.replace(str(self.base_path), ".")
            print(f"   {i:2d}. {score:.2f} - {short_path}")
        
        # Show cleanup recommendations
        cleanup = self.analysis_results.get("cleanup_recommendations", {})
        print(f"\n🧹 Cleanup Recommendations:")
        print(f"   📭 Delete empty files: {len(cleanup.get('delete_empty', []))}")
        print(f"   📦 Archive duplicates: {len(cleanup.get('archive_duplicates', []))}")
        print(f"   🗑️  Remove unused: {len(cleanup.get('remove_unused', []))}")
        
        # Show Mistral 7B requirements
        print(f"\n🧠 Mistral 7B Central Control Setup:")
        mistral_req = self.analysis_results.get("mistral_7b_requirements", {})
        print(f"   🎯 Central Control: {mistral_req.get('central_control', {}).get('model', 'Not configured')}")
        print(f"   📊 Data Analyzer: Required")
        print(f"   🔀 Router Controller: Required") 
        print(f"   🔧 Tool Director: Required")

def main():
    print("🔍 Comprehensive Workspace Analysis & Mistral 7B Setup")
    print("=" * 60)
    
    analyzer = WorkspaceAnalyzer()
    results = analyzer.run_full_analysis()
    
    print(f"\n🎉 Analysis Complete!")
    print(f"📋 Detailed report saved to: workspace_analysis_report.json")
    print(f"🏗️ Mistral 7B central control structure created")
    print(f"🚀 Ready for DevOps.md and TODO.md updates!")

if __name__ == "__main__":
    main()
