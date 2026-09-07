CREATE TABLE IF NOT EXISTS reading_warrant (
    warrant_id    TEXT PRIMARY KEY,
    chunk_uuid    TEXT NOT NULL,
    doc_uuid      TEXT NOT NULL,

    warrant_text  TEXT NOT NULL,


    applied_to    TEXT,
    conclusion    TEXT,

    rule_from      TEXT NOT NULL CHECK (rule_from IN ('court','author','other')),
    reaction_from  TEXT NOT NULL CHECK (reaction_from IN ('court','author','other')),
    reaction       TEXT NOT NULL CHECK (reaction IN ('applied','refused','distinguished')),

    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rw_chunk ON reading_warrant(chunk_uuid);
CREATE INDEX IF NOT EXISTS idx_rw_doc ON reading_warrant(doc_uuid);
CREATE INDEX IF NOT EXISTS idx_rw_reaction ON reading_warrant(reaction, reaction_from);


CREATE VIRTUAL TABLE IF NOT EXISTS reading_warrant_fts USING fts5(
  warrant_text,
  warrant_id UNINDEXED
);