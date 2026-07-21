-- Digital Thread POC — Knowledge Store schema
-- Design rule: Documents and AuditLog are APPEND-ONLY. Never UPDATE/DELETE a row's content;
-- superseded documents get status='superseded', new revisions get a new row.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Parts (
    part_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    part_no     TEXT NOT NULL UNIQUE,
    description TEXT,
    supplier    TEXT,
    assembly_id INTEGER REFERENCES Parts(part_id),  -- nullable: NULL = top-level assembly
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS Documents (
    doc_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id       INTEGER NOT NULL REFERENCES Parts(part_id),
    doc_type      TEXT NOT NULL CHECK (doc_type IN ('MBD','MBOM','NC','SOP')),
    source_ref    TEXT NOT NULL,     -- local file path in PoC -> Windchill doc ID in production
    revision      TEXT,
    date_received TEXT NOT NULL DEFAULT (datetime('now')),
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','rejected'))
);

CREATE TABLE IF NOT EXISTS Relationships (
    parent_part_id INTEGER NOT NULL REFERENCES Parts(part_id),
    child_part_id  INTEGER NOT NULL REFERENCES Parts(part_id),
    bom_level      INTEGER NOT NULL DEFAULT 1,
    qty            REAL NOT NULL DEFAULT 1,
    PRIMARY KEY (parent_part_id, child_part_id)
);

CREATE TABLE IF NOT EXISTS Versions (
    version_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES Documents(doc_id),
    version_no  TEXT NOT NULL,
    changed_by  TEXT,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    change_note TEXT
);

CREATE TABLE IF NOT EXISTS AuditLog (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
    user_id     TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('submit','reject','ingest','query','retrieve')),
    target_id   TEXT,
    result      TEXT
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    role    TEXT NOT NULL CHECK (role IN ('Engineer','ShopFloor','QA','Admin'))
);

CREATE INDEX IF NOT EXISTS idx_documents_part ON Documents(part_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON Documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON Documents(status);
