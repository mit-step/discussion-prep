import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import DATABASE_PATH



def bm25_search(query, db_path, top_k=5):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    """
    CREATE TABLE IF NOT EXISTS embeddings_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_uuid TEXT NOT NULL UNIQUE,
            doc_uuid TEXT NOT NULL,
            source_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    try:
        cursor.execute("""
            SELECT m.id, m.chunk_uuid, m.doc_uuid, m.source_type, m.content, m.metadata,
                   bm25(embeddings_fts) AS score
            FROM embeddings_fts
            JOIN embeddings_meta m ON m.id = embeddings_fts.rowid
            WHERE embeddings_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """, (query, top_k))
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    finally:
        conn.close()
    return results