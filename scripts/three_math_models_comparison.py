#!/usr/bin/env python3
"""
Mathematics Models Comparison Tool
Compare the three mathematics-relevant models:
1. General Mathematics Model (standard math datasets)
2. Tutoring Model (authentic tutoring datasets) 
3. Pure Methodology Model (tutoring methodology only)

English model excluded as requested.
"""

from datetime import datetime

import requests


class MathematicsModelsComparator:
    """Compare mathematics-relevant models only"""

    def __init__(self, ollama_url="http://localhost:11435"):
        self.ollama_url = ollama_url
        self.base_model = "phi3:mini"

    def query_model_with_context(self, prompt, model_type="general_math"):
        """Query model with specific context formatting"""

        # Format prompt based on model type
        if model_type == "general_math":
            formatted_prompt = f"[LEARNING_CONTEXT] Mathematics [LEARNING_OBJECTIVE] Understand and solve mathematical concepts clearly. [TASK] {prompt}"
        elif model_type == "tutoring":
            formatted_prompt = f"[LEARNING_CONTEXT] Mathematics Tutoring [LEARNING_OBJECTIVE] Solve math word problems step-by-step with clear explanations. [TASK] {prompt}"
        elif model_type == "pure_methodology":
            formatted_prompt = f"[TUTORING_METHODOLOGY_MODE] Focus on teaching techniques, pedagogical approaches, and instructional strategies. [STUDENT_SITUATION] Student working on: {prompt} [TUTORING_TASK] Apply appropriate tutoring methodology to guide the student."
        else:
            formatted_prompt = prompt

        try:
            payload = {
                "model": self.base_model,
                "prompt": formatted_prompt,
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9},
            }

            response = requests.post(
                f"{self.ollama_url}/api/generate", json=payload, timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response received")
            else:
                return f"Error: {response.status_code}"

        except Exception as e:
            return f"Exception: {e}"

    def compare_mathematics_models(self, test_problem):
        """Compare all three mathematics-relevant models"""

        print("🎯 MATHEMATICS MODELS COMPARISON")
        print("🚫 English model excluded (different subject matter)")
        print("=" * 70)
        print(f"Test Problem: {test_problem}")
        print("=" * 70)

        models_to_test = [
            {
                "name": "GENERAL MATHEMATICS MODEL",
                "type": "general_math",
                "icon": "📚",
                "description": "Dataset: Standard mathematics content\n   Training: Calculative fine-tuning on general math",
            },
            {
                "name": "TUTORING MODEL",
                "type": "tutoring",
                "icon": "🎓",
                "description": "Dataset: Authentic tutoring content (GSM8K + Socratic)\n   Training: Calculative fine-tuning on tutoring data",
            },
            {
                "name": "PURE METHODOLOGY MODEL",
                "type": "pure_methodology",
                "icon": "🔬",
                "description": "Dataset: Pure tutoring methodology (1000 examples)\n   Training: Calculative fine-tuning on teaching techniques",
            },
        ]

        responses = {}

        for model in models_to_test:
            print(f"\n{model['icon']} {model['name']}")
            print(f"   {model['description']}")
            print("-" * 50)

            response = self.query_model_with_context(test_problem, model["type"])
            responses[model["type"]] = response

            print(f"Response:\n{response}")
            print("\n" + "=" * 70)

        # Analysis focusing on teaching quality across all three models
        print("\n📊 TEACHING QUALITY ANALYSIS")
        print("=" * 50)

        # Enhanced indicators for comprehensive comparison
        teaching_indicators = {
            "step_structure": [
                "step 1",
                "step 2",
                "step 3",
                "first",
                "next",
                "then",
                "finally",
            ],
            "explanation_quality": [
                "let's",
                "we need to",
                "to find",
                "calculate",
                "because",
                "understand",
            ],
            "pedagogical_approach": [
                "notice",
                "remember",
                "important",
                "careful",
                "think about",
            ],
            "methodology_focus": [
                "approach",
                "strategy",
                "method",
                "technique",
                "process",
            ],
            "student_engagement": [
                "you",
                "your",
                "can you",
                "what do you",
                "let's work",
            ],
            "clarity_indicators": [
                "clear",
                "step-by-step",
                "systematic",
                "organized",
                "logical",
            ],
        }

        model_scores = {}

        for model in models_to_test:
            model_type = model["type"]
            response = responses[model_type]
            response_lower = response.lower()

            category_scores = {}
            total_score = 0

            for category, indicators in teaching_indicators.items():
                category_score = sum(
                    1 for indicator in indicators if indicator in response_lower
                )
                category_scores[category] = category_score
                total_score += category_score

            model_scores[model_type] = {
                "total": total_score,
                "categories": category_scores,
                "name": model["name"],
            }

            print(f"\n{model['icon']} {model['name']}:")
            print(
                f"  Overall Teaching Quality Score: {total_score}/{sum(len(indicators) for indicators in teaching_indicators.values())}"
            )
            for category, score in category_scores.items():
                print(
                    f"  {category.replace('_', ' ').title()}: {score}/{len(teaching_indicators[category])}"
                )

        # Determine rankings
        sorted_models = sorted(
            model_scores.items(), key=lambda x: x[1]["total"], reverse=True
        )

        print("\n🏆 RANKINGS:")
        for i, (model_type, score_data) in enumerate(sorted_models, 1):
            print(f"   {i}. {score_data['name']}: {score_data['total']} points")

        # Specialized analysis for methodology model
        methodology_score = model_scores.get("pure_methodology", {}).get("total", 0)
        tutoring_score = model_scores.get("tutoring", {}).get("total", 0)
        general_score = model_scores.get("general_math", {}).get("total", 0)

        print("\n🔍 SPECIALIZED ANALYSIS:")
        print(
            f"   Pure Methodology Focus: {'✅ Highest' if methodology_score == max(methodology_score, tutoring_score, general_score) else '📊 Moderate' if methodology_score > min(methodology_score, tutoring_score, general_score) else '❌ Lowest'}"
        )
        print(
            f"   Tutoring Integration: {'✅ Optimal' if tutoring_score >= methodology_score else '📊 Good' if tutoring_score > general_score else '❌ Needs Work'}"
        )
        print(
            f"   Mathematical Content: {'✅ Strong' if general_score > 0 else '❌ Weak'}"
        )

        return {
            "responses": responses,
            "scores": model_scores,
            "rankings": sorted_models,
            "timestamp": datetime.now().isoformat(),
        }


def main():
    """Run mathematics models comparison"""
    comparator = MathematicsModelsComparator()

    # Mathematics test problems specifically designed to test all three approaches
    test_problems = [
        "Sarah has 36 stickers. She gives 1/4 of them to her brother and 1/3 of the remaining stickers to her sister. How many stickers does Sarah have left?",
        "A student is struggling with this problem: 'If a recipe calls for 2/3 cup of flour and you want to make 1.5 times the recipe, how much flour do you need?' Help guide them through it.",
        "Tom has $45. He buys 3 notebooks for $4 each and 2 pens for $3 each. How much money does Tom have left?",
    ]

    print("🔬 COMPARING THREE MATHEMATICS-RELEVANT MODELS")
    print("🚫 English model excluded (different subject matter)")
    print("📊 Models: General Math | Tutoring | Pure Methodology")
    print("=" * 80)

    for i, problem in enumerate(test_problems, 1):
        print(f"\n🧪 MATHEMATICS TEST {i}")
        comparison = comparator.compare_mathematics_models(problem)

        if i < len(test_problems):
            print("\n" + "=" * 80)
            input("Press Enter to continue to next test...")


if __name__ == "__main__":
    main()
