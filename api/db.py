"""Database access: Postgres in production, SQLite for local dev and tests.

If DATABASE_URL is set (Railway injects it when a Postgres service is
attached), a psycopg connection pool is used and data survives redeploys.
Otherwise the original SQLite file is used — zero local setup, fast tests.

Routers write one dialect: '?' placeholders and mapping-style rows. The thin
Db wrapper translates placeholders for Postgres; sqlite3.Row and psycopg's
dict_row both support row["column"]. Always bind values as parameters
(Python bools for is_admin etc.) so both backends store them correctly.
"""

import os
import sqlite3

from config import db_path

DATABASE_URL = os.environ.get("DATABASE_URL", "")
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

if IS_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
    IntegrityError = psycopg.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError

_SCHEMA_SQLITE = [
    """CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY,
        email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
        name          TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin      INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS trips (
        id          INTEGER PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name        TEXT NOT NULL,
        params_json TEXT NOT NULL,
        plan_json   TEXT NOT NULL,
        share_token TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_trips_share ON trips(share_token)",
]

# created_at kept TEXT in UTC for identical string-comparison semantics
# across both backends (sessions.expires_at is compared with < as text).
_SCHEMA_POSTGRES = [
    """CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         TEXT NOT NULL UNIQUE,
        name          TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin      BOOLEAN NOT NULL DEFAULT FALSE,
        created_at    TEXT NOT NULL
            DEFAULT (to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD HH24:MI:SS'))
    )""",
    """CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS trips (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name        TEXT NOT NULL,
        params_json TEXT NOT NULL,
        plan_json   TEXT NOT NULL,
        share_token TEXT,
        created_at  TEXT NOT NULL
            DEFAULT (to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD HH24:MI:SS'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_trips_share ON trips(share_token)",
]

# Additive migrations for SQLite databases created before a column existed
# (SQLite has no ADD COLUMN IF NOT EXISTS; Postgres baseline already has them).
_MIGRATIONS_SQLITE = [
    ("trips", "share_token", "ALTER TABLE trips ADD COLUMN share_token TEXT"),
    ("users", "is_admin",
     "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"),
]


class Db:
    """Uniform connection facade over sqlite3 / psycopg."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        if IS_POSTGRES:
            sql = sql.replace("?", "%s")
        return self._conn.execute(sql, params)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def insert_id(db: Db, sql: str, params=()) -> int:
    """INSERT and return the new row id on either backend."""
    if IS_POSTGRES:
        return db.execute(sql + " RETURNING id", params).fetchone()["id"]
    return db.execute(sql, params).lastrowid


_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(DATABASE_URL, min_size=0, max_size=5,
                               kwargs={"row_factory": dict_row})
    return _pool


def _connect_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    if IS_POSTGRES:
        with _get_pool().connection() as conn:
            for ddl in _SCHEMA_POSTGRES:
                conn.execute(ddl)
        return
    db_path().parent.mkdir(parents=True, exist_ok=True)
    conn = _connect_sqlite()
    try:
        for table, column, ddl in _MIGRATIONS_SQLITE:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name = ?",
                            (table,)).fetchone():
                cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
                if column not in cols:
                    conn.execute(ddl)
        for ddl in _SCHEMA_SQLITE:
            conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """FastAPI dependency: one connection per request.

    Commits on success; an exception skips the commit (Postgres rolls back
    via the pool context manager, SQLite discards on close).
    """
    if IS_POSTGRES:
        with _get_pool().connection() as conn:
            yield Db(conn)
    else:
        conn = _connect_sqlite()
        try:
            yield Db(conn)
            conn.commit()
        finally:
            conn.close()
