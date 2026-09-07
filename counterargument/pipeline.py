import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))

from student import extract_turn
from retrieve import find_parallel
from generate import generate_challenge


def challenge_for(conn, student_text, exclude_chunk_ids=None):
    """Returns a dict with the challenge and its provenance, or None.

    None means fall through to the normal Socratic question: either the turn
    carried no argument, or nothing in the readings opposes it. Never force a
    challenge.
    """
    try:
        t = extract_turn(student_text)
        if not t:
            return None

        hits = find_parallel(conn, t.warrant_text, stance=t.stance.value,
                             k_final=1, exclude_chunk_ids=exclude_chunk_ids)
        if not hits:
            return None

        h = hits[0]
        text = generate_challenge(t.warrant_text, h, stance=t.stance.value)
        if not text:
            return None

        return {
            "text": text,
            "claim": t.claim,
            "warrant": t.warrant_text,
            "stance": t.stance.value,
            "source_doc": h["doc_uuid"],
            "source_chunk": h["chunk_uuid"],
            "source_name": h.get("filename"),
            "reaction": h["reaction"],
        }
    except Exception as e:
        print("counterargument failed: " + repr(e))
        return None