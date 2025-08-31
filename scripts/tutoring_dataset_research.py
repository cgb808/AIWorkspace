#!/usr/bin/env python3
"""
Tutoring and Instructional Dataset Research
Focuses on finding high-quality tutoring, instruction, and pedagogical datasets
"""

import json
import time
from pathlib import Path

import requests


class TutoringDatasetResearcher:
    """Research and identify tutoring-focused datasets"""

    def __init__(self):
        self.huggingface_api = "https://huggingface.co/api/datasets"

        # Tutoring-specific search terms
        self.TUTORING_KEYWORDS = [
            "tutoring",
            "instruction",
            "teaching",
            "pedagogy",
            "educational",
            "step-by-step",
            "explanation",
            "reasoning",
            "walkthrough",
            "tutorial",
            "guided",
            "learning",
            "coaching",
            "mentoring",
            "socratic",
            "dialogue",
            "conversation",
            "q&a",
            "questioning",
        ]

        # Subject-specific tutoring keywords
        self.SUBJECT_TUTORING = {
            "mathematics": [
                "math tutoring",
                "mathematical reasoning",
                "step-by-step math",
                "math explanation",
                "problem solving",
                "mathematical dialogue",
                "tutoreval",
                "mathinstruct",
                "metamath",
                "math conversations",
            ],
            "english": [
                "reading comprehension",
                "writing instruction",
                "literature tutoring",
                "essay coaching",
                "grammar instruction",
                "writing feedback",
                "literary analysis",
                "reading tutoring",
                "composition instruction",
            ],
            "science": [
                "science tutoring",
                "physics instruction",
                "chemistry explanation",
                "biology teaching",
                "scientific reasoning",
                "lab instruction",
            ],
            "general": [
                "socratic dialogue",
                "tutoring conversations",
                "instructional dialogue",
                "teaching methodology",
                "educational conversation",
                "guided learning",
            ],
        }

    def search_tutoring_datasets(self, subject="all", limit=50):
        """Search for tutoring-specific datasets"""
        print(f"🔍 Searching for {subject} tutoring datasets...")

        tutoring_datasets = []

        # Combine keywords for search
        if subject == "all":
            search_terms = self.TUTORING_KEYWORDS
            for subj_terms in self.SUBJECT_TUTORING.values():
                search_terms.extend(subj_terms)
        else:
            search_terms = self.TUTORING_KEYWORDS + self.SUBJECT_TUTORING.get(
                subject, []
            )

        # Search each term
        for term in search_terms[:10]:  # Limit to avoid rate limiting
            try:
                url = f"{self.huggingface_api}?search={term}&limit=20"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    results = response.json()
                    for dataset in results:
                        dataset_info = {
                            "id": dataset.get("id", ""),
                            "description": dataset.get("description", ""),
                            "downloads": dataset.get("downloads", 0),
                            "likes": dataset.get("likes", 0),
                            "search_term": term,
                            "tags": dataset.get("tags", []),
                        }
                        tutoring_datasets.append(dataset_info)

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                print(f"   ⚠️  Error searching '{term}': {e}")

        # Remove duplicates and sort by relevance
        unique_datasets = {}
        for dataset in tutoring_datasets:
            dataset_id = dataset["id"]
            if dataset_id not in unique_datasets:
                unique_datasets[dataset_id] = dataset

        # Sort by tutoring relevance score
        scored_datasets = []
        for dataset in unique_datasets.values():
            score = self.calculate_tutoring_score(dataset)
            if score > 0:
                dataset["tutoring_score"] = score
                scored_datasets.append(dataset)

        scored_datasets.sort(key=lambda x: x["tutoring_score"], reverse=True)
        return scored_datasets[:limit]

    def calculate_tutoring_score(self, dataset):
        """Calculate relevance score for tutoring applications"""
        score = 0
        text_content = f"{dataset['description']} {' '.join(dataset['tags'])} {dataset['id']}".lower()

        # High-value tutoring indicators
        tutoring_indicators = {
            "tutoring": 5,
            "instruction": 4,
            "teaching": 4,
            "dialogue": 4,
            "conversation": 3,
            "step-by-step": 5,
            "explanation": 4,
            "reasoning": 4,
            "walkthrough": 3,
            "guided": 3,
            "socratic": 5,
            "mentoring": 3,
            "coaching": 3,
            "pedagogy": 4,
            "educational": 2,
            "q&a": 3,
            "questioning": 3,
            "tutorial": 3,
            "learning": 2,
        }

        # Subject-specific high-value terms
        subject_indicators = {
            "math": 2,
            "mathematical": 2,
            "problem solving": 3,
            "reading comprehension": 3,
            "writing instruction": 3,
            "literature": 2,
            "science": 2,
            "physics": 2,
        }

        # Calculate score
        for term, weight in tutoring_indicators.items():
            if term in text_content:
                score += weight

        for term, weight in subject_indicators.items():
            if term in text_content:
                score += weight

        # Bonus for popularity (but not primary factor)
        score += min(dataset.get("downloads", 0) / 1000, 3)
        score += min(dataset.get("likes", 0) / 10, 2)

        return score

    def analyze_top_tutoring_datasets(self, datasets):
        """Analyze the top tutoring datasets for detailed evaluation"""
        print("\n📊 TOP TUTORING DATASETS ANALYSIS")
        print("=" * 60)

        for i, dataset in enumerate(datasets[:10], 1):
            print(f"\n{i}. {dataset['id']}")
            print(f"   Score: {dataset['tutoring_score']:.1f}")
            print(f"   Downloads: {dataset['downloads']:,}")
            print(f"   Likes: {dataset['likes']}")
            print(f"   Description: {dataset['description'][:200]}...")
            print(f"   Tags: {', '.join(dataset['tags'][:5])}")
            print(f"   Found via: {dataset['search_term']}")

    def generate_tutoring_recommendations(self, datasets):
        """Generate specific recommendations for tutoring datasets"""
        recommendations = {
            "high_priority": [],
            "medium_priority": [],
            "specialized": {},
        }

        for dataset in datasets:
            score = dataset["tutoring_score"]
            dataset_id = dataset["id"]

            if score >= 8:
                recommendations["high_priority"].append(
                    {
                        "id": dataset_id,
                        "score": score,
                        "reason": "High tutoring relevance with instruction/dialogue focus",
                    }
                )
            elif score >= 5:
                recommendations["medium_priority"].append(
                    {
                        "id": dataset_id,
                        "score": score,
                        "reason": "Good tutoring potential with educational content",
                    }
                )

            # Categorize by subject
            text = f"{dataset['description']} {dataset['id']}".lower()
            if any(
                term in text for term in ["math", "mathematical", "algebra", "geometry"]
            ):
                if "mathematics" not in recommendations["specialized"]:
                    recommendations["specialized"]["mathematics"] = []
                recommendations["specialized"]["mathematics"].append(dataset_id)

            if any(
                term in text
                for term in ["reading", "writing", "literature", "english", "essay"]
            ):
                if "english" not in recommendations["specialized"]:
                    recommendations["specialized"]["english"] = []
                recommendations["specialized"]["english"].append(dataset_id)

        return recommendations


def main():
    """Main research execution"""
    researcher = TutoringDatasetResearcher()

    print("🎯 TUTORING DATASET RESEARCH")
    print("=" * 50)
    print("Searching for high-quality instructional and tutoring datasets...")

    # Search for tutoring datasets
    datasets = researcher.search_tutoring_datasets("all", limit=30)

    print(f"\n✅ Found {len(datasets)} relevant tutoring datasets")

    # Analyze top results
    researcher.analyze_top_tutoring_datasets(datasets)

    # Generate recommendations
    recommendations = researcher.generate_tutoring_recommendations(datasets)

    print("\n🎯 TUTORING DATASET RECOMMENDATIONS")
    print("=" * 50)

    print("\n🔥 HIGH PRIORITY (Score ≥8):")
    for rec in recommendations["high_priority"]:
        print(f"   📚 {rec['id']} (Score: {rec['score']:.1f})")
        print(f"      Reason: {rec['reason']}")

    print("\n📖 MEDIUM PRIORITY (Score ≥5):")
    for rec in recommendations["medium_priority"][:5]:
        print(f"   📚 {rec['id']} (Score: {rec['score']:.1f})")

    print("\n🎨 SPECIALIZED BY SUBJECT:")
    for subject, dataset_ids in recommendations["specialized"].items():
        print(f"   {subject.upper()}: {len(dataset_ids)} datasets")
        for dataset_id in dataset_ids[:3]:
            print(f"      - {dataset_id}")

    # Save results
    output_file = Path("data/tutoring_dataset_research.json")
    with open(output_file, "w") as f:
        json.dump(
            {
                "datasets": datasets,
                "recommendations": recommendations,
                "research_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
        )

    print(f"\n💾 Research results saved to: {output_file}")
    print("\n🎯 NEXT STEPS:")
    print("   1. Review high-priority tutoring datasets")
    print("   2. Download and evaluate instructional quality")
    print("   3. Integrate into calculative fine-tuning pipeline")
    print("   4. Replace general datasets with tutoring-specific ones")


if __name__ == "__main__":
    main()
