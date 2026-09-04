import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "rag_hybrid" / "data" / "mvp.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("counts")
for r in conn.execute("""
    SELECT reaction, rule_from, reaction_from, COUNT(*) c
    FROM reading_warrant
    GROUP BY reaction, rule_from, reaction_from
    ORDER BY c DESC
"""):
    print("  " + r["reaction"] + " | rule:" + r["rule_from"] +
          " | reacts:" + r["reaction_from"] + " -> " + str(r["c"]))

print()
print("suspect combinations")
for r in conn.execute("""
    SELECT COUNT(*) c FROM reading_warrant
    WHERE rule_from='author' AND reaction_from='author' AND reaction='refused'
"""):
    print("  author refusing own rule (steelman): " + str(r["c"]))
for r in conn.execute("""
    SELECT COUNT(*) c FROM reading_warrant
    WHERE rule_from='other' AND reaction_from='author' AND reaction='applied'
"""):
    print("  author endorsing other's rule (may be split steelman): " + str(r["c"]))

print()
print("challenge pool")
for r in conn.execute("""
    SELECT warrant_text, reaction, rule_from, reaction_from
    FROM reading_warrant
    WHERE reaction IN ('refused', 'distinguished')
    LIMIT 25
"""):
    print("  [" + r["reaction"] + " rule:" + r["rule_from"] +
          " reacts:" + r["reaction_from"] + "]")
    print("    " + r["warrant_text"])