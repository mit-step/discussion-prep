import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "rag_hybrid" / "data" / "mvp.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

for r in conn.execute("""
    SELECT COUNT(*) n, json_extract(metadata, '$.filename') f
    FROM embeddings_meta GROUP BY doc_uuid ORDER BY f
"""):
    print(r["n"], r["f"])