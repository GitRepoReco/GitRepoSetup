-- ========================================================
-- 00_extensions.sql
-- Active les extensions PostgreSQL recommandées pour GitRepoReco
-- ========================================================

-- Support des identifiants UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Recherche textuelle avancée, trigrammes et similarité textuelle
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Support des embeddings vectoriels pour les recommandations (pgvector)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'vector'
    ) THEN
        CREATE EXTENSION IF NOT EXISTS "vector";
        RAISE NOTICE 'Extension vector (pgvector) activée avec succès.';
    ELSE
        RAISE NOTICE 'Extension vector non disponible sur cette image PostgreSQL, ignorée.';
    END IF;
END $$;

