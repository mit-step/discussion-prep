import sqlite3
import struct
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
sys.path.append(str(_SRC))

from config import VECTOR_OVERFETCH_MIN, VECTOR_OVERFETCH_MULTIPLIER


def serialize_embedding(embedding: list[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def vector_search(conn, query_embedding: list[float], top_k: int = 100, doc_uuid=None):
    cursor = conn.cursor()
    results = []
    # sqlite-vec's `k = ?` picks nearest neighbors from the WHOLE table before
    # any WHERE filter runs, so a doc_uuid filter needs a wider net cast first,
    # then LIMIT trims back down to top_k after filtering.
    fetch_k = top_k if doc_uuid is None else max(top_k * VECTOR_OVERFETCH_MULTIPLIER, VECTOR_OVERFETCH_MIN)

    sql = """
        SELECT m.id, m.chunk_uuid, m.doc_uuid, m.source_type, m.content, m.metadata,
               v.distance
        FROM vec_embeddings v
        JOIN embeddings_meta m ON m.id = v.rowid
        WHERE v.embedding MATCH ?
        AND k = ?
    """
    params = [serialize_embedding(query_embedding), fetch_k]
    if doc_uuid:
        sql += " AND m.doc_uuid = ?"
        params.append(doc_uuid)
    sql += " ORDER BY v.distance LIMIT ?"
    params.append(top_k)

    try:
        cursor.execute(sql, params)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    return results