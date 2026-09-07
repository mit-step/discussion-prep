import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from warrant import extract_warrants

DB = HERE.parent.parent / "rag_hybrid" / "data" / "mvp.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

for r in conn.execute("""
    SELECT doc_uuid, COUNT(*) n, json_extract(metadata, '$.filename') f
    FROM embeddings_meta
    WHERE f LIKE '%McFarlane%' OR f LIKE '%Rebuilding%'
    GROUP BY doc_uuid
"""):
    print(r["doc_uuid"], r["n"], r["f"])