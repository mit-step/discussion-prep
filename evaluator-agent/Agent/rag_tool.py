from __future__ import annotations

import sys
from pathlib import Path

_RAG_HYBRID_ROOT = Path(__file__).resolve().parents[2] / "rag_hybrid"
_DB_PATH = _RAG_HYBRID_ROOT / "data" / "mvp.db"

sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "retrieval"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "ingestion"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src"))

from search import hybrid_search  # noqa: E402
from embed import generate_embedding  # noqa: E402
from config import (  # noqa: E402
    GROUNDING_MAX_OTHER,
    GROUNDING_TOP_K_OTHER,
    GROUNDING_TOP_K_PRIMARY,
)


def _rows_to_dicts(results: list) -> list[dict]:
    return [
        {"content": row["content"], "metadata": row["metadata"], "doc_uuid": row["doc_uuid"]}
        for row, _ in results
    ]


def check_groundedness(
    claim_text: str,
    primary_doc_uuid: str | None = None,
    top_k_primary: int = GROUNDING_TOP_K_PRIMARY,
    top_k_other: int = GROUNDING_TOP_K_OTHER,
    max_other: int = GROUNDING_MAX_OTHER,
) -> dict[str, list[dict]]:
    """Two-tier grounding: `primary` is scoped to the assigned reading (if any),
    `other` is a small cross-corpus pool (excluding the primary reading) so the
    agent can still reference/dispute using other course materials like a real
    discussion partner, while staying anchored to the assigned reading."""
    if not _DB_PATH.exists():
        return {"primary": [], "other": []}

    query_embedding = generate_embedding(claim_text)

    primary = []
    if primary_doc_uuid:
        primary_results = hybrid_search(
            str(_DB_PATH), claim_text, query_embedding, top_k=top_k_primary, doc_uuid=primary_doc_uuid
        )
        primary = _rows_to_dicts(primary_results)

    pool_results = hybrid_search(str(_DB_PATH), claim_text, query_embedding, top_k=top_k_other, doc_uuid=None)
    other = [d for d in _rows_to_dicts(pool_results) if d["doc_uuid"] != primary_doc_uuid][:max_other]

    return {"primary": primary, "other": other}
