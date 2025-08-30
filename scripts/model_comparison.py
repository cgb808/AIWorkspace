#!/usr/bin/env python3
"""
Model Comparison Tool
Compare responses between different specialized models
"""

import requests
import json
from datetime import datetime

class ModelComparator:
    """Compare responses from different models"""
    
    def __init__(self, ollama_url="http://localhost:11435"):
        self.ollama_url = ollama_url
        self.base_model = "phi3:mini"
    
    def query_model_with_context(self, prompt, context_type="base"):
        """Query model with specific context formatting"""
        
        # Format prompt based on context type
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
    
    def compare_models(self, test_problem):
        """Compare base, general math, and tutoring model responses"""
        
        print("🎯 MODEL COMPARISON ANALYSIS")
        print("=" * 70)
        print(f"Test Problem: {test_problem}")
        print("=" * 70)
        
        # Test with base model (no special context)
        print("\n📱 BASE MODEL (No Special Context)")
        print("-" * 40)
        base_response = self.query_model_with_context(test_problem, "base")
        print(f"Response: {base_response[:300]}...")
        
        # Test with general mathematics context
        print("\n📚 GENERAL MATHEMATICS MODEL")
        print("-" * 40)
        math_response = self.query_model_with_context(test_problem, "general_math")
        print(f"Response: {math_response[:300]}...")
        
        # Test with tutoring context
        print("\n🎓 TUTORING MODEL (Step-by-Step)")
        print("-" * 40)
        tutoring_response = self.query_model_with_context(test_problem, "tutoring")
        print(f"Response: {tutoring_response[:300]}...")
        
        # Analysis
        print("\n📊 ANALYSIS")
        print("=" * 40)
        
        # Check for tutoring indicators
        tutoring_indicators = {
            "step_by_step": ["step", "first", "next", "then", "finally"],
            "clear_breakdown": ["calculate", "subtract", "add", "multiply", "divide"],
            "teaching_style": ["let's", "we", "now", "remember"],
            "final_answer": ["final answer", "therefore", "so", "result"]
        }
        
        models = {
            "Base": base_response,
            "General Math": math_response, 
            "Tutoring": tutoring_response
        }
        
        for model_name, response in models.items():
            response_lower = response.lower()
            score = 0
            found_indicators = []
            
            for category, indicators in tutoring_indicators.items():
                for indicator in indicators:
                    if indicator in response_lower:
                        score += 1
                        found_indicators.append(f"{category}: {indicator}")
            
            print(f"\n{model_name} Model:")
            print(f"  Teaching Quality Score: {score}/20")
            print(f"  Found indicators: {len(found_indicators)}")
            if found_indicators:
                print(f"  Examples: {', '.join(found_indicators[:3])}")
        
        return {
            'base_response': base_response,
            'math_response': math_response,
            'tutoring_response': tutoring_response,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Run model comparison"""
    comparator = ModelComparator()
    
    # Test problems to compare
    test_problems = [
        "Sarah has 36 stickers. She gives 1/4 of them to her brother and 1/3 of the remaining stickers to her sister. How many stickers does Sarah have left?",
        "A rectangle has a length of 12 cm and a width of 8 cm. What is its area and perimeter?",
        "If a car travels 240 miles in 4 hours, what is its average speed in miles per hour?"
    ]
    
    print("🔬 COMPARING BASE vs GENERAL MATH vs TUTORING MODELS")
    print("=" * 80)
    
    for i, problem in enumerate(test_problems, 1):
        print(f"\n🧪 TEST {i}")
        comparison = comparator.compare_models(problem)
        
        if i < len(test_problems):
            print("\n" + "="*80)
            input("Press Enter to continue to next test...")

if __name__ == "__main__":
    main()
