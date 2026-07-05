"""SQLite access: schema and a per-request connection dependency."""

import sqlite3

from config import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    params_json TEXT NOT NULL,
    plan_json   TEXT NOT NULL,
    share_token TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_trips_share ON trips(share_token);
"""

# Additive migrations for databases created before a column existed.
MIGRATIONS = [
    ("trips", "share_token", "ALTER TABLE trips ADD COLUMN share_token TEXT"),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        for table, column, ddl in MIGRATIONS:
            if conn.execute(f"SELECT 1 FROM sqlite_master WHERE name = ?",
                            (table,)).fetchone():
                cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
                if column not in cols:
                    conn.execute(ddl)
        conn.executescript(SCHEMA)


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
