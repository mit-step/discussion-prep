from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
sys.path.append(str(HERE.parent / "rag_hybrid" / "src"))

from ingestion.embed import generate_embeddings

import uuid
import sqlite_vec



from db import get_conn, apply_schema
from warrant import extract_warrants

def pending_chunks(conn, doc_uuid=None, limit=None):
    SKIP_FILES = (
        "Devillier v Texas (2024) cropped.pdf",
        "Mass v EPA 2007 549_U.S._497 Excerpts.pdf",
        "Land Use Law and Envtl Law Syllabus 2022.pdf",
    )
    sql = """
        SELECT m.chunk_uuid, m.doc_uuid, m.content
        FROM embeddings_meta m
        LEFT JOIN reading_warrant w ON w.chunk_uuid = m.chunk_uuid
        WHERE w.chunk_uuid IS NULL
    """
    sql += " AND json_extract(m.metadata, '$.filename') NOT IN (?, ?, ?)"
    params = []
    params.extend(SKIP_FILES)
   
    if doc_uuid:
        sql += " AND m.doc_uuid = ?"
        params.append(doc_uuid)
    sql += " GROUP BY m.chunk_uuid ORDER BY m.id"
    if limit:
        sql += " LIMIT " + str(int(limit))
    return conn.execute(sql, params).fetchall()


def store(conn, chunk, warrants):
    if not warrants:
        return
    vectors = generate_embeddings([w.warrant_text for w in warrants])
    with conn:
        for w, vec in zip(warrants, vectors):
            wid = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO reading_warrant
                (warrant_id, chunk_uuid, doc_uuid, warrant_text,
                applied_to, conclusion, reaction, rule_from, reaction_from)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (wid, chunk["chunk_uuid"], chunk["doc_uuid"], w.warrant_text,
                w.applied_to, w.conclusion, w.reaction.value,
                w.rule_from.value, w.reaction_from.value),
            )
            conn.execute(
                "INSERT INTO reading_warrant_fts (warrant_text, warrant_id) VALUES (?, ?)",
                (w.warrant_text, wid),
            )
            conn.execute(
                "INSERT INTO reading_warrant_vec (warrant_id, embedding) VALUES (?, ?)",
                (wid, sqlite_vec.serialize_float32(vec)),
            )


def run(doc_uuid=None, limit=None):
    conn = get_conn()
    apply_schema(conn)

    chunks = pending_chunks(conn, doc_uuid, limit)
    print(str(len(chunks)) + " chunks to process")

    empty = 0
    failed = 0
    for i, chunk in enumerate(chunks, 1):
        try:
            warrants = extract_warrants(chunk["content"])
        except Exception as e:
            failed += 1
            print("  chunk " + chunk["chunk_uuid"] + " failed: " + repr(e))
            continue

        if not warrants:
            empty += 1
        store(conn, chunk, warrants)

        if i % 25 == 0:
            print("  " + str(i) + "/" + str(len(chunks)))

    total = conn.execute("SELECT COUNT(*) c FROM reading_warrant").fetchone()["c"]
    print("done. empty " + str(empty) + ", failed " + str(failed) +
          ", warrants in table " + str(total))


if __name__ == "__main__":
    doc = 'efb97db0-43ef-4e21-847f-812ad27ebad2'
    # lim = 20
    run()
