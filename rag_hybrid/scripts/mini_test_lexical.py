import os
import sys
from pathlib import Path

folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'ingestion'))
retrieval_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'retrieval'))
sys.path.append(folder_path)
sys.path.append(retrieval_path)

from lexical import bm25_search

DB_PATH = Path(folder_path) / "mvp.db"


def print_results(query, results):
    print(f"\nQuery: '{query}'  ->  {len(results)} results")
    for r in results:
        preview = r["content"][:80].replace("\n", " ")
        print(f"  score={r['score']:.4f}  page={r['doc_uuid'][:8]}...  \"{preview}...\"")


def test_bm25_search():
    assert DB_PATH.exists(), f"No db found at {DB_PATH}, run index.py first"

    #We know 'takings' is in the sample data, so we should get results for it
    results = bm25_search("takings", str(DB_PATH), top_k=5)
    assert len(results) > 0, "Expected results for 'takings', got none"
    print_results("takings", results)

    #should input the entire chunk text, but for now just checks that the top result contains the word 'taking'
    top_content = results[0]["content"].lower()
    assert "taking" in top_content, (
        f"Top result doesn't contain 'taking' in content: {top_content[:100]}"
    )

    # whatever was returned should be in ascending order of score (more negative = better match)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores), f"Scores not in ascending order: {scores}"

    # A silly query that shouldn't match anything should return an empty list
    results_empty = bm25_search("zzzxyznotarealword", str(DB_PATH), top_k=5)
    assert results_empty == [], f"Expected no results for nonsense query, got {len(results_empty)}"

    # Makes sure that <=k are returned
    results_limited = bm25_search("the", str(DB_PATH), top_k=2)
    assert len(results_limited) <= 2, f"Expected at most 2 results, got {len(results_limited)}"

    print("\nAll checks passed.")


if __name__ == "__main__":
    test_bm25_search()