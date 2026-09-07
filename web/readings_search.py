from __future__ import annotations

import sys
from pathlib import Path

_RAG_HYBRID_ROOT = Path(__file__).resolve().parent.parent / "rag_hybrid"
_DB_PATH = _RAG_HYBRID_ROOT / "data" / "mvp.db"

sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "retrieval"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "ingestion"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src"))

from search import connect, hybrid_search  # noqa: E402
from vector import vector_search  # noqa: E402
from lexical import bm25_search  # noqa: E402
from embed import generate_embedding  # noqa: E402
from config import READING_SEARCH_CHUNK_POOL, READING_SEARCH_MAX_DISTANCE  # noqa: E402

import db  # noqa: E402


def search_readings(query: str, user_id: str) -> list[dict]:
    """Reading-level hybrid search: aggregate chunk-level RRF scores up to their
    parent doc_uuid (max score wins — avoids favoring longer documents) for
    ranking, but GATE admissibility on a real relevance signal (a keyword hit
    or a genuinely close vector match) rather than pure rank — a nearest-
    neighbor search always returns a "closest" result even for a nonsense
    query, so rank alone can't tell relevant from irrelevant. Readings that
    clear neither signal are hidden entirely, not reordered/de-emphasized."""
    if not _DB_PATH.exists() or not query.strip():
        return []

    embedding = generate_embedding(query)

    fused_pool = hybrid_search(str(_DB_PATH), query, embedding, top_k=READING_SEARCH_CHUNK_POOL, doc_uuid=None)
    if not fused_pool:
        return []

    conn = connect(str(_DB_PATH))
    vector_pool = vector_search(conn, embedding, top_k=READING_SEARCH_CHUNK_POOL)
    conn.close()
    lexical_pool = bm25_search(query, str(_DB_PATH), top_k=READING_SEARCH_CHUNK_POOL)

    min_distance_by_doc: dict[str, float] = {}
    for row in vector_pool:
        doc_uuid = row["doc_uuid"]
        min_distance_by_doc[doc_uuid] = min(min_distance_by_doc.get(doc_uuid, float("inf")), row["distance"])
    lexical_hit_docs = {row["doc_uuid"] for row in lexical_pool}

    doc_scores: dict[str, float] = {}
    for row, score in fused_pool:
        doc_uuid = row["doc_uuid"]
        doc_scores[doc_uuid] = max(doc_scores.get(doc_uuid, 0.0), score)

    admissible = [
        doc_uuid
        for doc_uuid in doc_scores
        if doc_uuid in lexical_hit_docs or min_distance_by_doc.get(doc_uuid, float("inf")) <= READING_SEARCH_MAX_DISTANCE
    ]
    admissible.sort(key=lambda d: doc_scores[d], reverse=True)

    catalog_by_uuid = {r["doc_uuid"]: r for r in db.list_readings_catalog()}
    ordered_readings = [catalog_by_uuid[u] for u in admissible if u in catalog_by_uuid]

    return db.readings_with_evaluations(user_id, ordered_readings)
