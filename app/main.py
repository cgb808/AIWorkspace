"""FastAPI entrypoint for ZenGlow Indexer API.
Order of operations on import:
    1. Apply env backward compatibility shim (old -> new names).
    2. Bootstrap secrets (may populate SUPABASE_KEY).
    3. Validate required env vars (fail fast if missing).
Then import remainder of modules relying on configuration.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List
from app.rag.schemas import RAGQueryRequest, RAGQueryResponse, RetrievedChunk
from app.health.health_router import health_router
from typing import Generator

from app.core.config import apply_backward_compat_env, validate_required_env, config_router
from app.core.secrets import bootstrap_supabase_key

# 1. Backward compatibility env translation
_applied_compat = apply_backward_compat_env()
# 2. Load Supabase indexer key early (may populate SUPABASE_KEY from Vault)
bootstrap_supabase_key()
# 3. Validate required envs (raises RuntimeError if missing)
try:
    validate_required_env(fail_fast=True)
except RuntimeError as e:  # pragma: no cover - startup failure path
    # Re-raise to prevent app from starting with invalid config
    raise

from app.rag.pipeline import RAGPipeline
from app.rag.db_client import DBClient
from app.rag.embedder import Embedder
from app.rag.llm_client import LLMClient
from app.rag.ranking_router import router as ranking_router
from app.rag.ranking_router import rag_query2  # reuse logic for legacy endpoint refactor
from app.audio import transcription_router

# Legacy imports (can be deprecated once new pipeline stable)
# Legacy direct embedding/retrieval removed; use ranking_router logic instead. Edge LLM kept for answer generation.
from app.rag.edge_llm import get_edge_model_response  # Note: legacy direct embedding/retrieval removed; relies on ranking_router

app: FastAPI = FastAPI(title="ZenGlow Indexer API")
app.include_router(health_router)
app.include_router(ranking_router)
app.include_router(transcription_router.router)
app.include_router(config_router)

# Static assets (voice UI)
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    # Directory might not exist in some deploy contexts; fail soft
    pass


def get_rag_pipeline() -> Generator[RAGPipeline, None, None]:
    db_client = DBClient()
    embedder = Embedder()
    llm = LLMClient()
    pipeline = RAGPipeline(db_client=db_client, embedder=embedder, llm_client=llm)
    try:
        yield pipeline
    finally:
        db_client.close()

@app.post("/rag/query")  # Refactored legacy endpoint: delegates scoring to /rag/query2 logic
async def rag_query(request: Request) -> Dict[str, Any]:
    body = await request.json()
    query = body.get("query")
    top_k = body.get("top_k", 5)
    if not query:
        return {"error": "Missing query"}

    # Reuse rag_query2 internal logic for retrieval + scoring (simulate payload)
    ranking_payload = type("Tmp", (), {"query": query, "top_k": top_k})()
    try:
        ranked = await rag_query2(ranking_payload)  # returns dict with results/items
    except Exception as e:  # fallback returns error reason only (legacy retrieval removed)
        # If this fires frequently add diagnostics for ranking_router
        return {"chunks": [], "answer": None, "error": "retrieval_failed", "detail": str(e)}

    # Build answer using fused ranked chunks
    ranked_results = ranked.get("results", [])[:top_k]
    context = "\n---\n".join([r.get("text_preview", "") for r in ranked_results])
    prompt = f"You are ZenGlow Assistant. Use context to answer.\nContext:\n{context}\nQuestion: {query}\nAnswer:"
    answer = get_edge_model_response(prompt)
    # Return legacy shape + new scoring metadata
    legacy_chunks = [
        {
            "id": r.get("chunk_id"),
            "chunk": r.get("text_preview"),
            "score": r.get("fused_score"),
            "ltr_score": r.get("ltr_score"),
            "conceptual_score": r.get("conceptual_score"),
            "distance": r.get("distance"),
        }
        for r in ranked_results
    ]
    return {
        "chunks": legacy_chunks,
        "answer": answer,
        "fusion_weights": ranked.get("fusion_weights"),
        "feature_schema_version": ranked.get("feature_schema_version"),
        "feature_names": ranked.get("feature_names"),
        "scoring_version": ranked.get("scoring_version"),
    }


@app.post("/rag/pipeline", response_model=RAGQueryResponse)
async def rag_pipeline_endpoint(payload: RAGQueryRequest, pipeline: RAGPipeline = Depends(get_rag_pipeline)) -> RAGQueryResponse:
    answer = pipeline.run(query=payload.query, top_k=payload.top_k)
    # For now we don't surface chunk scores since db_client stub doesn't provide them
    return RAGQueryResponse(answer=answer, chunks=[])
