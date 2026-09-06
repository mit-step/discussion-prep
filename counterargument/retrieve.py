import re
import sqlite3
import sys
from pathlib import Path

import sqlite_vec

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
sys.path.append(str(HERE.parent / "rag_hybrid" / "src"))

from ingestion.embed import generate_embedding

_FTS_STRIP = re.compile(r"[^\w\s]")


def sanitize_fts(text):
    """FTS5 MATCH throws on punctuation, and warrants have commas and periods."""
    return " ".join(_FTS_STRIP.sub(" ", text).split())


def warrant_bm25(conn, query, top_k=40):
    terms = sanitize_fts(query).split()
    STOP = {"a", "an", "the", "that", "is", "as", "of", "to", "in", "if",
            "and", "or", "it", "its", "for", "by", "on", "when", "does", "not"}
    terms = [t for t in terms if t.lower() not in STOP and len(t) > 2]
    if not terms:
        return []
    q = " OR ".join(terms)
    try:
        return conn.execute("""
            SELECT f.warrant_id AS id, bm25(reading_warrant_fts) AS score
            FROM reading_warrant_fts f
            WHERE reading_warrant_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """, (q, top_k)).fetchall()
    except sqlite3.Error as e:
        print("FTS error: " + str(e))
        return []


def warrant_vector(conn, query_embedding, top_k=40):
    try:
        return conn.execute("""
            SELECT warrant_id AS id, distance
            FROM reading_warrant_vec
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
        """, (sqlite_vec.serialize_float32(query_embedding), top_k)).fetchall()
    except sqlite3.Error as e:
        print("vec error: " + str(e))
        return []


def weighted_rrf(vector_res, lexical_res, smoothing_param=60, weights=None):
    """
    Same shape as rag_hybrid's, weights flipped. Groundedness checking wants
    exact terms, so lexical dominates there. Warrant matching wants the same
    rule stated in different vocabulary, so dense dominates here.
    """
    if weights is None:
        weights = {"rank_v": 1.0, "rank_l": 0.7}

    v_ranks = {r["id"]: i for i, r in enumerate(vector_res, start=1)}
    l_ranks = {r["id"]: i for i, r in enumerate(lexical_res, start=1)}

    scores = {}
    for wid in set(v_ranks) | set(l_ranks):
        s = 0.0
        if wid in v_ranks:
            s += weights["rank_v"] / (smoothing_param + v_ranks[wid])
        if wid in l_ranks:
            s += weights["rank_l"] / (smoothing_param + l_ranks[wid])
        scores[wid] = s
    return scores


def find_parallel(conn, warrant_text, k_candidates=40, k_final=5,
                  reactions=("refused", "distinguished"),
                  exclude_chunk_ids=None, mode="hybrid", weights=None):
    """
    mode: 'hybrid', 'dense', or 'lexical'. Run all three on one query to see
    whether fusion earns its place on this corpus.

    k_candidates wide, k_final narrow on purpose: RRF has nothing to do when
    both lists are the same length as the output.
    """
    exclude_chunk_ids = set(exclude_chunk_ids or [])

    lexical = warrant_bm25(conn, warrant_text, k_candidates) if mode in ("hybrid", "lexical") else []
    vector = []
    if mode in ("hybrid", "dense"):
        vector = warrant_vector(conn, generate_embedding(warrant_text), k_candidates)

    scores = weighted_rrf(vector, lexical, weights=weights)
    if not scores:
        return []

    ids = list(scores.keys())
    ph = ",".join("?" * len(ids))
    rows = conn.execute(
        "SELECT w.*, m.content AS chunk_text, "
        "       json_extract(m.metadata, '$.filename') AS filename "
        "FROM reading_warrant w "
        "LEFT JOIN embeddings_meta m ON m.chunk_uuid = w.chunk_uuid "
        "WHERE w.warrant_id IN (" + ph + ")", ids
    ).fetchall()

    out = []
    for r in rows:
        d = dict(r)
        if d["chunk_uuid"] in exclude_chunk_ids:
            continue
        if reactions and d["reaction"] not in reactions:
            continue
        d["score"] = scores[d["warrant_id"]]
        out.append(d)

    out.sort(key=lambda d: d["score"], reverse=True)
    return out[:k_final]