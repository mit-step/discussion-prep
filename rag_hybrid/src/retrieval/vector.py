def vector_search(conn, query_embedding: list[float], top_k: int = 100):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT rowid, distance, content, source_type, doc_uuid
            FROM vec_embeddings
            WHERE embedding MATCH ?
            AND k = ?
            ORDER BY distance
        """, (serialize_embedding(query_embedding), top_k))

        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []
    return results


