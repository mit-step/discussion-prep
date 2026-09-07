import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_conn
from retrieve import find_parallel

QUERY = "A taking that produces a public benefit qualifies as a public use."

conn = get_conn()
print("query: " + QUERY)
print(conn.execute("SELECT COUNT(*) FROM reading_warrant_fts").fetchone()[0])

for mode in ("lexical", "dense", "hybrid"):
    print()
    print("=" * 60)
    print(mode)
    hits = find_parallel(conn, QUERY, mode=mode)
    if not hits:
        print("  nothing")
    for h in hits:
        print("  [" + h["reaction"] + " rule:" + h["rule_from"] +
              " reacts:" + h["reaction_from"] + "] " + str(round(h["score"], 5)))
        print("    " + h["warrant_text"])