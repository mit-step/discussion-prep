import sqlite3
import struct
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
sys.path.append(str(_SRC))


def serialize_embedding(embedding: list[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def vector_search(conn, query_embedding: list[float], top_k: int = 100):
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("""
            SELECT m.id, m.chunk_uuid, m.doc_uuid, m.source_type, m.content, m.metadata,
                   v.distance
            FROM vec_embeddings v
            JOIN embeddings_meta m ON m.id = v.rowid
            WHERE v.embedding MATCH ?
            AND k = ?
            ORDER BY v.distance
        """, (serialize_embedding(query_embedding), top_k))
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    return results