-- ========================================================
-- 01_schema_github.sql
-- Schéma et tables pour le collecteur de données Analyse-github
-- ========================================================

CREATE SCHEMA IF NOT EXISTS github;

-- --------------------------------------------------------
-- github.repositories — état courant de chaque repo
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS github.repositories (
    id                   VARCHAR(100) PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL,
    full_name            VARCHAR(255) UNIQUE NOT NULL,
    description          TEXT,
    url                  TEXT,
    homepage_url         TEXT,
    open_graph_image_url TEXT,
    stars                INTEGER NOT NULL DEFAULT 0,
    forks                INTEGER NOT NULL DEFAULT 0,
    disk_usage_kb        INTEGER,
    visibility           VARCHAR(20),
    is_archived          BOOLEAN DEFAULT FALSE,
    is_fork              BOOLEAN DEFAULT FALSE,
    is_template          BOOLEAN DEFAULT FALSE,
    is_disabled          BOOLEAN DEFAULT FALSE,
    is_mirror            BOOLEAN DEFAULT FALSE,
    mirror_url           TEXT,
    has_issues           BOOLEAN,
    has_wiki             BOOLEAN,
    has_discussions      BOOLEAN,
    merge_commit_allowed   BOOLEAN,
    squash_merge_allowed   BOOLEAN,
    rebase_merge_allowed   BOOLEAN,
    delete_branch_on_merge BOOLEAN,
    language             VARCHAR(100),
    language_color       VARCHAR(10),
    default_branch       VARCHAR(100),
    owner_login          VARCHAR(255),
    owner_avatar_url     TEXT,
    license_spdx_id      VARCHAR(50),
    license_name         VARCHAR(255),
    ssh_url              TEXT,
    parent_full_name     VARCHAR(255),
    parent_url           TEXT,
    code_of_conduct_name VARCHAR(255),
    code_of_conduct_url  TEXT,
    topics               TEXT[],
    languages            JSONB,
    total_releases       INTEGER,
    total_issues_open    INTEGER,
    total_issues_closed  INTEGER,
    total_prs_open       INTEGER,
    total_prs_merged     INTEGER,
    total_watchers       INTEGER,
    created_at           TIMESTAMP,
    updated_at           TIMESTAMP,
    pushed_at            TIMESTAMP,
    last_seen_commit_sha VARCHAR(100),
    last_commit_date     TIMESTAMP,
    last_checked_at      TIMESTAMP,
    collected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repositories_stars ON github.repositories(stars);
CREATE INDEX IF NOT EXISTS idx_repositories_language ON github.repositories(language);
CREATE INDEX IF NOT EXISTS idx_repositories_updated_at ON github.repositories(updated_at);
CREATE INDEX IF NOT EXISTS idx_repositories_last_checked ON github.repositories(last_checked_at);

-- --------------------------------------------------------
-- github.readmes — historique des README par commit
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS github.readmes (
    id              BIGSERIAL PRIMARY KEY,
    repository_id   VARCHAR(100) NOT NULL
                        REFERENCES github.repositories(id),
    commit_sha      VARCHAR(100) NOT NULL,
    content         TEXT,
    collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, commit_sha)
);

CREATE INDEX IF NOT EXISTS idx_readmes_repository_id ON github.readmes(repository_id);

-- --------------------------------------------------------
-- github.repository_snapshots — évolution dans le temps
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS github.repository_snapshots (
    id                  BIGSERIAL PRIMARY KEY,
    repository_id       VARCHAR(100) NOT NULL
                            REFERENCES github.repositories(id),
    commit_sha          VARCHAR(100),
    snapshot_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stars               INTEGER,
    forks               INTEGER,
    watchers            INTEGER,
    total_issues_open   INTEGER,
    total_issues_closed INTEGER,
    total_prs_open      INTEGER,
    total_prs_merged    INTEGER,
    total_releases      INTEGER,
    description         TEXT,
    language            VARCHAR(100),
    topics              TEXT[],
    is_archived         BOOLEAN,
    homepage_url        TEXT,
    disk_usage_kb       INTEGER
);

CREATE INDEX IF NOT EXISTS idx_snapshots_repository_at
    ON github.repository_snapshots(repository_id, snapshot_at);

-- --------------------------------------------------------
-- github.collection_progress — reprise pagination historique
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS github.collection_progress (
    id               BIGSERIAL PRIMARY KEY,
    phase            VARCHAR(100) NOT NULL,
    segment_key      TEXT,
    tier_low         INTEGER NOT NULL,
    tier_high        INTEGER,
    date_low         DATE,
    date_high        DATE,
    sort_order       VARCHAR(50) NOT NULL,
    search_query     TEXT NOT NULL,
    cursor           TEXT,
    completed        BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_progress_segment_unique
    ON github.collection_progress(phase, segment_key, sort_order);

CREATE INDEX IF NOT EXISTS idx_collection_progress_lookup
    ON github.collection_progress(phase, tier_low, tier_high, completed);

