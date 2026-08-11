import sqlite3
import struct
import json
from pathlib import Path
from chunk import 
from embedding import generate_embedding

import sqlite_vec

DATABASE_PATH = Path("mvp.db")
EMBEDDING_DIM = 384  


def init_database(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    cursor = conn.cursor()

    # for metadata and content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_uuid TEXT NOT NULL UNIQUE,
            doc_uuid TEXT NOT NULL,
            source_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # for vector embeddings, rowid shared with embeddings_meta.id
    cursor.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
            embedding float[{EMBEDDING_DIM}] distance_metric=cosine
        )
    """)

    # for full text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_fts USING fts5(
            content,
            source_type,
            doc_uuid,
            content='embeddings_meta',
            content_rowid='id'
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS embeddings_ai AFTER INSERT ON embeddings_meta BEGIN
            INSERT INTO embeddings_fts(rowid, content, source_type, doc_uuid)
            VALUES (new.id, new.content, new.source_type, new.doc_uuid);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS embeddings_ad AFTER DELETE ON embeddings_meta BEGIN
            INSERT INTO embeddings_fts(embeddings_fts, rowid, content, source_type, doc_uuid)
            VALUES ('delete', old.id, old.content, old.source_type, old.doc_uuid);
        END
    """)

    conn.commit()
    return conn

db = init_database(DATABASE_PATH)

def serialize_embedding(embedding):
    embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
    return embedding_bytes

def insert_chunk(conn, chunk_uuid, doc_uuid, source_type, content, embedding, extra_metadata=None):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO embeddings_meta (chunk_uuid, doc_uuid, source_type, content, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (chunk_uuid, doc_uuid, source_type, content, json.dumps(extra_metadata or {})),
    )
    row_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO vec_embeddings(rowid, embedding) VALUES (?, ?)",
        (row_id, serialize_embedding(embedding)),
    )
    conn.commit()
    return row_id


def main():
    db = init_database(DATABASE_PATH)
    for record in recorded_chunks:
        embedding = generate_embedding(record["text"]) 
        insert_chunk(
            db,
            chunk_uuid=record["chunk_uuid"],
            doc_uuid=record["doc_uuid"],
            source_type=record.get("source_type", "pdf"),
            content=record["text"],
            embedding=embedding,
            extra_metadata={
                "headings": record["headings"],
                "page_no": record["page_no"],
                "filename": record["filename"],
            },
        )
    return db


if __name__ == "__main__":
    main()



