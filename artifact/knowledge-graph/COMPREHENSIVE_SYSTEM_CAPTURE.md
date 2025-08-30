# Comprehensive System Capture (Excerpt)

This document synthesizes distributed architectural knowledge into a single, high-signal reference. Each section maps to entities and relations stored in the knowledge graph for automated retrieval and reasoning.

## 1. RAG Pipeline Overview
Stages: retrieve -> feature_assembly -> ltr -> fusion -> llm_generate. Planned instrumentation will measure each stage latency for observability and UI display.

## 2. LLM Backend Strategy
Backends prioritized: Supabase Edge Functions, llama.cpp server, Ollama, development fake. Fallback logic executed inside `LLMClient.generate_with_metadata`.

## 3. Frontend Chat Surface
`/gemma-phi` route provides chat UI. Pending: wiring to `/rag/query` and display of per-stage timings, fusion weights, and backend selection metadata.

## 4. Indexing & Model Registry
`scripts/index_codebase.py` enumerates Python modules, hashes them, and seeds a model registry. Enhancement required: exclude `archive/` directory to avoid stale modules.

## 5. Operational Backlog (High Priority Excerpts)
- Stage Timing Instrumentation
- Fusion Weights Management Endpoint
- Retrieval Mode Branching via `RAG_RETRIEVAL_MODE`

## 6. Strategies
StageTimingPlan, FusionWeightsManagement, RetrievalModeBranching encode evolving optimization levers for performance and experimentation.

## 7. Knowledge Graph Rationale
Entities hold atomic observation phrases enabling granular embedding & diff. Relations capture directional semantics for impact analysis (e.g., instrumentation changes affecting UI surfaces).

---
This excerpt is intentionally concise; full narrative can be regenerated from source docs + index script if drift detected.
