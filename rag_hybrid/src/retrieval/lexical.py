import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import DATABASE_PATH

import re

_FTS_STRIP = re.compile(r"[^\w\s]")

# FTS5 MATCH parses its argument as a query expression, so punctuation in
# free text (case citations, quotes, apostrophes) is a syntax error. Callers
# pass raw student text and article prose, so strip it here rather than at
# every call site.
_STOP = {"a", "an", "the", "that", "is", "as", "of", "to", "in", "if",
         "and", "or", "it", "its", "for", "by", "on", "when", "does", "not"}


def _fts_query(text):
    terms = _FTS_STRIP.sub(" ", text).split()
    terms = [t for t in terms if t.lower() not in _STOP and len(t) > 2]
    return " OR ".join(terms)



def bm25_search(query, db_path, top_k=5, doc_uuid=None):
    query = _fts_query(query)
    if not query:
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT m.id, m.chunk_uuid, m.doc_uuid, m.source_type, m.content, m.metadata,
               bm25(embeddings_fts) AS score
        FROM embeddings_fts
        JOIN embeddings_meta m ON m.id = embeddings_fts.rowid
        WHERE embeddings_fts MATCH ?
    """
    params = [query]
    if doc_uuid:
        sql += " AND embeddings_fts.doc_uuid = ?"
        params.append(doc_uuid)
    sql += " ORDER BY score LIMIT ?"
    params.append(top_k)

    try:
        cursor.execute(sql, params)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    finally:
        conn.close()
    return results