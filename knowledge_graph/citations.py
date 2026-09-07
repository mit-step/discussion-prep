import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "rag_hybrid" / "data" / "mvp.db"
OUT = Path(__file__).resolve().parent / "graph_raw.json"

PARTY = r"[A-Z][\w.'&-]*(?:\s+(?:of|the|for|and)?\s*[A-Z][\w.'&-]*){0,5}"
CASE = re.compile(r"\b(" + PARTY + r")\s+v\.?\s+(" + PARTY + r")")

REPORTER = re.compile(
    r"\b(\d+)\s+"
    r"(U\.\s?S\.|S\.\s?Ct\.|F\.\s?Supp\.(?:\s?\d[a-z]{0,2})?|F\.\s?\d[a-z]{0,2}|"
    r"Cal\.\s?App\.\s?\d[a-z]{0,2}|Mass\.|N\.E\.\s?\d[a-z]{0,2}|LCR|NRC)\s+"
    r"(\d+)\b"
)

# Words that show up capitalized around a citation and get swept into the
# party name. "See Kelo v. City of New London" should yield "Kelo v. City of
# New London", not be thrown away, so these get stripped rather than used to
# reject the match.
CASE_NOISE = {
    "the", "court", "id", "see", "supra", "note", "cf", "compare", "but",
    "accord", "e.g", "eg", "ibid", "infra", "no", "in", "at", "of", "and",
    "also", "citing", "quoting", "overruled", "aff'd", "rev'd", "cert",
    "denied", "held", "holding", "cited", "cites", "here", "this", "that",
}

# ------------------------------------------------------------ authorities ---

# canonical name -> patterns that mean it
AUTHORITIES = {
    "Clean Air Act": [
        r"Clean Air Act", r"\bCAA\b", r"42\s+U\.\s?S\.\s?C\.\s*§+\s*74\d\d",
    ],
    "Clean Water Act": [
        r"Clean Water Act", r"\bCWA\b", r"Federal Water Pollution Control Act",
        r"33\s+U\.\s?S\.\s?C\.\s*§+\s*13\d\d",
    ],
    "National Environmental Policy Act": [
        r"National Environmental Policy Act", r"\bNEPA\b",
        r"42\s+U\.\s?S\.\s?C\.\s*§+\s*43\d\d", r"40\s+C\.\s?F\.\s?R\.\s*§*\s*150\d",
    ],
    "Endangered Species Act": [r"Endangered Species Act", r"\bESA\b"],
    "Administrative Procedure Act": [r"Administrative Procedure Act", r"\bAPA\b"],
    "CERCLA": [
        r"CERCLA", r"Comprehensive Environmental Response",
        r"Superfund",
    ],
    "Massachusetts Environmental Policy Act": [
        r"Massachusetts Environmental Policy Act", r"\bMEPA\b",
    ],
    "Fair Housing Act": [r"Fair Housing Act", r"\bFHA\b"],
    "Civil Rights Act Title VI": [
        r"Title\s+VI", r"Civil Rights Act",
    ],
    "Executive Order 12898": [r"Executive Order\s+12,?898", r"\bE\.?O\.?\s+12,?898"],

    # constitutional provisions
    "Fifth Amendment": [r"Fifth Amendment"],
    "Takings Clause": [r"Takings Clause"],
    "Public Use Clause": [r"Public Use Clause"],
    "Due Process Clause": [r"Due Process Clause"],
    "Equal Protection Clause": [r"Equal Protection Clause"],
    "Commerce Clause": [r"Commerce Clause"],
    "Tenth Amendment": [r"Tenth Amendment"],
    "Eleventh Amendment": [r"Eleventh Amendment"],
    "Fourteenth Amendment": [r"Fourteenth Amendment"],
    "Article III standing": [r"Article\s+III"],
}

AUTH_COMPILED = {
    name: [re.compile(p, re.IGNORECASE if len(p) > 8 else 0) for p in pats]
    for name, pats in AUTHORITIES.items()
}


def normalize(s):
    return " ".join(s.split()).rstrip(".,;: ")


def short_key(case_name):
    """'kelo' from 'Kelo v. City of New London'."""
    return normalize(case_name).split()[0].rstrip(".,").lower()


def strip_noise(party):
    """Drop leading and trailing filler swept in by the party pattern."""
    words = normalize(party).split()
    while words and words[0].lower().rstrip(".,") in CASE_NOISE:
        words.pop(0)
    while words and words[-1].lower().rstrip(".,") in CASE_NOISE:
        words.pop()
    return " ".join(words)


def cases_in(text):
    out = []
    for m in CASE.finditer(text):
        left = strip_noise(m.group(1))
        right = strip_noise(m.group(2))
        if len(left) < 3 or len(right) < 3:
            continue
        name = left + " v. " + right
        tail = text[m.end():m.end() + 90]
        rep = REPORTER.search(tail)
        out.append((name, normalize(rep.group(0)) if rep else None))
    return out


def authorities_in(text):
    hits = set()
    for name, pats in AUTH_COMPILED.items():
        for p in pats:
            if p.search(text):
                hits.add(name)
                break
    return hits


def corpus_index(conn):
    """Map a lookup key to doc_uuid for each assigned reading."""
    index, docs = {}, {}
    for r in conn.execute("""
        SELECT DISTINCT doc_uuid, json_extract(metadata, '$.filename') AS fn
        FROM embeddings_meta
    """):
        fn = r["fn"] or ""
        docs[r["doc_uuid"]] = fn
        clean = fn.replace("_", " ").replace(".pdf", "").replace(".PDF", "")
        clean = clean.replace(".DOCX", "").replace(".docx", "")
        m = CASE.search(clean)
        if m:
            index[short_key(m.group(1))] = r["doc_uuid"]
        else:
            first = clean.split()[0].lower().rstrip(".,") if clean.split() else ""
            if first:
                index.setdefault(first, r["doc_uuid"])
    return index, docs


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    index, docs = corpus_index(conn)
    print(str(len(docs)) + " documents, " + str(len(index)) + " lookup keys")

    case_edges = defaultdict(int)     # (src, case_name) -> count
    auth_edges = defaultdict(int)     # (src, authority)  -> count
    reporters = {}

    for r in conn.execute("SELECT doc_uuid, content FROM embeddings_meta"):
        src = r["doc_uuid"]
        for name, rep in cases_in(r["content"]):
            case_edges[(src, name)] += 1
            if rep and name not in reporters:
                reporters[name] = rep
        for a in authorities_in(r["content"]):
            auth_edges[(src, a)] += 1

    edges, external = [], defaultdict(int)
    for (src, name), count in case_edges.items():
        tgt = index.get(short_key(name))
        if tgt and tgt != src:
            edges.append({"source": src, "target": tgt, "type": "cites",
                          "label": name, "in_corpus": True, "weight": count})
        elif not tgt:
            external[name] += count
            edges.append({"source": src, "target": "case:" + short_key(name),
                          "type": "cites", "label": name,
                          "in_corpus": False, "weight": count})

    for (src, auth), count in auth_edges.items():
        edges.append({"source": src, "target": "auth:" + auth, "type": "invokes",
                      "label": auth, "in_corpus": False, "weight": count})

    print(str(len(edges)) + " edges")

    print()
    print("--- authorities, by how many documents invoke them")
    per_auth = defaultdict(int)
    for (src, auth) in auth_edges:
        per_auth[auth] += 1
    for a, n in sorted(per_auth.items(), key=lambda t: -t[1]):
        print("  " + str(n) + " docs  " + a)

    print()
    print("--- top cited cases NOT in the corpus")
    for name, c in sorted(external.items(), key=lambda t: -t[1])[:30]:
        print("  " + str(c).rjust(4) + "  " + name + "   " + reporters.get(name, ""))

    OUT.write_text(json.dumps({
        "documents": docs, "edges": edges, "reporters": reporters,
    }, indent=2))
    print()
    print("wrote " + str(OUT))


if __name__ == "__main__":
    main()