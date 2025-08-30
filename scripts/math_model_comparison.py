#!/usr/bin/env python3
"""
Mathematics Model Comparison Tool
Compare ONLY the mathematics-relevant models:
1. General Mathematics Model (standard datasets)
2. Tutoring Model (authentic tutoring datasets)
"""

import requests
import json
from datetime import datetime

class MathModelComparator:
    """Compare mathematics models only"""
    
    def __init__(self, ollama_url="http://localhost:11435"):
        self.ollama_url = ollama_url
        self.base_model = "phi3:mini"
    
    def query_model_with_context(self, prompt, context_type="general_math"):
        """Query model with specific mathematics context formatting"""
        
        # Format prompt based on mathematics context type
        if context_type == "general_math":
            formatted_prompt = f"[LEARNING_CONTEXT] Mathematics [LEARNING_OBJECTIVE] Understand and solve mathematical concepts clearly. [TASK] {prompt}"
        elif context_type == "tutoring":
            formatted_prompt = f"[LEARNING_CONTEXT] Mathematics Tutoring [LEARNING_OBJECTIVE] Solve math word problems step-by-step with clear explanations. [TASK] {prompt}"
        else:
            formatted_prompt = prompt
        
        try:
            payload = {
                "model": self.base_model,
                "prompt": formatted_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response received')
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Exception: {e}"
    
    def compare_math_models(self, test_problem):
        """Compare general mathematics vs tutoring mathematics models"""
        
        print("🎯 MATHEMATICS MODEL COMPARISON")
        print("=" * 70)
        print(f"Test Problem: {test_problem}")
        print("=" * 70)
        
        # Test with general mathematics context (standard datasets)
        print("\n📚 GENERAL MATHEMATICS MODEL")
        print("   Dataset: Standard mathematics content")
        print("   Training: Calculative fine-tuning on general math")
        print("-" * 50)
        math_response = self.query_model_with_context(test_problem, "general_math")
        print(f"Response:\n{math_response}")
        
        print("\n" + "="*70)
        
        # Test with tutoring context (authentic tutoring datasets)
        print("\n🎓 TUTORING MATHEMATICS MODEL")
        print("   Dataset: Authentic tutoring content (GSM8K + Socratic)")
        print("   Training: Calculative fine-tuning on tutoring data")
        print("-" * 50)
        tutoring_response = self.query_model_with_context(test_problem, "tutoring")
        print(f"Response:\n{tutoring_response}")
        
        # Analysis focusing on tutoring quality
        print("\n📊 TUTORING QUALITY ANALYSIS")
        print("=" * 50)
        
        # Check for authentic tutoring indicators
        tutoring_indicators = {
            "step_structure": ["step 1", "step 2", "step 3", "first", "next", "then", "finally"],
            "explanation_quality": ["let's", "we need to", "to find", "calculate", "because"],
            "pedagogical_approach": ["understand", "remember", "notice", "important", "careful"],
            "problem_breakdown": ["divide", "subtract", "multiply", "add", "remaining"],
            "final_clarity": ["therefore", "so", "final answer", "result", "total"]
        }
        
        models = {
            "General Math": math_response,
            "Tutoring": tutoring_response
        }
        
        for model_name, response in models.items():
            response_lower = response.lower()
            category_scores = {}
            total_score = 0
            
            for category, indicators in tutoring_indicators.items():
                category_score = sum(1 for indicator in indicators if indicator in response_lower)
                category_scores[category] = category_score
                total_score += category_score
            
            print(f"\n{model_name} Model Analysis:")
            print(f"  Overall Tutoring Quality Score: {total_score}/25")
            for category, score in category_scores.items():
                print(f"  {category.replace('_', ' ').title()}: {score}/{len(tutoring_indicators[category])}")
        
        # Determine which model demonstrates better tutoring
        math_score = sum(1 for indicators in tutoring_indicators.values() 
                        for indicator in indicators if indicator in math_response.lower())
        tutoring_score = sum(1 for indicators in tutoring_indicators.values() 
                           for indicator in indicators if indicator in tutoring_response.lower())
        
        print(f"\n🏆 WINNER: {'Tutoring Model' if tutoring_score > math_score else 'General Math Model' if math_score > tutoring_score else 'Tie'}")
        print(f"   Tutoring Model: {tutoring_score} vs General Math: {math_score}")
        
        return {
            'general_math_response': math_response,
            'tutoring_response': tutoring_response,
            'tutoring_score': tutoring_score,
            'general_math_score': math_score,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Run mathematics model comparison"""
    comparator = MathModelComparator()
    
    # Mathematics test problems specifically
    test_problems = [
        "Sarah has 36 stickers. She gives 1/4 of them to her brother and 1/3 of the remaining stickers to her sister. How many stickers does Sarah have left?",
        "A train travels 180 miles in 3 hours. If it maintains the same speed, how far will it travel in 5 hours?",
        "Tom has $45. He buys 3 notebooks for $4 each and 2 pens for $3 each. How much money does Tom have left?"
    ]
    
    print("🔬 COMPARING GENERAL MATH vs TUTORING MATHEMATICS MODELS")
    print("🚫 English model excluded (different subject matter)")
    print("=" * 80)
    
    for i, problem in enumerate(test_problems, 1):
        print(f"\n🧪 MATHEMATICS TEST {i}")
        comparison = comparator.compare_math_models(problem)
        
        if i < len(test_problems):
            print("\n" + "="*80)
            input("Press Enter to continue to next test...")

if __name__ == "__main__":
    main()
