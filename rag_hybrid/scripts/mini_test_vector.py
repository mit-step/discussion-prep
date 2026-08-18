import os
import sys
from pathlib import Path

folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'ingestion'))
retrieval_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'retrieval'))
sys.path.insert(0, folder_path)
sys.path.insert(0, retrieval_path)

import sqlite3
import sqlite_vec
from embed import generate_embedding 
from vector import vector_search
from lexical import bm25_search

DB_PATH = Path(folder_path) / "mvp.db"


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def print_results(query, results, score_key="distance"):
    print(f"\nQuery: '{query}'  ->  {len(results)} results")
    for r in results:
        preview = r["content"][:80].replace("\n", " ")
        print(f"  {score_key}={r[score_key]:.4f}  \"{preview}...\"")


def test_vector_search():
    assert DB_PATH.exists(), f"No db found at {DB_PATH}, run index.py first"
    conn = connect(DB_PATH)

    # trival case: a chunk should retrieve itself as the nearest neighbor with k=1
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM embeddings_meta LIMIT 1")
    sample = cursor.fetchone()
    sample_embedding = generate_embedding(sample["content"])
    results = vector_search(conn, sample_embedding, top_k=1)
    assert len(results) == 1, "Expected exactly 1 result for top_k=1"
    assert results[0]["id"] == sample["id"], "Chunk's own text didn't retrieve itself as nearest match"
    assert results[0]["distance"] < 0.01, f"Expected near-zero self-distance, got {results[0]['distance']}"
    print(f"Self-retrieval check passed, distance={results[0]['distance']:.6f}")

    semantic_query = "government taking private land for a business project"
    query_embedding = generate_embedding(semantic_query)
    vec_results = vector_search(conn, query_embedding, top_k=5)
    assert len(vec_results) > 0, "Expected results for semantic query, got none"
    print_results(semantic_query, vec_results)

    #how does the top BM25 result compare to the top vector result?
    lex_results = bm25_search(semantic_query, str(DB_PATH), top_k=5)
    print(f"\nSame query via BM25: {len(lex_results)} results")
    for r in lex_results:
        print(f"  score={r['score']:.4f}  \"{r['content'][:80]}...\"")
    

    # Making sure distances should be non-negative and ascending
    distances = [r["distance"] for r in vec_results]
    assert all(d >= 0 for d in distances), f"Found negative cosine distance: {distances}"
    assert distances == sorted(distances), f"Distances not in ascending order: {distances}"

    # Making sure that <=k are returned
    results_limited = vector_search(conn, query_embedding, top_k=2)
    assert len(results_limited) <= 2, f"Expected at most 2 results, got {len(results_limited)}"

    conn.close()
    print("\nAll checks passed.")


if __name__ == "__main__":
    test_vector_search()