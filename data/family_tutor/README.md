Family Tutor / Educational Chat Dataset (Scaffold)
=================================================

Goal
----
Curate a blended, family‑friendly, educational tutoring dataset to fine‑tune a 7B model (e.g., Mistral) toward:
  - Helpful, kind, age‑appropriate dialogue
  - ELI5 style explanations and analogies
  - Light factual QA and reading comprehension
  - Basic math reasoning (controlled share)
  - Safety / refusal exemplars

Current Status
--------------
Scaffold script `scripts/family_tutor_curation.py` provides:
  - Loaders: DailyDialog (first turn), ELI5 (question + top answer)
  - Basic safety & profanity filtering (regex)
  - Readability (approx Flesch) filtering
  - Length truncation heuristic
  - Deduplication via content hash
  - Unified JSONL schema: { messages: [...], meta: {...} }

Schema
------
messages:
  - role=user / assistant
  - content=string
meta:
  - source (dataset origin)
  - category (dialogue | explanation | ...)
  - synthetic (bool) placeholder for future LLM rewrites
  - reading_ease (float)
  - flags (optional list)

Usage
-----
python scripts/family_tutor_curation.py --output data/family_tutor/curated_family_tutor.jsonl --max-examples 4000

Planned Extensions
------------------
1. Additional Loaders:
   - SciQ, ARC-Easy, GSM8K (simplified), SQuAD (short answers), OpenBookQA, SimpleWikipedia, EmpatheticDialogues, BlendedSkillTalk.
2. LLM Rewrites:
   - Complexity reduction (Flesch < target), style normalization, safety paraphrasing.
3. Safety Augmentation:
   - Add refusal exemplars: curated prompts + safe guidance responses.
4. Category Balancing:
   - Enforce target proportions per category with reservoir sampling + backfill.
5. Metrics Report:
   - Summary JSON: counts, avg tokens per category, rejection reasons histogram.
6. Evaluation Set:
   - Stratified 200 example hold‑out with rubric (helpfulness, correctness, age suitability, safety) for manual + automated eval.
7. Tokenization Pass:
   - Pre-compute token counts using model tokenizer to support batch size planning.
8. License Tracking:
   - Append license/source SPDX fields in meta.

Quality / Safety Filters (Current)
---------------------------------
Regex for profanity / adult / PII
Flesch readability threshold: 65
Max assistant tokens (approx words): 130

Reproducibility
---------------
Set --seed (default 42). For future rewrites include deterministic temperature sampling (t=0.2) and store rewrite_model + rewrite_seed in meta.

Next Immediate Steps
--------------------
1. Add SciQ + ARC-Easy loaders (factual QA) with short answer simplification.
2. Implement math subset (GSM8K) with solution condensation to concise rationale + final answer line.
3. Add evaluation splitting (train/val/test) consistent hash on first user message.
4. Produce stats JSON alongside curated JSONL.

File Inventory
--------------
curated_family_tutor.jsonl (generated) – unified dataset
README.md (this file) – design + roadmap

Contact / Notes
---------------
This directory is versioned; regenerate to update counts. Large rewrites should emit a new file suffix (e.g., curated_family_tutor_v2.jsonl) rather than overwriting to preserve lineage.
