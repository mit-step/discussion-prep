import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from lexical import bm25_search
from vector import vector_search
from config import DATABASE_PATH

import sqlite_vec

def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

def weighted_rrf(vector_res, lexical_res, top_k=10, smoothing_param=60, weights=None):
    if weights is None:
        weights = {'rank_v': 0.7, 'rank_l': 1.0}

    lexical_ranks = {row['id']: rank for rank, row in enumerate(lexical_res, start=1)}
    vector_ranks = {row['id']: rank for rank, row in enumerate(vector_res, start=1)}

    all_chunk_data = {row['id']: row for row in vector_res}
    all_chunk_data.update({row['id']: row for row in lexical_res})

    scores = []
    for chunk_id in all_chunk_data:
        score = 0.0
        if chunk_id in vector_ranks:
            score += weights['rank_v'] * (1 / (smoothing_param + vector_ranks[chunk_id]))
        if chunk_id in lexical_ranks:
            score += weights['rank_l'] * (1 / (smoothing_param + lexical_ranks[chunk_id]))
        scores.append((all_chunk_data[chunk_id], score))

    return sorted(scores, key=lambda t: t[1], reverse=True)[:top_k]

def hybrid_search(db_path, query_text, query_embedding, smoothing_param=60, top_k=5):
    conn = connect(db_path)
    vector_results = vector_search(conn, query_embedding, top_k=top_k)
    lexical_results = bm25_search(query_text, db_path, top_k=top_k)
    conn.close()
    rrf_scores = weighted_rrf(vector_results, lexical_results, top_k=top_k, smoothing_param=smoothing_param)
    return rrf_scores
