#!/usr/bin/env python3
"""
Download and Evaluate Tutoring Datasets
Downloads the highest-quality tutoring datasets for integration into calculative fine-tuning
"""

import json
from pathlib import Path

from datasets import load_dataset


class TutoringDatasetDownloader:
    """Download and evaluate tutoring-specific datasets"""

    def __init__(self, output_dir="data/tutoring_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Priority tutoring datasets based on research
        self.PRIORITY_DATASETS = {
            "Eedi/Question-Anchored-Tutoring-Dialogues-2k": {
                "priority": "highest",
                "reason": "Actual math tutoring dialogues",
                "subject": "mathematics",
                "format": "dialogue",
            },
            "drwlf/Teaching-Dataset": {
                "priority": "highest",
                "reason": "Explicitly designed for teaching/instruction",
                "subject": "general",
                "format": "instructional",
            },
            "KarthikaRajagopal/socratic_teaching_dataset": {
                "priority": "highest",
                "reason": "Socratic method teaching - perfect for tutoring",
                "subject": "general",
                "format": "socratic",
            },
            "Josephgflowers/OpenOrca-Step-by-step-reasoning": {
                "priority": "high",
                "reason": "Step-by-step reasoning for STEM",
                "subject": "mathematics",
                "format": "step_by_step",
            },
            "pbcong/gsm8k_step_by_step": {
                "priority": "high",
                "reason": "Math word problems with step-by-step solutions",
                "subject": "mathematics",
                "format": "step_by_step",
            },
            "ChristophSchuhmann/basic-math-problems-with-step-by-step-solutions": {
                "priority": "high",
                "reason": "Basic math with detailed solutions",
                "subject": "mathematics",
                "format": "step_by_step",
            },
        }

    def download_tutoring_dataset(self, dataset_id, sample_size=5000):
        """Download and sample a tutoring dataset"""
        print(f"📥 Downloading {dataset_id}...")

        try:
            # Load dataset
            dataset = load_dataset(dataset_id, split="train")
            print(f"   📊 Total examples: {len(dataset):,}")

            # Take a sample for evaluation
            sample_size = min(sample_size, len(dataset))
            sampled_dataset = dataset.select(range(sample_size))

            # Save sample
            dataset_name = dataset_id.replace("/", "_")
            output_file = self.output_dir / f"{dataset_name}_sample.jsonl"

            with open(output_file, "w") as f:
                for example in sampled_dataset:
                    f.write(json.dumps(example) + "\n")

            print(f"   ✅ Saved {sample_size:,} examples to {output_file}")

            # Analyze structure
            first_example = sampled_dataset[0]
            analysis = {
                "dataset_id": dataset_id,
                "total_examples": len(dataset),
                "sample_size": sample_size,
                "columns": list(first_example.keys()),
                "first_example": first_example,
                "output_file": str(output_file),
            }

            return analysis

        except Exception as e:
            print(f"   ❌ Failed to download {dataset_id}: {e}")
            return None

    def evaluate_tutoring_quality(self, analysis):
        """Evaluate the tutoring quality of a dataset"""
        print(f"\n🔍 Evaluating: {analysis['dataset_id']}")
        print(f"   Columns: {analysis['columns']}")

        # Look for tutoring indicators in the structure
        tutoring_indicators = []
        columns = [col.lower() for col in analysis["columns"]]

        if any(col in columns for col in ["dialogue", "conversation", "messages"]):
            tutoring_indicators.append("Has dialogue/conversation structure")

        if any(col in columns for col in ["step", "reasoning", "explanation"]):
            tutoring_indicators.append("Contains step-by-step reasoning")

        if any(col in columns for col in ["question", "answer", "response"]):
            tutoring_indicators.append("Question-answer format")

        # Examine first example
        first_example = analysis["first_example"]
        print("   First example preview:")
        for key, value in first_example.items():
            if isinstance(value, str):
                print(f"      {key}: {value[:150]}...")
            else:
                print(f"      {key}: {type(value)} - {value}")

        print(f"   Tutoring indicators: {tutoring_indicators}")

        return {
            "dataset_id": analysis["dataset_id"],
            "tutoring_indicators": tutoring_indicators,
            "quality_score": len(tutoring_indicators),
            "structure_analysis": analysis,
        }

    def convert_to_instructional_format(self, dataset_file, dataset_info):
        """Convert dataset to our instructional format"""
        print(
            f"\n🔄 Converting {dataset_info['dataset_id']} to instructional format..."
        )

        # Load the dataset
        examples = []
        with open(dataset_file, "r") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))

        # Convert based on dataset structure
        converted_examples = []
        dataset_id = dataset_info["dataset_id"]

        for example in examples[:100]:  # Convert first 100 as sample
            converted = self.convert_example_to_instructional(example, dataset_id)
            if converted:
                converted_examples.append(converted)

        # Save converted format
        dataset_name = dataset_id.replace("/", "_")
        output_file = self.output_dir / f"{dataset_name}_instructional.jsonl"

        with open(output_file, "w") as f:
            for example in converted_examples:
                f.write(json.dumps(example) + "\n")

        print(f"   ✅ Converted {len(converted_examples)} examples to {output_file}")
        return str(output_file)

    def convert_example_to_instructional(self, example, dataset_id):
        """Convert a single example to instructional format"""

        # Different conversion strategies based on dataset
        if "Question-Anchored-Tutoring" in dataset_id:
            # Already in dialogue format - extract Q&A
            if "dialogue" in example:
                dialogue = example["dialogue"]
                if isinstance(dialogue, list) and len(dialogue) >= 2:
                    # Find question and answer in dialogue
                    question = None
                    answer = None
                    for turn in dialogue:
                        if "student" in turn.get("role", "").lower():
                            question = turn.get("content", "")
                        elif "tutor" in turn.get("role", "").lower():
                            answer = turn.get("content", "")
                            break

                    if question and answer:
                        return {
                            "instruction": f"[LEARNING_CONTEXT] Mathematics Tutoring [LEARNING_OBJECTIVE] Provide step-by-step tutoring guidance. [TASK] {question}",
                            "input": "",
                            "output": f"[TUTORING_RESPONSE] {answer}",
                        }

        elif "Teaching-Dataset" in dataset_id:
            # Look for instruction/response format
            if "instruction" in example and "response" in example:
                return {
                    "instruction": f"[LEARNING_CONTEXT] General Instruction [LEARNING_OBJECTIVE] Provide clear teaching guidance. [TASK] {example['instruction']}",
                    "input": example.get("input", ""),
                    "output": f"[TEACHING_RESPONSE] {example['response']}",
                }

        elif "socratic" in dataset_id.lower():
            # Socratic method format
            if "question" in example and "answer" in example:
                return {
                    "instruction": f"[LEARNING_CONTEXT] Socratic Teaching [LEARNING_OBJECTIVE] Guide student discovery through questioning. [TASK] {example['question']}",
                    "input": "",
                    "output": f"[SOCRATIC_RESPONSE] {example['answer']}",
                }

        elif "step-by-step" in dataset_id.lower():
            # Step-by-step reasoning format
            if "problem" in example and "solution" in example:
                return {
                    "instruction": f"[LEARNING_CONTEXT] Step-by-Step Learning [LEARNING_OBJECTIVE] Provide detailed problem-solving guidance. [TASK] {example['problem']}",
                    "input": "",
                    "output": f"[STEP_BY_STEP_RESPONSE] {example['solution']}",
                }
            elif "question" in example and "answer" in example:
                return {
                    "instruction": f"[LEARNING_CONTEXT] Step-by-Step Learning [LEARNING_OBJECTIVE] Provide detailed problem-solving guidance. [TASK] {example['question']}",
                    "input": "",
                    "output": f"[STEP_BY_STEP_RESPONSE] {example['answer']}",
                }

        # Generic conversion for other formats
        for q_key in ["question", "prompt", "instruction"]:
            for a_key in ["answer", "response", "output"]:
                if q_key in example and a_key in example:
                    return {
                        "instruction": f"[LEARNING_CONTEXT] Instructional Guidance [LEARNING_OBJECTIVE] Provide clear educational support. [TASK] {example[q_key]}",
                        "input": "",
                        "output": f"[INSTRUCTIONAL_RESPONSE] {example[a_key]}",
                    }

        return None


def main():
    """Download and evaluate top tutoring datasets"""
    downloader = TutoringDatasetDownloader()

    print("🎯 TUTORING DATASET DOWNLOAD & EVALUATION")
    print("=" * 60)

    # Download priority datasets
    dataset_analyses = []
    for dataset_id, info in downloader.PRIORITY_DATASETS.items():
        print(f"\n{'='*50}")
        print(f"Processing: {dataset_id}")
        print(
            f"Priority: {info['priority']} | Subject: {info['subject']} | Format: {info['format']}"
        )

        analysis = downloader.download_tutoring_dataset(dataset_id, sample_size=1000)
        if analysis:
            evaluation = downloader.evaluate_tutoring_quality(analysis)
            dataset_analyses.append(evaluation)

            # Convert to instructional format
            converted_file = downloader.convert_to_instructional_format(
                analysis["output_file"], evaluation
            )

    # Summary
    print("\n🎉 TUTORING DATASET EVALUATION COMPLETE")
    print("=" * 50)
    print(f"Downloaded and evaluated {len(dataset_analyses)} tutoring datasets")

    for eval_result in dataset_analyses:
        print(f"\n📚 {eval_result['dataset_id']}")
        print(f"   Quality Score: {eval_result['quality_score']}/3")
        print(f"   Indicators: {', '.join(eval_result['tutoring_indicators'])}")

    print("\n🎯 READY FOR CALCULATIVE FINE-TUNING!")
    print(
        "   Use these high-quality tutoring datasets in place of general educational content"
    )
    print(f"   Location: {downloader.output_dir}")


if __name__ == "__main__":
    main()
