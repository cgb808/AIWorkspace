# ZenGlow Engineering TODO
Date: 2025-08-26

## High Priority
- Stage timing instrumentation (`/rag/query2`): capture retrieve_ms, feature_ms, ltr_ms, fusion_ms.
- Fusion weights management endpoint (GET/PUT `/rag/fusion/weights`) + cache invalidation.
- Retrieval mode branching (`RAG_RETRIEVAL_MODE`): pgvector | supabase_rpc scaffold.

## Medium
- Extend `/metrics/json` & query stats with stage latency breakdown.
- Structured JSON logging + request IDs.
- Rate limiting (Redis token bucket) & API key middleware.
- TimescaleDB hypertable for `query_performance` (rollups).
- Add config bootstrap consolidation function.
- Test: backcompat env mapping + validation failure path.

## Low
- Model throughput sampler (tokens/sec) + dynamic registry updates.
- Lockfile generation (`make freeze`) + CI diff guard.
- Secret import alias (legacy path) if external tests require.
- ANN strategy config table (future retrieval enhancements).

## Done (Recent)
- Backcompat env shim & validation.
- Sanitized `/config/env` endpoint.
- Secrets bootstrap from Vault (Supabase key).
- System metrics integration.
- Feature + full response cache layers.
- Config env snapshot tests.
- Virtual environment + Makefile targets.

## Notes
Prioritize instrumentation before expanding retrieval strategies to ensure baseline metrics for comparison.