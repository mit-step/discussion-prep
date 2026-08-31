# Run: .venv/bin/python -m pytest web/tests/test_grounding_scope.py -v
# (or: .venv/bin/python web/tests/test_grounding_scope.py to run without pytest)
#
# Guards the single most correctness-sensitive change in the reading-library
# refactor: once a student picks a reading, the Socratic agent's "primary"
# grounding must never leak chunks from other documents, and "other" must
# never silently duplicate the primary reading.

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "evaluator-agent"))

from Agent import rag_tool  # noqa: E402


def _sample_doc_uuids(n=3):
    import sqlite3

    db_path = _REPO_ROOT / "rag_hybrid" / "data" / "mvp.db"
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT DISTINCT doc_uuid FROM embeddings_meta LIMIT ?", (n,)).fetchall()
    conn.close()
    return [r[0] for r in rows]


def test_primary_chunks_scoped_to_doc_uuid():
    doc_uuids = _sample_doc_uuids(3)
    assert doc_uuids, "mvp.db has no ingested documents — run ingestion first"

    for doc_uuid in doc_uuids:
        grounding = rag_tool.check_groundedness("standing doctrine and injury in fact", primary_doc_uuid=doc_uuid)
        assert all(row["doc_uuid"] == doc_uuid for row in grounding["primary"]), (
            f"primary grounding leaked a chunk from another document for doc_uuid={doc_uuid}"
        )
        assert all(row["doc_uuid"] != doc_uuid for row in grounding["other"]), (
            f"other grounding duplicated the primary reading for doc_uuid={doc_uuid}"
        )


def test_no_reading_selected_falls_back_to_cross_corpus():
    grounding = rag_tool.check_groundedness("standing doctrine and injury in fact", primary_doc_uuid=None)
    assert grounding["primary"] == []


if __name__ == "__main__":
    test_primary_chunks_scoped_to_doc_uuid()
    test_no_reading_selected_falls_back_to_cross_corpus()
    print("ok")
