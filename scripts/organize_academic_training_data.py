#!/usr/bin/env python3
"""
Organize existing training data into academic domains and generate domain-specific datasets.
"""

import json
import random
import shutil
from pathlib import Path
from typing import Dict, List

# Academic domain configuration
ACADEMIC_DOMAINS = {
    "mathematics": {
        "subdomains": ["algebra", "geometry", "trigonometry", "calculus"],
        "keywords": [
            "math",
            "algebra",
            "geometry",
            "trigonometry",
            "calculus",
            "equation",
            "formula",
            "solve",
            "calculate",
            "arithmetic",
            "number",
            "fraction",
            "decimal",
            "polynomial",
            "derivative",
            "integral",
        ],
        "specialist": "phi3_mathematics_tutor",
        "voice": "jarvis",
        "tools": ["calculator", "graphing", "latex_renderer", "equation_solver"],
    },
    "english": {
        "subdomains": [
            "creative_writing",
            "reading_comprehension",
            "american_literature",
        ],
        "keywords": [
            "english",
            "writing",
            "literature",
            "reading",
            "comprehension",
            "essay",
            "story",
            "poem",
            "grammar",
            "vocabulary",
            "author",
            "character",
            "plot",
            "theme",
        ],
        "specialist": "phi3_english_tutor",
        "voice": "alan",
        "tools": ["text_analyzer", "writing_assistant", "literature_database"],
    },
    "science": {
        "subdomains": [
            "environmental_science",
            "physics",
            "astronomy",
            "forensic_science",
            "oceanography",
            "botany",
            "earth_science",
            "geology",
            "physical_science",
            "zoology",
            "anatomy",
            "computer_science",
            "food_science",
        ],
        "keywords": [
            "science",
            "physics",
            "chemistry",
            "biology",
            "astronomy",
            "geology",
            "environmental",
            "anatomy",
            "zoology",
            "botany",
            "experiment",
            "lab",
            "hypothesis",
            "data",
            "observation",
        ],
        "specialist": "phi3_science_tutor",
        "voice": "jarvis",
        "tools": [
            "data_analyzer",
            "simulation_runner",
            "lab_guide",
            "formula_renderer",
        ],
    },
    "history": {
        "subdomains": [
            "civics",
            "us_history",
            "world_history",
            "economics",
            "regional_history/west_virginia",
        ],
        "keywords": [
            "history",
            "historical",
            "civilization",
            "war",
            "politics",
            "government",
            "economy",
            "culture",
            "society",
            "timeline",
            "era",
            "period",
            "revolution",
            "democracy",
        ],
        "specialist": "phi3_history_tutor",
        "voice": "jarvis",
        "tools": ["timeline_creator", "map_generator", "primary_source_analyzer"],
    },
    "art": {
        "subdomains": [
            "foundational",
            "abstract",
            "history_of_art",
            "performing",
            "music_theory",
            "visual_arts",
        ],
        "keywords": [
            "art",
            "music",
            "painting",
            "drawing",
            "sculpture",
            "performance",
            "theater",
            "dance",
            "composition",
            "rhythm",
            "melody",
            "color",
            "design",
            "aesthetic",
        ],
        "specialist": "phi3_art_tutor",
        "voice": "amy",
        "tools": [
            "image_analyzer",
            "color_palette",
            "music_notation",
            "timeline_creator",
        ],
    },
    "foreign_language": {
        "subdomains": ["spanish", "french", "italian"],
        "keywords": [
            "spanish",
            "french",
            "italian",
            "language",
            "grammar",
            "vocabulary",
            "pronunciation",
            "translation",
            "culture",
            "conversation",
            "verb",
            "noun",
            "adjective",
        ],
        "specialist": "phi3_language_tutor",
        "voice": "amy",
        "tools": [
            "translator",
            "pronunciation_guide",
            "grammar_checker",
            "culture_guide",
        ],
    },
}


class AcademicDataOrganizer:
    def __init__(self, base_path: str = "/home/cgbowen/AIWorkspace"):
        self.base_path = Path(base_path)
        self.datasets_path = self.base_path / "fine_tuning" / "datasets"
        self.academic_path = self.datasets_path / "academic_domains"
        self.processed_path = self.datasets_path / "processed"

    def analyze_existing_data(self) -> Dict[str, List[str]]:
        """Analyze existing training data and categorize by domain."""
        existing_files = {}

        # Find all JSONL files
        for jsonl_file in self.datasets_path.rglob("*.jsonl"):
            if "academic_domains" not in str(
                jsonl_file
            ):  # Skip already organized files
                existing_files[str(jsonl_file)] = self._categorize_file(jsonl_file)

        return existing_files

    def _categorize_file(self, file_path: Path) -> List[str]:
        """Categorize a file based on its content and name."""
        categories = []
        file_name = file_path.name.lower()

        # Check filename for domain keywords
        for domain, config in ACADEMIC_DOMAINS.items():
            for keyword in config["keywords"]:
                if keyword in file_name or keyword in str(file_path).lower():
                    categories.append(domain)
                    break

        # If math-related, definitely add mathematics
        if any(
            word in file_name for word in ["math", "gsm8k", "arithmetic", "algebra"]
        ):
            if "mathematics" not in categories:
                categories.append("mathematics")

        # If no categories found, try to infer from content (sample first few lines)
        if not categories:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    sample_lines = [f.readline() for _ in range(5)]
                    content = " ".join(sample_lines).lower()

                    for domain, config in ACADEMIC_DOMAINS.items():
                        for keyword in config["keywords"]:
                            if keyword in content:
                                categories.append(domain)
                                break
            except Exception as e:
                print(f"Warning: Could not analyze content of {file_path}: {e}")

        return categories if categories else ["general"]

    def organize_existing_data(self):
        """Organize existing training data into academic domains."""
        print("🔍 Analyzing existing training data...")

        existing_files = self.analyze_existing_data()

        for file_path, categories in existing_files.items():
            source_file = Path(file_path)
            print(f"\n📁 Processing: {source_file.name}")
            print(f"   Categories: {categories}")

            for category in categories:
                if category in ACADEMIC_DOMAINS:
                    # Copy to main domain folder
                    dest_dir = self.academic_path / category
                    dest_file = dest_dir / f"existing_{source_file.name}"

                    try:
                        shutil.copy2(source_file, dest_file)
                        print(f"   ✅ Copied to {category}/")
                    except Exception as e:
                        print(f"   ❌ Failed to copy to {category}/: {e}")

    def generate_domain_specific_training(self):
        """Generate domain-specific training examples for each academic domain."""
        print("\n🚀 Generating domain-specific training data...")

        for domain, config in ACADEMIC_DOMAINS.items():
            print(f"\n📚 Generating training for {domain}...")

            domain_dir = self.academic_path / domain
            training_file = domain_dir / "training_examples.jsonl"
            tool_file = domain_dir / "tool_integration.jsonl"
            socratic_file = domain_dir / "socratic_questioning.jsonl"
            assessment_file = domain_dir / "assessment_examples.jsonl"

            # Generate basic training examples
            training_examples = self._generate_domain_training(domain, config, 100)
            self._write_jsonl(training_file, training_examples)

            # Generate tool integration examples
            tool_examples = self._generate_tool_integration(domain, config, 50)
            self._write_jsonl(tool_file, tool_examples)

            # Generate Socratic questioning examples
            socratic_examples = self._generate_socratic_examples(domain, config, 75)
            self._write_jsonl(socratic_file, socratic_examples)

            # Generate assessment examples
            assessment_examples = self._generate_assessment_examples(domain, config, 25)
            self._write_jsonl(assessment_file, assessment_examples)

            print(f"   ✅ Generated {len(training_examples)} training examples")
            print(f"   ✅ Generated {len(tool_examples)} tool integration examples")
            print(f"   ✅ Generated {len(socratic_examples)} Socratic examples")
            print(f"   ✅ Generated {len(assessment_examples)} assessment examples")

    def _generate_domain_training(
        self, domain: str, config: Dict, count: int
    ) -> List[Dict]:
        """Generate basic training examples for a domain."""
        examples = []

        if domain == "mathematics":
            examples.extend(
                [
                    {
                        "instruction": "Solve the equation 2x + 5 = 15 and explain each step.",
                        "input": "",
                        "output": "Let me solve this step by step:\n\n1) Start with: 2x + 5 = 15\n2) Subtract 5 from both sides: 2x + 5 - 5 = 15 - 5\n3) Simplify: 2x = 10\n4) Divide both sides by 2: 2x ÷ 2 = 10 ÷ 2\n5) Solution: x = 5\n\nTo verify: 2(5) + 5 = 10 + 5 = 15 ✓",
                        "domain": domain,
                        "subdomain": "algebra",
                        "tools_used": ["calculator", "equation_solver"],
                    },
                    {
                        "instruction": "What is the area of a circle with radius 7 units?",
                        "input": "",
                        "output": "To find the area of a circle, I'll use the formula A = πr².\n\nGiven: radius (r) = 7 units\n\nCalculation:\nA = π × r²\nA = π × 7²\nA = π × 49\nA = 49π square units\n\nAs a decimal approximation: A ≈ 49 × 3.14159 ≈ 153.94 square units",
                        "domain": domain,
                        "subdomain": "geometry",
                        "tools_used": ["calculator", "formula_renderer"],
                    },
                ]
            )

        elif domain == "science":
            examples.extend(
                [
                    {
                        "instruction": "Explain the process of photosynthesis and its importance.",
                        "input": "",
                        "output": "Photosynthesis is the process by which plants convert light energy into chemical energy:\n\n**Process:**\n6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂\n\n**Steps:**\n1. Light reactions: Chlorophyll absorbs light\n2. Dark reactions: CO₂ is converted to glucose\n\n**Importance:**\n- Produces oxygen for life\n- Creates food for the food chain\n- Removes CO₂ from atmosphere",
                        "domain": domain,
                        "subdomain": "botany",
                        "tools_used": ["formula_renderer", "lab_guide"],
                    }
                ]
            )

        elif domain == "english":
            examples.extend(
                [
                    {
                        "instruction": "Analyze the theme of courage in 'To Kill a Mockingbird'.",
                        "input": "",
                        "output": "Courage is a central theme in Harper Lee's 'To Kill a Mockingbird', manifested in several ways:\n\n**Moral Courage:**\n- Atticus defending Tom Robinson despite social pressure\n- Scout standing up to classmates about her father\n\n**Physical Courage:**\n- Jem and Scout facing the mad dog incident\n- Scout confronting the mob at the jail\n\n**Quiet Courage:**\n- Mrs. Dubose fighting her addiction\n- Boo Radley protecting the children\n\nLee shows that true courage isn't the absence of fear, but acting rightly despite it.",
                        "domain": domain,
                        "subdomain": "american_literature",
                        "tools_used": ["literature_database", "text_analyzer"],
                    }
                ]
            )

        # Fill remaining examples with generated content
        while len(examples) < count:
            examples.append(self._generate_generic_example(domain, config))

        return examples[:count]

    def _generate_tool_integration(
        self, domain: str, config: Dict, count: int
    ) -> List[Dict]:
        """Generate tool integration examples."""
        examples = []
        tools = config["tools"]

        for i in range(count):
            tool = random.choice(tools)
            example = {
                "instruction": f"Use the {tool} tool to help solve this {domain} problem.",
                "input": f"Student needs help with {domain} using {tool}",
                "output": f"I'll use the {tool} tool to assist you. Let me activate it and guide you through the solution step by step.",
                "domain": domain,
                "tool_call": tool,
                "specialist": config["specialist"],
            }
            examples.append(example)

        return examples

    def _generate_socratic_examples(
        self, domain: str, config: Dict, count: int
    ) -> List[Dict]:
        """Generate Socratic questioning examples."""
        examples = []

        for i in range(count):
            example = {
                "instruction": f"Guide a student through discovering a {domain} concept using Socratic questioning.",
                "input": f"Student is struggling with {domain} concept",
                "output": "Let me ask you some guiding questions to help you discover the answer yourself:\n\n1. What do you already know about this topic?\n2. Can you think of a similar problem you've solved before?\n3. What patterns do you notice?\n4. How might you test your hypothesis?",
                "domain": domain,
                "method": "socratic",
                "specialist": config["specialist"],
            }
            examples.append(example)

        return examples

    def _generate_assessment_examples(
        self, domain: str, config: Dict, count: int
    ) -> List[Dict]:
        """Generate assessment examples."""
        examples = []

        for i in range(count):
            example = {
                "instruction": f"Create an assessment question for {domain} understanding.",
                "input": f"Need to assess {domain} knowledge",
                "output": f"Here's an assessment question for {domain}:\n\nQuestion: [Generated assessment question]\nExpected answer: [Expected response]\nRubric: [Scoring criteria]",
                "domain": domain,
                "type": "assessment",
                "specialist": config["specialist"],
            }
            examples.append(example)

        return examples

    def _generate_generic_example(self, domain: str, config: Dict) -> Dict:
        """Generate a generic example for a domain."""
        return {
            "instruction": f"Help me understand this {domain} concept.",
            "input": f"Student needs help with {domain}",
            "output": f"I'll help you understand this {domain} concept step by step. Let me break it down for you clearly.",
            "domain": domain,
            "specialist": config["specialist"],
            "generated": True,
        }

    def _write_jsonl(self, file_path: Path, data: List[Dict]):
        """Write data to JSONL file."""
        with open(file_path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def create_training_manifest(self):
        """Create a manifest of all training data organized by domain."""
        manifest = {
            "academic_domains": {},
            "total_examples": 0,
            "generated_at": "2024-01-01",
        }

        for domain in ACADEMIC_DOMAINS.keys():
            domain_dir = self.academic_path / domain
            domain_info = {
                "specialist": ACADEMIC_DOMAINS[domain]["specialist"],
                "subdomains": ACADEMIC_DOMAINS[domain]["subdomains"],
                "training_files": [],
                "example_count": 0,
            }

            # Count examples in each file
            for jsonl_file in domain_dir.glob("*.jsonl"):
                try:
                    with open(jsonl_file, "r", encoding="utf-8") as f:
                        count = sum(1 for _ in f)
                    domain_info["training_files"].append(
                        {"file": jsonl_file.name, "examples": count}
                    )
                    domain_info["example_count"] += count
                except Exception as e:
                    print(f"Warning: Could not count examples in {jsonl_file}: {e}")

            manifest["academic_domains"][domain] = domain_info
            manifest["total_examples"] += domain_info["example_count"]

        # Write manifest
        manifest_file = self.academic_path / "training_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest


def main():
    print("🎓 Academic Training Data Organization")
    print("=" * 50)

    organizer = AcademicDataOrganizer()

    # Step 1: Organize existing data
    organizer.organize_existing_data()

    # Step 2: Generate domain-specific training
    organizer.generate_domain_specific_training()

    # Step 3: Create training manifest
    manifest = organizer.create_training_manifest()

    print("\n🎉 Academic Training Data Organization Complete!")
    print(f"📊 Total training examples: {manifest['total_examples']}")
    print(f"📚 Domains organized: {len(manifest['academic_domains'])}")

    for domain, info in manifest["academic_domains"].items():
        print(f"   • {domain}: {info['example_count']} examples")

    print("\n📝 Training manifest saved to: academic_domains/training_manifest.json")
    print("🚀 Ready for specialist model fine-tuning!")


if __name__ == "__main__":
    main()
