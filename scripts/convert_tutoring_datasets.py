#!/usr/bin/env python3
"""
Tutoring Dataset Converter
Converts tutoring datasets to our instructional format for calculative fine-tuning
"""

import json
from pathlib import Path

class TutoringDatasetConverter:
    """Convert tutoring datasets to instructional format"""
    
    def __init__(self):
        self.input_dir = Path("data/tutoring_datasets")
        self.output_dir = Path("data/tutoring_instructional")
        self.output_dir.mkdir(exist_ok=True)
    
    def convert_gsm8k_step_by_step(self):
        """Convert GSM8K step-by-step dataset to tutoring format"""
        print("🔄 Converting GSM8K Step-by-Step dataset...")
        
        input_file = self.input_dir / "pbcong_gsm8k_step_by_step_sample.jsonl"
        output_file = self.output_dir / "mathematics_tutoring_gsm8k.jsonl"
        
        converted_examples = []
        
        with open(input_file, 'r') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    
                    question = example['question']
                    answer = example['answer']
                    
                    # Clean up the answer format
                    if '<solution>' in answer:
                        solution_part = answer.split('<solution>')[1].split('</solution>')[0].strip()
                        final_answer = answer.split('Final answer:')[1].strip() if 'Final answer:' in answer else ""
                        
                        tutoring_response = f"{solution_part}\n\nFinal Answer: {final_answer}"
                    else:
                        tutoring_response = answer
                    
                    converted = {
                        'instruction': f"[LEARNING_CONTEXT] Mathematics Tutoring [LEARNING_OBJECTIVE] Solve math word problems step-by-step with clear explanations. [TASK] {question}",
                        'input': '',
                        'output': f"[TUTORING_RESPONSE] {tutoring_response}"
                    }
                    
                    converted_examples.append(converted)
        
        # Save converted examples
        with open(output_file, 'w') as f:
            for example in converted_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"   ✅ Converted {len(converted_examples)} GSM8K examples to {output_file}")
        return len(converted_examples)
    
    def convert_socratic_teaching(self):
        """Convert Socratic teaching dataset"""
        print("🔄 Converting Socratic Teaching dataset...")
        
        input_file = self.input_dir / "KarthikaRajagopal_socratic_teaching_dataset_sample.jsonl"
        output_file = self.output_dir / "general_tutoring_socratic.jsonl"
        
        converted_examples = []
        
        with open(input_file, 'r') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    
                    messages = example['messages']
                    
                    # Extract the first student question and complete dialogue
                    student_question = None
                    dialogue_text = []
                    
                    for msg in messages:
                        role = msg['role']
                        content = msg['content']
                        
                        if role == 'user' and student_question is None:
                            student_question = content
                        
                        dialogue_text.append(f"{role.title()}: {content}")
                    
                    if student_question:
                        full_dialogue = "\n\n".join(dialogue_text)
                        
                        converted = {
                            'instruction': f"[LEARNING_CONTEXT] Socratic Tutoring [LEARNING_OBJECTIVE] Guide student learning through questioning and discovery. [TASK] {student_question}",
                            'input': '',
                            'output': f"[SOCRATIC_TUTORING_RESPONSE] {full_dialogue}"
                        }
                        
                        converted_examples.append(converted)
        
        # Save converted examples
        with open(output_file, 'w') as f:
            for example in converted_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"   ✅ Converted {len(converted_examples)} Socratic examples to {output_file}")
        return len(converted_examples)
    
    def create_combined_tutoring_dataset(self):
        """Create combined tutoring dataset for calculative fine-tuning"""
        print("\n📚 Creating combined tutoring dataset...")
        
        # Convert individual datasets
        gsm8k_count = self.convert_gsm8k_step_by_step()
        socratic_count = self.convert_socratic_teaching()
        
        # Combine all tutoring datasets
        combined_examples = []
        
        # Load GSM8K examples
        gsm8k_file = self.output_dir / "mathematics_tutoring_gsm8k.jsonl"
        if gsm8k_file.exists():
            with open(gsm8k_file, 'r') as f:
                for line in f:
                    if line.strip():
                        combined_examples.append(json.loads(line))
        
        # Load Socratic examples  
        socratic_file = self.output_dir / "general_tutoring_socratic.jsonl"
        if socratic_file.exists():
            with open(socratic_file, 'r') as f:
                for line in f:
                    if line.strip():
                        combined_examples.append(json.loads(line))
        
        # Shuffle and save combined dataset
        import random
        random.shuffle(combined_examples)
        
        combined_file = self.output_dir / "combined_tutoring_dataset.jsonl"
        with open(combined_file, 'w') as f:
            for example in combined_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"\n🎯 TUTORING DATASET CONVERSION COMPLETE!")
        print(f"   📊 GSM8K Math Tutoring: {gsm8k_count} examples")
        print(f"   🤔 Socratic Teaching: {socratic_count} examples")
        print(f"   📚 Combined Dataset: {len(combined_examples)} examples")
        print(f"   📁 Location: {combined_file}")
        
        # Create dataset statistics
        stats = {
            'total_examples': len(combined_examples),
            'gsm8k_examples': gsm8k_count,
            'socratic_examples': socratic_count,
            'output_file': str(combined_file),
            'format': 'instructional_tutoring',
            'ready_for_calculative_training': True
        }
        
        stats_file = self.output_dir / "tutoring_dataset_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return str(combined_file)

def main():
    """Convert tutoring datasets for calculative fine-tuning"""
    converter = TutoringDatasetConverter()
    
    print("🎯 TUTORING DATASET CONVERSION")
    print("=" * 50)
    print("Converting tutoring datasets to instructional format for calculative fine-tuning...")
    
    combined_file = converter.create_combined_tutoring_dataset()
    
    print(f"\n✅ Ready for calculative fine-tuning with tutoring datasets!")
    print(f"   Use: {combined_file}")
    print(f"   These datasets focus on actual tutoring methodologies")
    print(f"   Including step-by-step reasoning and Socratic questioning")

if __name__ == "__main__":
    main()
