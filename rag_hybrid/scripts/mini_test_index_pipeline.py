import os
import sys
import sqlite3
from pathlib import Path
import re


TEST_DB_PATH = Path(__file__).parent / "test_mvp.db"
_ROOT = Path(__file__).resolve().parents[1] 
sys.path.append(str(_ROOT / "src"))
sys.path.append(str(_ROOT / "src" / "ingestion"))
sys.path.append(str(_ROOT / "src" / "retrieval"))
from config import DATABASE_PATH as DB_PATH


def cleanup(db_path):
    if db_path.exists():
        db_path.unlink()


def test_index_pipeline():
    cleanup(TEST_DB_PATH)
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'ingestion'))
    sys.path.append(folder_path)

    import index

    try:
        db = index.main(db_path=TEST_DB_PATH)

        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) AS c FROM embeddings_meta")
        meta_count = cursor.fetchone()["c"]
        assert meta_count > 0, "No rows inserted into embeddings_meta"
        print(f"embeddings_meta: {meta_count} rows")

       
        cursor.execute("SELECT COUNT(*) AS c FROM vec_embeddings")
        vec_count = cursor.fetchone()["c"]
        assert vec_count == meta_count, (
            f"vec_embeddings count ({vec_count}) != embeddings_meta count ({meta_count})"
        )
        print(f"vec_embeddings: {vec_count} rows")

        
        cursor.execute("SELECT COUNT(*) AS c FROM embeddings_fts")
        fts_count = cursor.fetchone()["c"]
        assert fts_count == meta_count, (
            f"embeddings_fts count ({fts_count}) != embeddings_meta count ({meta_count})"
        )
        print(f"embeddings_fts: {fts_count} rows")

        cursor.execute("SELECT content FROM embeddings_meta LIMIT 1")
        sample_text = cursor.fetchone()["content"]
        words = re.findall(r"[A-Za-z]+", sample_text)
        sample_word = next((w for w in words if len(w) > 3), words[0])

        cursor.execute("""
            SELECT m.id, m.content, bm25(embeddings_fts) AS score
            FROM embeddings_fts
            JOIN embeddings_meta m ON m.id = embeddings_fts.rowid
            WHERE embeddings_fts MATCH ?
            ORDER BY score
            LIMIT 5
        """, (sample_word,))
        fts_results = cursor.fetchall()
        assert len(fts_results) > 0, f"FTS search for '{sample_word}' returned no results"
        print(f"FTS search for '{sample_word}': {len(fts_results)} results")

       
        cursor.execute("SELECT chunk_uuid, content FROM embeddings_meta LIMIT 1")
        row = cursor.fetchone()
        sample_embedding = index.generate_embedding(row["content"])

        cursor.execute("""
            SELECT m.id, m.content, v.distance
            FROM vec_embeddings v
            JOIN embeddings_meta m ON m.id = v.rowid
            WHERE v.embedding MATCH ?
            AND k = ?
            ORDER BY v.distance
        """, (index.serialize_embedding(sample_embedding), 5))
        vec_results = cursor.fetchall()
        assert len(vec_results) > 0, "Vector search returned no results"
        assert vec_results[0]["distance"] < 0.01, (
            f"Expected near-zero self-distance, got {vec_results[0]['distance']}"
        )
        print(f"Vector search: {len(vec_results)} results, "
              f"top match distance={vec_results[0]['distance']:.4f}")

        db.close()
        print("\nAll checks passed.")

    finally:
        cleanup(TEST_DB_PATH)


if __name__ == "__main__":
    test_index_pipeline()
    # print(TEST_DB_PATH)