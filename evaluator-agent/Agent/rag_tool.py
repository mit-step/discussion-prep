import sys
from pathlib import Path

# rag_hybrid uses flat, same-directory imports, so lexical.py is only
# importable with its own directory on sys.path.
_RAG_RETRIEVAL_PATH = Path(__file__).resolve().parents[2] / "rag_hybrid" / "src" / "retrieval"
sys.path.insert(0, str(_RAG_RETRIEVAL_PATH))
from lexical import bm25_search  # noqa: E402

_DB_PATH = Path(__file__).resolve().parents[2] / "rag_hybrid" / "src" / "ingestion" / "mvp.db"


def check_groundedness(claim_text: str, top_k: int = 3) -> list[dict]:
    if not _DB_PATH.exists():
        return []
    return [dict(row) for row in bm25_search(claim_text, str(_DB_PATH), top_k=top_k)]
