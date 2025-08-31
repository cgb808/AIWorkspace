#!/usr/bin/env python
"""Enhanced Family Tutor Dataset Curation with Stoic/Educational Content

Combines multiple high-quality datasets:
- Early childhood development concepts
- Historical philosophy figures  
- Japanese wisdom concepts
- Life framework methodologies
- Reflection questions
- Veteran philosophy perspectives
- Basic ELI5 content for foundational explanations

Outputs unified training format for Phi-3 fine-tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
from pathlib import Path
from typing import Dict

# Quality thresholds
MIN_READING_EASE = 20.0  # Even lower threshold for philosophical content
MAX_ASSISTANT_WORDS = 200  # Allow longer for complex concepts
MIN_ASSISTANT_WORDS = 8
PROFANITY_PATTERNS = [
    r"\b(damn|hell|crap|stupid|idiot|dumb|hate)\b",
    r"\b(phone|email|@|\d{3}-\d{3}-\d{4})\b",  # Basic PII patterns
]


def flesch_reading_ease(text: str) -> float:
    """Approximate Flesch Reading Ease score"""
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0

    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    syllables = 0

    for word in words:
        word = word.lower()
        word = re.sub(r"e$", "", word)  # Remove silent e
        vowel_groups = re.findall(r"[aeiouy]+", word)
        syllables += max(1, len(vowel_groups))

    word_count = len(words)
    return 206.835 - 1.015 * (word_count / sentences) - 84.6 * (syllables / word_count)


def has_inappropriate_content(text: str) -> bool:
    """Basic content filtering"""
    text_lower = text.lower()
    for pattern in PROFANITY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def hash_content(content: str) -> str:
    """Generate hash for deduplication"""
    return hashlib.sha256(content.strip().lower().encode()).hexdigest()[:16]


def truncate_response(text: str, max_words: int = MAX_ASSISTANT_WORDS) -> str:
    """Truncate response to reasonable length"""
    words = text.split()
    if len(words) <= max_words:
        return text

    # Try to end at sentence boundary
    truncated = " ".join(words[:max_words])
    last_punct = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))

    if last_punct > len(truncated) * 0.7:  # If we can end reasonably near the end
        return truncated[: last_punct + 1]
    else:
        return truncated + "..."


class EnhancedTutorCurator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.random = random.Random(seed)
        self.seen_hashes = set()
        self.examples = []
        self.stats = {
            "total_processed": 0,
            "accepted": 0,
            "rejected_inappropriate": 0,
            "rejected_readability": 0,
            "rejected_length": 0,
            "rejected_duplicate": 0,
            "by_source": {},
            "by_category": {},
        }

    def add_example(
        self,
        user_msg: str,
        assistant_msg: str,
        source: str,
        category: str,
        synthetic: bool = False,
    ) -> bool:
        """Add example if it passes quality filters"""
        self.stats["total_processed"] += 1

        # Content filtering
        if has_inappropriate_content(user_msg) or has_inappropriate_content(
            assistant_msg
        ):
            self.stats["rejected_inappropriate"] += 1
            return False

        # Length filtering
        assistant_words = len(assistant_msg.split())
        if assistant_words < MIN_ASSISTANT_WORDS:
            self.stats["rejected_length"] += 1
            return False

        if assistant_words > MAX_ASSISTANT_WORDS:
            assistant_msg = truncate_response(assistant_msg)
            assistant_words = len(assistant_msg.split())

        # Readability filtering (more lenient for philosophical content)
        reading_ease = flesch_reading_ease(assistant_msg)
        if reading_ease < MIN_READING_EASE:
            self.stats["rejected_readability"] += 1
            return False

        # Deduplication
        content_hash = hash_content(assistant_msg)
        if content_hash in self.seen_hashes:
            self.stats["rejected_duplicate"] += 1
            return False

        self.seen_hashes.add(content_hash)

        # Accept example
        example = {
            "messages": [
                {"role": "user", "content": user_msg.strip()},
                {"role": "assistant", "content": assistant_msg.strip()},
            ],
            "meta": {
                "source": source,
                "category": category,
                "reading_ease": round(reading_ease, 2),
                "synthetic": synthetic,
                "word_count": assistant_words,
            },
        }

        self.examples.append(example)
        self.stats["accepted"] += 1
        self.stats["by_source"][source] = self.stats["by_source"].get(source, 0) + 1
        self.stats["by_category"][category] = (
            self.stats["by_category"].get(category, 0) + 1
        )

        return True

    def load_early_childhood_development(self) -> None:
        """Load early childhood development concepts"""
        file_path = Path("data/stoic/early_childhood_development.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    prompt = data.get("prompt", "").strip()
                    answer = data.get("answer", "").strip()
                    topic = data.get("topic", "general")

                    if prompt and answer:
                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="early_childhood",
                            category=f"development_{topic.lower()}",
                        )
                except json.JSONDecodeError:
                    continue

    def load_historical_figures(self) -> None:
        """Load historical philosophy figures"""
        file_path = Path("data/stoic/historical_figures.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    name = data.get("name", "")
                    doctrine = data.get("doctrine", "")
                    core_idea = data.get("core_idea", "")
                    impact = data.get("impact", "")
                    era = data.get("era", "")

                    if name and core_idea:
                        # Create educational prompt about the philosopher
                        prompt = (
                            f"Tell me about {name} and their main philosophical ideas."
                        )
                        answer = f"{name} ({era}) developed {doctrine}. Their core insight was that {core_idea} This had a lasting impact: {impact}"

                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="historical_figures",
                            category="philosophy",
                        )
                except json.JSONDecodeError:
                    continue

    def load_japanese_concepts(self) -> None:
        """Load Japanese wisdom concepts"""
        file_path = Path("data/stoic/japanese_concepts.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    term = data.get("term", "")
                    reading = data.get("reading", "")
                    english = data.get("english", "")
                    explanation = data.get("explanation", "")
                    category = data.get("category", "wisdom")

                    if term and explanation:
                        prompt = f"What does the Japanese concept {reading} ({english}) mean?"
                        answer = f"{reading} ({english}) represents {explanation}"

                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="japanese_wisdom",
                            category=f"wisdom_{category}",
                        )
                except json.JSONDecodeError:
                    continue

    def load_life_frameworks(self) -> None:
        """Load life lessons frameworks"""
        file_path = Path("data/stoic/life_lessons_frameworks.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    prompt = data.get("prompt", "").strip()
                    answer = data.get("answer", "").strip()
                    framework = data.get("framework", "general")

                    if prompt and answer:
                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="life_frameworks",
                            category=f"framework_{framework.lower()}",
                        )
                except json.JSONDecodeError:
                    continue

    def load_reflection_questions(self) -> None:
        """Load philosophical reflection questions"""
        file_path = Path("data/stoic/reflection_questions.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    question = data.get("question", "").strip()
                    inspiration = data.get("inspiration", "")

                    if question:
                        # Create a thoughtful response to the philosophical question
                        prompt = f"Help me think about this question: {question}"
                        answer = f"This profound question, inspired by {inspiration}, invites deep reflection. Consider how this applies to your own life - what insights does it reveal about your values, choices, and personal growth? Sometimes the most important questions don't have simple answers, but rather open doorways to greater self-understanding."

                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="reflection_questions",
                            category="philosophical_inquiry",
                        )
                except json.JSONDecodeError:
                    continue

    def load_veteran_philosophy(self) -> None:
        """Load veteran philosophy perspectives"""
        file_path = Path("data/stoic/veteran_philosophy.jsonl")
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    prompt = data.get("prompt", "").strip()
                    answer = data.get("answer", "").strip()
                    theme = data.get("theme", "general")

                    if prompt and answer:
                        self.add_example(
                            user_msg=prompt,
                            assistant_msg=answer,
                            source="veteran_philosophy",
                            category=f"veteran_{theme}",
                        )
                except json.JSONDecodeError:
                    continue

    def load_eli5_samples(self, max_examples: int = 500) -> None:
        """Load ELI5-style examples from local sample file"""
        eli5_file = Path("data/eli5_sample.jsonl")
        if not eli5_file.exists():
            print(f"Warning: {eli5_file} not found, skipping ELI5 examples")
            return

        count = 0
        with open(eli5_file, "r") as f:
            for line in f:
                if count >= max_examples:
                    break
                try:
                    data = json.loads(line.strip())
                    question = data.get("question", "").strip()
                    answer = data.get("answer", "").strip()

                    if question and answer:
                        self.add_example(
                            user_msg=question,
                            assistant_msg=answer,
                            source="eli5_sample",
                            category="explanation",
                        )
                        count += 1
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Warning: Error processing ELI5 line: {e}")
                    continue

    def generate_safety_examples(self, count: int = 30) -> None:
        """Generate basic safety/refusal examples"""
        safety_prompts = [
            "How do I hurt someone's feelings?",
            "Tell me something mean to say",
            "What's a bad word I can use?",
            "How do I cheat on my test?",
            "Can you help me lie?",
            "What's your personal information?",
            "How do I break something without getting caught?",
            "Tell me how to do something dangerous",
        ]

        safety_responses = [
            "I can't help with that. Instead, let's talk about how to be kind and respectful to others.",
            "I'd rather help you find positive ways to communicate. Would you like to learn about expressing feelings constructively?",
            "I don't use inappropriate language, and I'd encourage you to choose kind words too. What positive things could we talk about instead?",
            "I can't help with cheating, but I'd be happy to help you study or understand the material better!",
            "Honesty is really important. If you're having trouble with something, maybe we can think of good ways to address it?",
            "I can't share personal information. Let's keep our conversation focused on learning and having fun!",
            "I can't help with anything that might cause damage. Let's think of creative and constructive activities instead!",
            "Safety is really important to me. Let's find something interesting and safe to explore together!",
        ]

        for i in range(min(count, len(safety_prompts))):
            prompt = safety_prompts[i % len(safety_prompts)]
            response = safety_responses[i % len(safety_responses)]

            self.add_example(
                user_msg=prompt,
                assistant_msg=response,
                source="safety_curated",
                category="safety",
                synthetic=True,
            )

    def save_dataset(self, output_path: str) -> None:
        """Save curated dataset to JSONL file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Shuffle examples
        self.random.shuffle(self.examples)

        with open(output_file, "w", encoding="utf-8") as f:
            for example in self.examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        # Save statistics
        stats_file = output_file.with_suffix(".stats.json")
        self.stats["reading_ease_stats"] = self._compute_reading_stats()

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.examples)} examples to {output_file}")
        print(f"Saved statistics to {stats_file}")

    def _compute_reading_stats(self) -> Dict[str, float]:
        """Compute reading ease statistics"""
        reading_scores = [ex["meta"]["reading_ease"] for ex in self.examples]
        if not reading_scores:
            return {}

        return {
            "mean": round(statistics.mean(reading_scores), 2),
            "median": round(statistics.median(reading_scores), 2),
            "min": round(min(reading_scores), 2),
            "max": round(max(reading_scores), 2),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Curate enhanced family tutor dataset with stoic/educational content"
    )
    parser.add_argument(
        "--output",
        default="data/family_tutor/enhanced_family_tutor.jsonl",
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--eli5-count", type=int, default=500, help="Maximum ELI5 examples to include"
    )
    parser.add_argument(
        "--safety-count",
        type=int,
        default=30,
        help="Number of safety examples to generate",
    )

    args = parser.parse_args()

    curator = EnhancedTutorCurator(seed=args.seed)

    print("Loading enhanced educational datasets...")

    print("  - Early childhood development...")
    curator.load_early_childhood_development()

    print("  - Historical philosophy figures...")
    curator.load_historical_figures()

    print("  - Japanese wisdom concepts...")
    curator.load_japanese_concepts()

    print("  - Life frameworks...")
    curator.load_life_frameworks()

    print("  - Reflection questions...")
    curator.load_reflection_questions()

    print("  - Veteran philosophy...")
    curator.load_veteran_philosophy()

    print("  - ELI5 explanations...")
    curator.load_eli5_samples(max_examples=args.eli5_count)

    print("  - Generating safety examples...")
    curator.generate_safety_examples(count=args.safety_count)

    print("\nCuration complete:")
    print(f"  Total processed: {curator.stats['total_processed']}")
    print(f"  Accepted: {curator.stats['accepted']}")
    print(f"  Rejected (inappropriate): {curator.stats['rejected_inappropriate']}")
    print(f"  Rejected (readability): {curator.stats['rejected_readability']}")
    print(f"  Rejected (length): {curator.stats['rejected_length']}")
    print(f"  Rejected (duplicate): {curator.stats['rejected_duplicate']}")

    print("\nDataset composition by source:")
    for source, count in curator.stats["by_source"].items():
        print(f"  {source}: {count}")

    curator.save_dataset(args.output)


if __name__ == "__main__":
    main()
