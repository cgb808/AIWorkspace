"""
Tests for FastAPI health endpoints and RAG query stub.
Run with pytest.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_root():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_health_ollama():
    resp = client.get("/health/ollama")
    assert resp.status_code == 200
    assert "ollama" in resp.json()

def test_health_db():
    resp = client.get("/health/db")
    assert resp.status_code == 200
    assert "db" in resp.json()

def test_rag_pipeline_endpoint_missing_query():
    resp = client.post("/rag/pipeline", json={})
    # Pydantic validation error -> 422
    assert resp.status_code == 422

def test_rag_pipeline_endpoint_basic():
    resp = client.post("/rag/pipeline", json={"query": "What is ZenGlow?", "top_k": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "chunks" in data
