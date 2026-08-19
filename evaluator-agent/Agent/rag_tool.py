import json
import sys
from pathlib import Path

_RAG_HYBRID_ROOT = Path(__file__).resolve().parents[2] / "rag_hybrid"
_DB_PATH = _RAG_HYBRID_ROOT / "data" / "mvp.db"

sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "retrieval"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src" / "ingestion"))
sys.path.insert(0, str(_RAG_HYBRID_ROOT / "src"))

from search import hybrid_search  # noqa: E402
from embed import generate_embedding  # noqa: E402


def check_groundedness(claim_text: str, top_k: int = 3) -> list[dict]:
    if not _DB_PATH.exists():
        return []
    query_embedding = generate_embedding(claim_text)
    results = hybrid_search(str(_DB_PATH), claim_text, query_embedding, top_k=top_k)
    return [{"content": row["content"], "metadata": row["metadata"]} for row, _ in results]


def extract_source_docs(grounding: list[dict]) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for row in grounding:
        try:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            fname = meta.get("filename")
            if fname and fname not in seen:
                names.append(fname)
                seen.add(fname)
        except (json.JSONDecodeError, TypeError):
            pass
    return names
