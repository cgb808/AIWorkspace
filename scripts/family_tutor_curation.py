#!/usr/bin/env python
"""Family Tutor Dataset Curation Script

Curates a blended, family-friendly educational dataset from multiple sources:
- ELI5 explanations
- DailyDialog conversations (family-appropriate)
- Basic safety/refusal examples

Outputs unified JSONL with schema:
{
  "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "meta": {"source": "...", "category": "...", "reading_ease": 0.0, "synthetic": false}
}
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
MIN_READING_EASE = 65.0  # Target family-friendly readability
MAX_ASSISTANT_WORDS = 130
MIN_ASSISTANT_WORDS = 8
PROFANITY_PATTERNS = [
    r"\b(damn|hell|crap|stupid|idiot|dumb|hate)\b",
    r"\b(sex|drug|alcohol|violence|death|kill)\b",
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


class FamilyTutorCurator:
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
        if (
            assistant_words < MIN_ASSISTANT_WORDS
            or assistant_words > MAX_ASSISTANT_WORDS
        ):
            assistant_msg = truncate_response(assistant_msg)
            assistant_words = len(assistant_msg.split())
            if assistant_words < MIN_ASSISTANT_WORDS:
                self.stats["rejected_length"] += 1
                return False

        # Readability filtering
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

    def load_eli5_samples(self, max_examples: int = 1000) -> None:
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

    def generate_safety_examples(self, count: int = 50) -> None:
        """Generate basic safety/refusal examples"""
        safety_prompts = [
            "How do I hurt someone's feelings?",
            "Tell me something mean to say to my sister",
            "What's a bad word I can use?",
            "How do I cheat on my test?",
            "Can you help me lie to my parents?",
            "What's your phone number?",
            "Where do you live?",
            "Can you give me someone's personal information?",
            "How do I break something without getting caught?",
            "Tell me how to do something dangerous",
        ]

        safety_responses = [
            "I can't help with that. Instead, let's talk about how to be kind and respectful to others.",
            "I'd rather help you find positive ways to communicate. Would you like to learn about expressing feelings constructively?",
            "I don't use inappropriate language, and I'd encourage you to choose kind words too. What positive things could we talk about instead?",
            "I can't help with cheating, but I'd be happy to help you study or understand the material better!",
            "Honesty is really important. If you're having trouble with something, maybe we can think of good ways to talk to your parents about it?",
            "I can't share personal information like that. Let's keep our conversation focused on learning and having fun!",
            "I don't share personal details. Is there something educational or fun we could explore together instead?",
            "I can't share anyone's private information. Privacy is really important! What would you like to learn about today?",
            "I can't help with anything that might cause damage. Let's think of creative and safe activities instead!",
            "Safety is really important to me. Let's find something fun and safe to explore together!",
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

    def generate_educational_examples(self, count: int = 100) -> None:
        """Generate basic educational Q&A examples"""
        educational_qa = [
            (
                "What is photosynthesis?",
                "Photosynthesis is how plants make their own food! They use sunlight, water, and air (carbon dioxide) to create sugar, which gives them energy to grow. It's like plants have their own kitchen powered by the sun!",
            ),
            (
                "Why is the sky blue?",
                "The sky looks blue because of how sunlight bounces around in our atmosphere! Sunlight has many colors mixed together, but blue light gets scattered more than other colors, so that's what we see most.",
            ),
            (
                "How do birds fly?",
                "Birds can fly because they have special lightweight bones, powerful flight muscles, and feathers that help them catch air. Their wings are shaped to create lift - the same force that helps airplanes fly!",
            ),
            (
                "What makes rainbows?",
                "Rainbows happen when sunlight shines through water droplets in the air! The water acts like a prism and splits the white sunlight into all its beautiful colors - red, orange, yellow, green, blue, indigo, and violet.",
            ),
            (
                "Why do we need to sleep?",
                "Sleep is super important because it's when our bodies and brains recharge! While we sleep, our brains organize memories, our bodies grow and repair themselves, and we get energy for the next day.",
            ),
            (
                "How do magnets work?",
                "Magnets have invisible force fields around them! Some materials like iron are attracted to these fields, while others aren't. The Earth is like a giant magnet too, which is how compasses work!",
            ),
            (
                "What are the phases of the moon?",
                "The moon looks different throughout the month because of how sunlight hits it! Sometimes we see the whole bright side (full moon), sometimes just a sliver (crescent), and sometimes we can't see it at all (new moon).",
            ),
            (
                "How do fish breathe underwater?",
                "Fish breathe through special organs called gills! Water flows over their gills, which take oxygen from the water instead of from air like we do. It's like having underwater lungs!",
            ),
            (
                "Why do leaves change color in fall?",
                "Leaves change color because they stop making the green stuff (chlorophyll) that helps them make food. When the green fades away, we can see the other colors that were hiding underneath - yellow, orange, and red!",
            ),
            (
                "What is gravity?",
                "Gravity is an invisible force that pulls things toward each other! The bigger something is, the stronger its gravity. Earth's gravity keeps us on the ground and makes things fall down instead of floating away!",
            ),
        ]

        for i in range(
            min(count, len(educational_qa) * 3)
        ):  # Allow repetition with variation
            question, answer = educational_qa[i % len(educational_qa)]

            self.add_example(
                user_msg=question,
                assistant_msg=answer,
                source="educational_curated",
                category="science",
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
    parser = argparse.ArgumentParser(description="Curate family tutor dataset")
    parser.add_argument(
        "--output",
        default="data/family_tutor/curated_family_tutor.jsonl",
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=4000,
        help="Maximum total examples to generate",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--eli5-count", type=int, default=1000, help="Maximum ELI5 examples to include"
    )
    parser.add_argument(
        "--safety-count",
        type=int,
        default=50,
        help="Number of safety examples to generate",
    )
    parser.add_argument(
        "--educational-count",
        type=int,
        default=200,
        help="Number of educational examples to generate",
    )

    args = parser.parse_args()

    curator = FamilyTutorCurator(seed=args.seed)

    print("Loading ELI5 examples...")
    curator.load_eli5_samples(max_examples=args.eli5_count)

    print("Generating safety examples...")
    curator.generate_safety_examples(count=args.safety_count)

    print("Generating educational examples...")
    curator.generate_educational_examples(count=args.educational_count)

    print("\nCuration complete:")
    print(f"  Total processed: {curator.stats['total_processed']}")
    print(f"  Accepted: {curator.stats['accepted']}")
    print(f"  Rejected (inappropriate): {curator.stats['rejected_inappropriate']}")
    print(f"  Rejected (readability): {curator.stats['rejected_readability']}")
    print(f"  Rejected (length): {curator.stats['rejected_length']}")
    print(f"  Rejected (duplicate): {curator.stats['rejected_duplicate']}")

    curator.save_dataset(args.output)


if __name__ == "__main__":
    main()
