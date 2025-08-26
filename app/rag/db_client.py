"""
DB Client for Vector Search (pgvector, Timescale)
"""
from typing import List, Dict, Any
import psycopg2
import psycopg2.extras
import os

class DBClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("PG_DB", "rag_db"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "password"),
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432"))
        )
        self.conn.autocommit = True

    def close(self):
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def vector_search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query pgvector for top-k similar documents.

        Returns list of dicts: {id, text, metadata, distance}
        Score is deliberately NOT computed here so it can be derived conceptually
        at response time based on current recency/weighting strategies.
        Assumes table schema: id, text, metadata JSONB, embedding vector.
        """
        if not embedding:
            return []
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, text, metadata, (embedding <-> %s)::float AS distance
                FROM doc_embeddings
                ORDER BY embedding <-> %s
                LIMIT %s
                """,
                (embedding, embedding, top_k),
            )
            rows = cur.fetchall() or []
            return [
                {
                    "id": r.get("id"),
                    "text": r.get("text"),
                    "metadata": r.get("metadata"),
                    "distance": r.get("distance") or 0.0,
                }
                for r in rows
            ]
