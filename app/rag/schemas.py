"""Pydantic schemas for RAG API and DB rows."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RAGQueryRequest(BaseModel):
	query: str = Field(..., description="User natural language question")
	top_k: int = Field(5, ge=1, le=50, description="Number of context chunks")


class RetrievedChunk(BaseModel):
	text: str
	metadata: Optional[Dict[str, Any]] = None
	score: Optional[float] = None


class RAGQueryResponse(BaseModel):
	answer: str
	chunks: List[RetrievedChunk] = []
