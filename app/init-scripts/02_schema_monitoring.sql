-- ========================================================
-- 02_schema_monitoring.sql
-- Schéma et tables pour le monitoring des API et quotas
-- ========================================================

CREATE SCHEMA IF NOT EXISTS monitoring;

-- --------------------------------------------------------
-- monitoring.rate_limit_usage
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS monitoring.rate_limit_usage (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    limit_value     INTEGER,
    remaining       INTEGER,
    used            INTEGER,
    cost            INTEGER,
    reset_at        TIMESTAMP,
    operation_name  VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_timestamp ON monitoring.rate_limit_usage(timestamp);

