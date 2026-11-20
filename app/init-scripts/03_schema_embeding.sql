-- ========================================================
-- 03_schema_embeding.sql
-- Schéma et tables pour l'embedding
-- ========================================================

CREATE SCHEMA IF NOT EXISTS embedding;

CREATE TABLE IF NOT EXISTS embedding.repo_embeddings (
    repository_id  VARCHAR(100) PRIMARY KEY
                       REFERENCES github.repositories(id) ON DELETE CASCADE,
    embedding      vector(768) NOT NULL,   
    text_hash      CHAR(64)    NOT NULL, 
    model_name     VARCHAR(100) NOT NULL DEFAULT 'intfloat/multilingual-e5-base',
    embedded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- À exécuter APRÈS le chargement des vecteurs (beaucoup plus rapide ainsi).
-- CREATE INDEX IF NOT EXISTS idx_repo_embeddings_hnsw
--     ON embedding.repo_embeddings
--     USING hnsw (embedding vector_cosine_ops);
-- ANALYZE embedding.repo_embeddings;