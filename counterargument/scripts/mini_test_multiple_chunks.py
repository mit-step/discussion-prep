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

doc = '8b357591-bb70-4999-a43c-1fb31061e8d6'

rows = conn.execute("""
    SELECT chunk_uuid, content FROM embeddings_meta
    WHERE doc_uuid = ? ORDER BY id LIMIT 20 OFFSET 100 
""", (doc,)).fetchall()

empty = 0
for r in rows:
    ws = extract_warrants(r["content"])
    print("---", r["content"][:90].replace("\n", " "), "...")
    if not ws:
        empty += 1
        print("    (none)")
    for w in ws:
        print(f"    [{w.relation.value}/{w.held_by.value}] {w.warrant_text}")
        

print("\nempty: " + str(empty) + "/" + str(len(rows)))

# r = conn.execute("""
#     SELECT content, json_extract(metadata, '$.page_no') p
#     FROM embeddings_meta WHERE doc_uuid = ? ORDER BY id DESC LIMIT 1
# """, (doc,)).fetchone()
# print(r["p"])
# print(r["content"][-400:])