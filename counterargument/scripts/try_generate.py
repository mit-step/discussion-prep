import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_conn
from student import extract_turn
from retrieve import find_parallel
from generate import generate_challenge, clean_source

TURNS = [
    "The New London taking was fine. Berman let them clear slums, and this is "
    "the same thing, the city gets jobs and tax revenue out of it.",

    "I don't think economic development should count as public use at all. "
    "Just saying a project creates jobs can't be enough, or the government "
    "could take anyone's house for anything.",
]

conn = get_conn()

for turn in TURNS:
    print("=" * 70)
    print(turn)
    t = extract_turn(turn)
    if not t:
        print("  no argument")
        continue
    print()
    print("  claim:   " + t.claim)
    print("  warrant: " + t.warrant_text)
    print("  stance:  " + t.stance.value)

    hits = find_parallel(conn, t.warrant_text, stance=t.stance.value, k_final=2)
    for h in hits:
        print()
        print("  --- [" + h["reaction"] + "] " + clean_source(h.get("filename")))
        print(generate_challenge(t.warrant_text, h, stance=t.stance.value))