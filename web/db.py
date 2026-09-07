from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

# app.db is the web app's OWN database (users, transcripts) — separate from
# rag_hybrid/data/mvp.db, which is the RAG team's ingestion artifact and gets
# rebuilt whenever they re-run ingestion. Never write to mvp.db from here.
APP_DATA_DIR = Path(__file__).resolve().parent / "data"
APP_DB_PATH = APP_DATA_DIR / "app.db"

MVP_DB_PATH = Path(__file__).resolve().parent.parent / "rag_hybrid" / "data" / "mvp.db"
READINGS_DIR = Path(__file__).resolve().parent.parent / "rag_hybrid" / "resources" / "readings"


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def app_connect() -> sqlite3.Connection:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _connect(APP_DB_PATH)


def mvp_connect() -> sqlite3.Connection:
    return _connect(MVP_DB_PATH)

def mvp_connect_vec() -> sqlite3.Connection:
    """mvp.db with sqlite-vec loaded, for warrant retrieval. Read-only."""
    import sqlite_vec
    conn = _connect(MVP_DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def init_app_db() -> None:
    with app_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    TEXT PRIMARY KEY,
                email      TEXT UNIQUE NOT NULL,
                name       TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                session_id  TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                reading_id  TEXT NOT NULL,
                argument    TEXT NOT NULL,
                exchanges   TEXT NOT NULL,
                evaluation  TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transcripts_user_reading "
            "ON transcripts(user_id, reading_id, created_at DESC)"
        )


# --- users (demo auth placeholder — see get_current_user_id in app.py) ---

def get_or_create_user(name: str, email: str) -> sqlite3.Row:
    email = email.strip().lower()
    name = name.strip()
    with app_connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, email, name) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), email, name),
        )
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user(user_id: str) -> sqlite3.Row | None:
    with app_connect() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


# --- transcripts ---

def save_transcript(
    session_id: str,
    user_id: str,
    reading_id: str,
    argument: str,
    exchanges: list[dict],
    evaluation: dict,
) -> None:
    with app_connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO transcripts
               (session_id, user_id, reading_id, argument, exchanges, evaluation)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, reading_id, argument, json.dumps(exchanges), json.dumps(evaluation)),
        )


def get_transcript(session_id: str, user_id: str) -> sqlite3.Row | None:
    with app_connect() as conn:
        return conn.execute(
            "SELECT * FROM transcripts WHERE session_id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()


def list_reading_history(user_id: str, reading_id: str) -> list[sqlite3.Row]:
    with app_connect() as conn:
        return conn.execute(
            "SELECT session_id, evaluation, created_at FROM transcripts "
            "WHERE user_id = ? AND reading_id = ? ORDER BY created_at DESC",
            (user_id, reading_id),
        ).fetchall()


def latest_evaluations_for_user(user_id: str) -> dict[str, sqlite3.Row]:
    """Most recent transcript per reading_id for this user."""
    with app_connect() as conn:
        rows = conn.execute(
            """
            SELECT t.reading_id, t.evaluation, t.created_at
            FROM transcripts t
            WHERE t.user_id = ?
              AND t.created_at = (
                  SELECT MAX(t2.created_at) FROM transcripts t2
                  WHERE t2.user_id = t.user_id AND t2.reading_id = t.reading_id
              )
            """,
            (user_id,),
        ).fetchall()
    return {row["reading_id"]: row for row in rows}


def summarize_evaluation(evaluation: dict) -> dict:
    """Plain numeric summary of an evaluation JSON — no LLM call."""
    pillars = evaluation.get("overall_reasoning") or {}
    scores = [p["score"] for p in pillars.values()]
    overall_mean = round(sum(scores) / len(scores), 2) if scores else None

    rubric = evaluation.get("rubric_alignment") or []
    rubric_total = sum(item["points_awarded"] for item in rubric) if rubric else None
    rubric_max = sum(item["max_points"] for item in rubric) if rubric else None

    return {"overall_mean": overall_mean, "rubric_total": rubric_total, "rubric_max": rubric_max}


# --- readings catalog (reads mvp.db only, never writes) ---

def list_readings_catalog() -> list[dict]:
    """One row per distinct doc_uuid in mvp.db, derived at query time."""
    if not MVP_DB_PATH.exists():
        return []
    with mvp_connect() as conn:
        rows = conn.execute(
            "SELECT doc_uuid, MIN(metadata) AS metadata FROM embeddings_meta GROUP BY doc_uuid"
        ).fetchall()

    catalog = []
    for row in rows:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        filename = meta.get("filename", row["doc_uuid"])
        title = Path(filename).stem.replace("_", " ").strip()
        catalog.append({
            "doc_uuid": row["doc_uuid"],
            "filename": filename,
            "title": title,
            "has_pdf": (READINGS_DIR / f"{row['doc_uuid']}.pdf").exists(),
        })
    catalog.sort(key=lambda r: r["title"].lower())
    return catalog


def get_reading(doc_uuid: str) -> dict | None:
    for reading in list_readings_catalog():
        if reading["doc_uuid"] == doc_uuid:
            return reading
    return None


def readings_with_evaluations(user_id: str, readings: list[dict] | None = None) -> list[dict]:
    """Attach each reading's latest-evaluation preview for this user. Preserves
    the order of `readings` if given (e.g. relevance-ranked search results)."""
    if readings is None:
        readings = list_readings_catalog()
    latest = latest_evaluations_for_user(user_id)

    result = []
    for reading in readings:
        row = latest.get(reading["doc_uuid"])
        result.append({
            **reading,
            "latest_evaluation": json.loads(row["evaluation"]) if row else None,
            "latest_attempt_at": row["created_at"] if row else None,
        })
    return result
