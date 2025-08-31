#!/usr/bin/env python3
"""
Unified Dataset Curator with Instructional Prompting
Converts all datasets to consistent format with proper role-based instructions
"""

import hashlib
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class UnifiedDatasetCurator:
    def __init__(self):
        self.role_templates = {
            "family_tutor": {
                "system": "You are a warm, patient family tutor who helps children and parents learn together. Use age-appropriate language, encourage curiosity, and always maintain a supportive tone. Draw from educational psychology, child development, and proven learning strategies.",
                "separators": [
                    "[FAMILY_CONTEXT]",
                    "[LEARNING_OBJECTIVE]",
                    "[RESPONSE]",
                ],
                "instruction_prefix": "As a family tutor, ",
            },
            "philosophical_guide": {
                "system": "You are a thoughtful philosophical guide who helps people explore deep questions about life, ethics, and meaning. Draw from various philosophical traditions including Stoicism, Eastern wisdom, and modern philosophy. Encourage reflection and critical thinking.",
                "separators": [
                    "[PHILOSOPHICAL_CONTEXT]",
                    "[REFLECTION_PROMPT]",
                    "[GUIDANCE]",
                ],
                "instruction_prefix": "As a philosophical guide, ",
            },
            "general_assistant": {
                "system": "You are a helpful, knowledgeable assistant who provides clear, accurate, and well-reasoned responses. You adapt your communication style to match the complexity and context of each question.",
                "separators": ["[CONTEXT]", "[TASK]", "[RESPONSE]"],
                "instruction_prefix": "As a helpful assistant, ",
            },
            "educational_expert": {
                "system": "You are an educational expert who specializes in making complex topics accessible and engaging. You use examples, analogies, and structured explanations to help learners at all levels understand difficult concepts.",
                "separators": [
                    "[LEARNING_CONTEXT]",
                    "[EXPLANATION_GOAL]",
                    "[TEACHING_RESPONSE]",
                ],
                "instruction_prefix": "As an educational expert, ",
            },
        }

        self.quality_filters = {
            "min_instruction_length": 10,
            "min_response_length": 20,
            "max_total_length": 2048,
            "forbidden_patterns": [
                "I can't",
                "I cannot",
                "I'm sorry, I can't",
                "As an AI",
                "I'm an AI",
                "I am an AI",
            ],
        }

    def classify_content_role(self, content: Dict[str, Any]) -> str:
        """Classify content to determine appropriate role template"""
        text = str(content).lower()

        # Family/child development indicators
        if any(
            word in text
            for word in ["child", "parent", "family", "development", "play", "learning"]
        ):
            return "family_tutor"

        # Philosophical content indicators
        if any(
            word in text
            for word in [
                "philosophy",
                "stoic",
                "wisdom",
                "meaning",
                "reflection",
                "ethics",
            ]
        ):
            return "philosophical_guide"

        # Educational content indicators
        if any(
            word in text
            for word in [
                "explain",
                "teach",
                "concept",
                "understand",
                "learn",
                "definition",
            ]
        ):
            return "educational_expert"

        # Default to general assistant
        return "general_assistant"

    def apply_instructional_formatting(
        self, instruction: str, response: str, role: str, context: str = ""
    ) -> Dict[str, Any]:
        """Apply proper instructional prompting with role-based formatting"""
        role_config = self.role_templates[role]

        # Build instructional prompt
        system_prompt = role_config["system"]
        instruction_prefix = role_config["instruction_prefix"]
        separators = role_config["separators"]

        # Format the instruction with separators and context
        formatted_instruction = f"{system_prompt}\n\n"

        if context:
            formatted_instruction += f"{separators[0]}\n{context}\n\n"

        formatted_instruction += (
            f"{separators[1]}\n{instruction_prefix}{instruction}\n\n"
        )
        formatted_instruction += f"{separators[2]}"

        return {
            "instruction": formatted_instruction,
            "input": "",  # Keep empty for consistency
            "output": response,
            "meta": {
                "role": role,
                "system_prompt": system_prompt,
                "separators_used": separators,
                "instructional_format": True,
                "timestamp": datetime.now().isoformat(),
            },
        }

    def convert_chat_to_alpaca(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert chat format to Alpaca with instructional prompting"""
        messages = chat_data.get("messages", [])
        meta = chat_data.get("meta", {})

        # Extract user and assistant messages
        user_msg = None
        assistant_msg = None

        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                assistant_msg = msg["content"]

        if not user_msg or not assistant_msg:
            return None

        # Determine role based on content
        role = self.classify_content_role(
            {"instruction": user_msg, "output": assistant_msg}
        )

        # Apply instructional formatting
        formatted = self.apply_instructional_formatting(
            instruction=user_msg,
            response=assistant_msg,
            role=role,
            context=meta.get("category", ""),
        )

        # Preserve original metadata
        formatted["meta"].update(meta)

        return formatted

    def enhance_alpaca_format(self, alpaca_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance existing Alpaca format with better instructional prompting"""
        instruction = alpaca_data.get("instruction", "")
        input_text = alpaca_data.get("input", "")
        output = alpaca_data.get("output", "")
        meta = alpaca_data.get("meta", {})

        # Combine instruction and input for role classification
        full_context = f"{instruction} {input_text}".strip()
        role = self.classify_content_role(
            {"instruction": full_context, "output": output}
        )

        # Apply instructional formatting
        formatted = self.apply_instructional_formatting(
            instruction=instruction, response=output, role=role, context=input_text
        )

        # Preserve original metadata
        formatted["meta"].update(meta)

        return formatted

    def convert_stoic_to_alpaca(
        self, stoic_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Convert stoic format (prompt/answer) to Alpaca with instructional prompting"""
        prompt = stoic_data.get("prompt", "")
        answer = stoic_data.get("answer", "")
        topic = stoic_data.get("topic", "")
        name = stoic_data.get("name", "")

        if not prompt or not answer:
            return None

        # Determine role based on content
        role = self.classify_content_role({"instruction": prompt, "output": answer})

        # Apply instructional formatting
        context = f"Topic: {topic}, Focus: {name}" if topic and name else ""
        formatted = self.apply_instructional_formatting(
            instruction=prompt, response=answer, role=role, context=context
        )

        # Preserve original metadata
        formatted["meta"].update(
            {
                "original_format": "stoic",
                "topic": topic,
                "name": name,
                "step": stoic_data.get("step", ""),
            }
        )

        return formatted

    def convert_eli5_to_alpaca(
        self, eli5_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Convert ELI5 format (question/answer) to Alpaca with instructional prompting"""
        question = eli5_data.get("question", "")
        answer = eli5_data.get("answer", "")

        if not question or not answer:
            return None

        # ELI5 content is inherently educational
        role = "educational_expert"

        # Apply instructional formatting with ELI5 context
        formatted = self.apply_instructional_formatting(
            instruction=f"Explain like I'm 5: {question}",
            response=answer,
            role=role,
            context="Simple explanation for young learners",
        )

        # Preserve original metadata
        formatted["meta"].update(
            {"original_format": "eli5", "original_question": question}
        )

        return formatted

    def convert_historical_to_alpaca(
        self, hist_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Convert historical figure format to Alpaca with instructional prompting"""
        name = hist_data.get("name", "")
        era = hist_data.get("era", "")
        doctrine = hist_data.get("doctrine", "")
        core_idea = hist_data.get("core_idea", "")
        impact = hist_data.get("impact", "")

        if not name or not core_idea:
            return None

        # Create instructional prompt about the historical figure
        instruction = f"Tell me about {name} and their philosophical contributions."
        response = f"{name} from {era} was known for {doctrine}. {core_idea} Their impact: {impact}"

        # Historical content is philosophical
        role = "philosophical_guide"

        formatted = self.apply_instructional_formatting(
            instruction=instruction,
            response=response,
            role=role,
            context=f"Historical Philosophy: {era}",
        )

        formatted["meta"].update(
            {
                "original_format": "historical",
                "figure_name": name,
                "era": era,
                "doctrine": doctrine,
            }
        )

        return formatted

    def convert_japanese_to_alpaca(
        self, jp_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Convert Japanese concept format to Alpaca with instructional prompting"""
        term = jp_data.get("term", "")
        reading = jp_data.get("reading", "")
        english = jp_data.get("english", "")
        category = jp_data.get("category", "")
        explanation = jp_data.get("explanation", "")

        if not term or not explanation:
            return None

        # Create instructional prompt about the Japanese concept
        instruction = f"Explain the Japanese concept '{term}' ({reading})."
        response = f"'{term}' ({reading}) means '{english}'. {explanation}"

        # Japanese wisdom is philosophical
        role = "philosophical_guide"

        formatted = self.apply_instructional_formatting(
            instruction=instruction,
            response=response,
            role=role,
            context=f"Japanese Wisdom: {category}",
        )

        formatted["meta"].update(
            {
                "original_format": "japanese",
                "term": term,
                "reading": reading,
                "category": category,
            }
        )

        return formatted

    def convert_reflection_to_alpaca(
        self, refl_data: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Convert reflection question format to Alpaca with instructional prompting"""
        question = refl_data.get("question", "")
        inspiration = refl_data.get("inspiration", "")

        if not question:
            return None

        # Create instructional prompt for philosophical reflection
        instruction = f"Help me reflect on this philosophical question: {question}"
        response = f"This profound question, inspired by {inspiration}, invites deep reflection. Consider how this applies to your own life - what insights does it reveal about your values, choices, and personal growth? Sometimes the most important questions don't have simple answers, but rather open doorways to greater self-understanding."

        # Reflection questions are philosophical
        role = "philosophical_guide"

        formatted = self.apply_instructional_formatting(
            instruction=instruction,
            response=response,
            role=role,
            context=f"Philosophical Reflection inspired by {inspiration}",
        )

        formatted["meta"].update(
            {
                "original_format": "reflection",
                "original_question": question,
                "inspiration": inspiration,
            }
        )

        return formatted

    def quality_filter(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply quality filters to ensure high-quality training data"""
        instruction = data.get("instruction", "")
        output = data.get("output", "")

        # Length checks
        if len(instruction) < self.quality_filters["min_instruction_length"]:
            return False, "instruction_too_short"

        if len(output) < self.quality_filters["min_response_length"]:
            return False, "response_too_short"

        total_length = len(instruction) + len(output)
        if total_length > self.quality_filters["max_total_length"]:
            return False, "total_too_long"

        # Content quality checks
        for pattern in self.quality_filters["forbidden_patterns"]:
            if pattern.lower() in output.lower():
                return False, f"forbidden_pattern: {pattern}"

        return True, "passed"

    def process_dataset_file(
        self, file_path: str, format_type: str = "auto"
    ) -> List[Dict[str, Any]]:
        """Process a single dataset file and convert to unified format"""
        results = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())

                    # Auto-detect format if not specified
                    if format_type == "auto":
                        if "messages" in data:
                            format_type = "chat"
                        elif "instruction" in data:
                            format_type = "alpaca"
                        elif "prompt" in data and "answer" in data:
                            format_type = "stoic"
                        elif "question" in data and "answer" in data:
                            format_type = "eli5"
                        elif "name" in data and "core_idea" in data:
                            format_type = "historical"
                        elif "term" in data and "explanation" in data:
                            format_type = "japanese"
                        elif "question" in data and "inspiration" in data:
                            format_type = "reflection"
                        else:
                            print(f"Unknown format in {file_path}:{line_num}")
                            continue

                    # Convert to unified format
                    if format_type == "chat":
                        converted = self.convert_chat_to_alpaca(data)
                    elif format_type == "alpaca":
                        converted = self.enhance_alpaca_format(data)
                    elif format_type == "stoic":
                        converted = self.convert_stoic_to_alpaca(data)
                    elif format_type == "eli5":
                        converted = self.convert_eli5_to_alpaca(data)
                    elif format_type == "historical":
                        converted = self.convert_historical_to_alpaca(data)
                    elif format_type == "japanese":
                        converted = self.convert_japanese_to_alpaca(data)
                    elif format_type == "reflection":
                        converted = self.convert_reflection_to_alpaca(data)
                    else:
                        print(f"Unsupported format: {format_type}")
                        continue

                    if converted is None:
                        continue

                    # Apply quality filtering
                    passes_filter, reason = self.quality_filter(converted)
                    if passes_filter:
                        converted["meta"]["source_file"] = file_path
                        converted["meta"]["source_line"] = line_num
                        results.append(converted)
                    else:
                        print(f"Filtered out {file_path}:{line_num} - {reason}")

                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue

        return results

    def deduplicate_by_content(
        self, datasets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate based on instruction+output hash"""
        seen_hashes = set()
        deduplicated = []

        for data in datasets:
            content_hash = hashlib.md5(
                (data["instruction"] + data["output"]).encode("utf-8")
            ).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                data["meta"]["content_hash"] = content_hash
                deduplicated.append(data)

        return deduplicated

    def curate_unified_dataset(
        self, source_files: List[str], output_file: str
    ) -> Dict[str, Any]:
        """Main curation function"""
        print("Starting unified dataset curation...")

        all_data = []
        stats = {
            "files_processed": 0,
            "total_examples": 0,
            "examples_by_role": {},
            "examples_by_source": {},
            "quality_filters": {},
        }

        # Process each source file
        for file_path in source_files:
            if not Path(file_path).exists():
                print(f"Warning: File not found: {file_path}")
                continue

            print(f"Processing: {file_path}")
            file_data = self.process_dataset_file(file_path)

            # Update stats
            stats["files_processed"] += 1
            stats["examples_by_source"][file_path] = len(file_data)

            all_data.extend(file_data)

        print(f"Collected {len(all_data)} examples before deduplication")

        # Deduplicate
        all_data = self.deduplicate_by_content(all_data)
        print(f"After deduplication: {len(all_data)} examples")

        # Shuffle for better training distribution
        random.shuffle(all_data)

        # Final stats
        stats["total_examples"] = len(all_data)
        for data in all_data:
            role = data["meta"]["role"]
            stats["examples_by_role"][role] = stats["examples_by_role"].get(role, 0) + 1

        # Save unified dataset
        with open(output_file, "w", encoding="utf-8") as f:
            for data in all_data:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        # Save stats
        stats_file = output_file.replace(".jsonl", ".stats.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"Unified dataset saved to: {output_file}")
        print(f"Stats saved to: {stats_file}")
        print(f"Total examples: {stats['total_examples']}")
        print(f"Role distribution: {stats['examples_by_role']}")

        return stats


if __name__ == "__main__":
    curator = UnifiedDatasetCurator()

    # Define all source files
    source_files = [
        "scripts/DATASET_for TUTOR_persona/combined_curated_cleaned_from_raw_v5_min_formatted.jsonl",
        "data/family_tutor/enhanced_family_tutor.jsonl",
        "data/eli5_sample.jsonl",
    ]

    # Add individual stoic files
    stoic_files = [
        "data/stoic/early_childhood_development.jsonl",
        "data/stoic/historical_figures.jsonl",
        "data/stoic/japanese_concepts.jsonl",
        "data/stoic/life_lessons_frameworks.jsonl",
        "data/stoic/reflection_questions.jsonl",
        "data/stoic/veteran_philosophy.jsonl",
    ]
    source_files.extend(stoic_files)

    # Output file
    output_file = "data/unified_instructional_dataset.jsonl"

    # Run curation
    stats = curator.curate_unified_dataset(source_files, output_file)

    print("\n=== CURATION COMPLETE ===")
    print(f"Ready for fine-tuning with {stats['total_examples']} examples")
