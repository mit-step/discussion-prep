import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]  # rag_hybrid/
sys.path.append(str(_ROOT / "src"))
sys.path.append(str(_ROOT / "src" / "ingestion"))
sys.path.append(str(_ROOT / "src" / "retrieval"))

from search import weighted_rrf, hybrid_search
from embed import generate_embedding
from config import DATABASE_PATH as DB_PATH



def fake_row(id_, content="dummy content"):
    return {"id": id_, "content": content}


def test_rrf_chunk_in_both_lists_scores_highest():
    vector_res = [fake_row("a"), fake_row("b"), fake_row("x")]
    lexical_res = [fake_row("a"), fake_row("c"), fake_row("y")]

    results = weighted_rrf(vector_res, lexical_res, top_k=10, smoothing_param=60)
    top_id = results[0][0]["id"]
    assert top_id == "a", f"Expected chunk 'a' (in both lists) to rank first, got '{top_id}'"


def test_rrf_all_chunks_present_none_dropped():
    vector_res = [fake_row("a"), fake_row("b")]
    lexical_res = [fake_row("c"), fake_row("d")]

    results = weighted_rrf(vector_res, lexical_res, top_k=10)
    returned_ids = {row["id"] for row, score in results}
    assert returned_ids == {"a", "b", "c", "d"}, f"Missing chunks: {{'a','b','c','d'}} - {returned_ids}"


def test_rrf_respects_top_k():
    vector_res = [fake_row(str(i)) for i in range(10)]
    lexical_res = [fake_row(str(i)) for i in range(10, 20)]

    results = weighted_rrf(vector_res, lexical_res, top_k=3)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"


def test_rrf_scores_descending():
    vector_res = [fake_row("a"), fake_row("b"), fake_row("c")]
    lexical_res = [fake_row("b"), fake_row("a"), fake_row("d")]

    results = weighted_rrf(vector_res, lexical_res, top_k=10)
    scores = [score for row, score in results]
    assert scores == sorted(scores, reverse=True), f"Scores not descending: {scores}"


def test_rrf_weights_actually_change_ranking():
    # chunk 'a' ranks 1st in vector, 5th in lexical. chunk 'b' ranks 5th in vector, 1st in lexical.
    # heavily favoring lexical should flip which one comes out on top.
    vector_res = [fake_row("a")] + [fake_row(f"v{i}") for i in range(4)] + [fake_row("b")]
    lexical_res = [fake_row("b")] + [fake_row(f"l{i}") for i in range(4)] + [fake_row("a")]

    lexical_favored = weighted_rrf(
        vector_res, lexical_res, top_k=10,
        weights={"rank_v": 0.1, "rank_l": 1.0},
    )
    assert lexical_favored[0][0]["id"] == "b", "Expected lexical-favoring weights to rank 'b' first"

    vector_favored = weighted_rrf(
        vector_res, lexical_res, top_k=10,
        weights={"rank_v": 1.0, "rank_l": 0.1},
    )
    assert vector_favored[0][0]["id"] == "a", "Expected vector-favoring weights to rank 'a' first"


def test_hybrid_search_end_to_end():
    assert DB_PATH.exists(), f"No db found at {DB_PATH}, run index.py first"

    query_text = "government taking private land for a business project"
    query_embedding = generate_embedding(query_text)

    results = hybrid_search(str(DB_PATH), query_text, query_embedding, top_k=5)

    assert len(results) > 0, "Expected at least one fused result"
    assert len(results) <= 5, f"Expected at most 5 results, got {len(results)}"

    scores = [score for row, score in results]
    assert scores == sorted(scores, reverse=True), f"Fused scores not descending: {scores}"

    print(f"\nQuery: '{query_text}'")
    for row, score in results:
        preview = row["content"][:80].replace("\n", " ")
        print(f"  rrf_score={score:.5f}  \"{preview}...\"")


if __name__ == "__main__":
    test_rrf_chunk_in_both_lists_scores_highest()
    test_rrf_all_chunks_present_none_dropped()
    test_rrf_respects_top_k()
    test_rrf_scores_descending()
    test_rrf_weights_actually_change_ranking()
    print("weighted_rrf unit tests passed.")

    test_hybrid_search_end_to_end()
    print("hybrid_search end-to-end test passed.")