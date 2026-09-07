import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))

from citations import (
    authorities_in,
    cases_in,
    corpus_index,
    short_key,
)

DB = HERE.parent / "rag_hybrid" / "data" / "mvp.db"
OUT = HERE / "graph.html"

MIN_WEIGHT = 2       # edges below this are dropped
MAX_PER_DOC = 10     # top N citations kept per document
MIN_AUTH_DOCS = 3    # authorities invoked by fewer docs are dropped


def clean_title(filename):
    """Readable label from a filename."""
    t = filename
    for ext in (".pdf", ".PDF", ".docx", ".DOCX", ".doc"):
        t = t.replace(ext, "")
    t = t.replace("_", " ").replace("+", " ")
    t = re.sub(r"\s*\d+\s*S\.?Ct\.?\s*\d+", "", t)   # trailing reporter cite
    t = re.sub(r"\s+", " ", t).strip(" -,")
    return t


def collect(conn):
    index, docs = corpus_index(conn)

    case_hits = defaultdict(int)      # (src, name) -> count
    auth_hits = defaultdict(int)      # (src, authority) -> count
    reporters = {}                    # name -> reporter cite

    for r in conn.execute("SELECT doc_uuid, content FROM embeddings_meta"):
        src = r["doc_uuid"]
        for name, rep in cases_in(r["content"]):
            case_hits[(src, name)] += 1
            if rep and name not in reporters:
                reporters[name] = rep
        for a in authorities_in(r["content"]):
            auth_hits[(src, a)] += 1

    return index, docs, case_hits, auth_hits, reporters


def canonical_external(name, reporters):
    """
    Identity key for a case not in the corpus. The reporter cite is the real
    identity; fall back to first and last word when there is no cite.
    """
    rep = reporters.get(name)
    if rep:
        return "cite:" + re.sub(r"[^\w]", "", rep).lower()
    words = name.replace(" v. ", " ").split()
    if len(words) >= 2:
        return "name:" + (words[0] + words[-1]).lower()
    return "name:" + name.lower()


def assemble(index, docs, case_hits, auth_hits, reporters,
             min_weight, max_per_doc, min_auth_docs):
    """One projection of the same extraction. The two views differ only in
    these three thresholds, so any difference on screen is a filtering
    effect, not a different extraction."""

    ext_label, ext_count, raw_edges = {}, defaultdict(int), []

    for (src, name), count in case_hits.items():
        tgt = index.get(short_key(name))
        if tgt and tgt != src:
            raw_edges.append((src, tgt, count))
        elif not tgt:
            key = canonical_external(name, reporters)
            ext_count[(key, name)] += count
            raw_edges.append((src, key, count))

    for (key, name), c in sorted(ext_count.items(), key=lambda t: -t[1]):
        ext_label.setdefault(key, name)

    merged = defaultdict(int)
    for src, tgt, count in raw_edges:
        merged[(src, tgt)] += count

    per_doc = defaultdict(list)
    for (src, tgt), w in merged.items():
        if w >= min_weight:
            per_doc[src].append((tgt, w))

    links = []
    for src, targets in per_doc.items():
        targets.sort(key=lambda t: -t[1])
        for tgt, w in targets[:max_per_doc]:
            links.append({"source": src, "target": tgt,
                          "type": "cites", "weight": w})

    auth_docs = defaultdict(set)
    for (src, a) in auth_hits:
        auth_docs[a].add(src)
    keep_auth = {a for a, s in auth_docs.items() if len(s) >= min_auth_docs}

    for (src, a), w in auth_hits.items():
        if a in keep_auth:
            links.append({"source": src, "target": "auth:" + a,
                          "type": "invokes", "weight": w})

    used = {l["source"] for l in links} | {l["target"] for l in links}
    nodes = []
    for uuid, fn in docs.items():
        if uuid in used:
            nodes.append({"id": uuid, "label": clean_title(fn), "kind": "reading"})
    for key, name in ext_label.items():
        if key in used:
            nodes.append({"id": key, "label": name,
                          "cite": reporters.get(name, ""), "kind": "case"})
    for a in keep_auth:
        if "auth:" + a in used:
            nodes.append({"id": "auth:" + a, "label": a, "kind": "authority"})

    deg = defaultdict(int)
    for l in links:
        deg[l["source"]] += 1
        deg[l["target"]] += 1
    for n in nodes:
        n["degree"] = deg[n["id"]]

    return {"nodes": nodes, "links": links}


def build():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    parts = collect(conn)
    index, docs = parts[0], parts[1]

    return {
        "filtered": assemble(*parts, MIN_WEIGHT, MAX_PER_DOC, MIN_AUTH_DOCS),
        # Everything the extractor found. Deduping externals on their reporter
        # cite is kept in both views: two spellings of one case is a data bug,
        # not a filtering choice, so showing it would misrepresent the raw pass.
        "raw": assemble(*parts, 1, 10_000, 1),
        "thresholds": {"min_weight": MIN_WEIGHT,
                       "max_per_doc": MAX_PER_DOC,
                       "min_auth_docs": MIN_AUTH_DOCS},
    }


def main():
    data = build()
    for view in ("filtered", "raw"):
        d = data[view]
        counts = defaultdict(int)
        for n in d["nodes"]:
            counts[n["kind"]] += 1
        print(view + ": " + str(len(d["nodes"])) + " nodes, "
              + str(len(d["links"])) + " edges  ("
              + ", ".join(str(v) + " " + k for k, v in sorted(counts.items())) + ")")

    template = (HERE / "graph_template.html").read_text()
    html = template.replace("/*__GRAPH_DATA__*/null", json.dumps(data))
    OUT.write_text(html)
    print("wrote " + str(OUT))


if __name__ == "__main__":
    main()