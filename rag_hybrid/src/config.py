from pathlib import Path

# config.py lives at rag_hybrid/src/, so parents[1] is rag_hybrid/
RAG_HYBRID_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = RAG_HYBRID_ROOT / "data"
RESOURCES_DIR = RAG_HYBRID_ROOT / "resources"

DATABASE_PATH = DATA_DIR / "mvp.db"
EMBEDDING_DIM = 384

# --- RRF fusion (retrieval/search.py::weighted_rrf) ---
RRF_WEIGHT_VECTOR = 0.7
RRF_WEIGHT_LEXICAL = 1.0
RRF_SMOOTHING = 60

# --- vector search over-fetch when filtering by doc_uuid (retrieval/vector.py) ---
# sqlite-vec's `k = ?` constraint picks nearest neighbors from the whole table
# BEFORE any WHERE filter, so a doc_uuid filter needs a wider net cast first.
VECTOR_OVERFETCH_MULTIPLIER = 20
VECTOR_OVERFETCH_MIN = 200

# --- per-reading Socratic/evaluation grounding (rag_tool.py::check_groundedness) ---
GROUNDING_TOP_K_PRIMARY = 3   # chunks pulled from the assigned reading
GROUNDING_TOP_K_OTHER = 5     # pool size for the cross-reference search
GROUNDING_MAX_OTHER = 2       # cross-reference chunks kept after excluding the primary reading

# --- library search-box aggregation (web/readings_search.py) ---
READING_SEARCH_CHUNK_POOL = 150
# Admissibility gate: a nearest-neighbor vector search always returns SOME
# "closest" chunk even for a nonsense query, so a purely rank-relative cutoff
# can't tell "somewhat relevant" from "not relevant at all". A reading only
# surfaces if it has a real BM25 keyword hit, or its closest chunk's cosine
# distance is below this value. Empirically calibrated on this corpus: a
# genuinely on-topic query clusters around ~0.36-0.40, unrelated/nonsense
# input around ~0.67-0.69 — 0.5 sits cleanly between them.
READING_SEARCH_MAX_DISTANCE = 0.5