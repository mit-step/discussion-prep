import sqlite3
import sys
from pathlib import Path

import sqlite_vec

HERE = Path(__file__).resolve().parent
DB_PATH = HERE.parent / "rag_hybrid" / "data" / "mvp.db"
SCHEMA_PATH = HERE / "schema.sql"

EMBED_DIM = 384


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def apply_schema(conn):
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS reading_warrant_vec USING vec0("
        "warrant_id TEXT PRIMARY KEY, embedding float[" + str(EMBED_DIM) + "])"
    )
    conn.commit()


def drop_warrants(conn):
    """Wipe the derived tables so they can be rebuilt after a prompt change."""
    conn.executescript("""
        DROP TABLE IF EXISTS reading_warrant_fts;
        DROP TABLE IF EXISTS reading_warrant_vec;
        DROP TABLE IF EXISTS reading_warrant;
    """)
    conn.commit()
    apply_schema(conn)