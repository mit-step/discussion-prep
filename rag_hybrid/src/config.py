from pathlib import Path

# config.py lives at rag_hybrid/src/, so parents[1] is rag_hybrid/
RAG_HYBRID_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = RAG_HYBRID_ROOT / "data"
RESOURCES_DIR = RAG_HYBRID_ROOT / "resources"

DATABASE_PATH = DATA_DIR / "mvp.db"
EMBEDDING_DIM = 384