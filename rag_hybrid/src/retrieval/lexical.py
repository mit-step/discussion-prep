import sqlite3

DATABASE_PATH = Path("mvp.db")
EMBEDDING_DIM = 384  

def bm25_search(query,db_path,top_k=5):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            SELECT id, chunk_uuid, doc_uuid, source_type, content, metadata,
                bm25(embeddings_fts) AS score
            FROM embeddings_fts
            WHERE embeddings_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """, (query, top_k))

        results = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.close()
        return []
    return results