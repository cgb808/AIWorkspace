-- Vector & dedupe performance indexes
-- IVF FLAT index (adjust lists upward as row count grows: ~sqrt(N) heuristic)
CREATE INDEX IF NOT EXISTS doc_embeddings_embedding_ivf
ON doc_embeddings
USING ivfflat (embedding vector_l2_ops)
WITH (lists=100);

-- Optional future HNSW (uncomment when pgvector build supports it)
-- CREATE INDEX IF NOT EXISTS doc_embeddings_embedding_hnsw
-- ON doc_embeddings
-- USING hnsw (embedding vector_l2_ops)
-- WITH (m=16, ef_construction=64);

-- Expression index for JSONB metadata content hash lookups (if using metadata pathway)
CREATE INDEX IF NOT EXISTS doc_embeddings_metadata_content_hash_idx
ON doc_embeddings ((metadata->>'content_hash'));

-- NOTE: A direct btree index on content_hash column (idx_doc_embeddings_content_hash)
-- may already exist from earlier migration; retaining both allows flexibility
-- while transitioning ingestion to populate the dedicated column.
