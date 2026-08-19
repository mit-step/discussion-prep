import json
import sqlite3
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Agent/, Schemas/, Parley/ are flat top-level packages under evaluator-agent/,
# same as evaluator-agent/Agent/rag_tool.py reaches into rag_hybrid/.
_EVALUATOR_AGENT_PATH = Path(__file__).resolve().parent.parent / "evaluator-agent"
sys.path.insert(0, str(_EVALUATOR_AGENT_PATH))

from Agent.rag_tool import check_groundedness, extract_source_docs  # noqa: E402
from Agent.socratic_agent import SocraticAgent  # noqa: E402
from Schemas.schemas import SocraticExchange, StudentArgument  # noqa: E402

ROUNDS = 3
STATIC_DIR = Path(__file__).resolve().parent / "static"
_DB_PATH = Path(__file__).resolve().parent.parent / "rag_hybrid" / "data" / "mvp.db"


# --- database helpers ---

def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_transcripts_table() -> None:
    with _db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                session_id  TEXT PRIMARY KEY,
                topic       TEXT,
                source_docs TEXT,
                argument    TEXT NOT NULL,
                exchanges   TEXT NOT NULL,
                evaluation  TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _save_transcript(session_id: str, session, evaluation: dict) -> None:
    exchanges = [
        {"question": ex.question, "response": ex.response}
        for ex in session.argument.rounds
    ]
    with _db_connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO transcripts
                (session_id, topic, source_docs, argument, exchanges, evaluation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session.topic,
                json.dumps(session.source_docs),
                session.argument.argument_text,
                json.dumps(exchanges),
                json.dumps(evaluation),
            ),
        )


# --- app lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_transcripts_table()
    yield


app = FastAPI(lifespan=lifespan)


# --- session management ---

def load_rubric_items() -> list[dict]:
    rubric_path = _EVALUATOR_AGENT_PATH / "sample_rubric.json"
    return json.loads(rubric_path.read_text())["criteria"]


class Session:
    def __init__(self):
        self.agent = SocraticAgent(rubric_items=load_rubric_items(), reading_text=None)
        self.argument: StudentArgument | None = None
        self.round_num = 0
        self.pending_question: str | None = None
        self.status = "awaiting_topic"
        self.topic: str | None = None
        self.source_docs: list[str] = []


sessions: dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return session


# --- request models ---

class TopicIn(BaseModel):
    topic_text: str


class ArgumentIn(BaseModel):
    argument_text: str


class ResponseIn(BaseModel):
    response_text: str


# --- session endpoints ---

@app.post("/api/session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session()
    return {"session_id": session_id, "rounds_total": ROUNDS}


@app.post("/api/session/{session_id}/topic")
def submit_topic(session_id: str, body: TopicIn):
    session = get_session(session_id)
    if session.status != "awaiting_topic":
        raise HTTPException(status_code=400, detail=f"Session is in state '{session.status}', not awaiting a topic")

    session.topic = body.topic_text
    grounding = check_groundedness(body.topic_text)
    session.source_docs = extract_source_docs(grounding)
    session.status = "awaiting_argument"
    return {"source_docs": session.source_docs}


@app.post("/api/session/{session_id}/argument")
def submit_argument(session_id: str, body: ArgumentIn):
    session = get_session(session_id)
    if session.status != "awaiting_argument":
        raise HTTPException(status_code=400, detail=f"Session is in state '{session.status}', not awaiting an argument")

    session.argument = StudentArgument(argument_text=body.argument_text)
    session.round_num = 1
    session.pending_question = session.agent.ask_question(session.argument, round_num=1)
    session.status = "in_round"
    return {"round": session.round_num, "rounds_total": ROUNDS, "question": session.pending_question}


@app.post("/api/session/{session_id}/respond")
def submit_response(session_id: str, body: ResponseIn):
    session = get_session(session_id)
    if session.status != "in_round":
        raise HTTPException(status_code=400, detail=f"Session is in state '{session.status}', not awaiting a response")

    session.argument.rounds.append(
        SocraticExchange(question=session.pending_question, response=body.response_text)
    )

    if session.round_num < ROUNDS:
        session.round_num += 1
        session.pending_question = session.agent.ask_question(session.argument, round_num=session.round_num)
        return {"round": session.round_num, "rounds_total": ROUNDS, "question": session.pending_question}

    session.status = "completed"
    session.pending_question = None
    result = session.agent.evaluate(session.argument)
    evaluation = result.model_dump()
    _save_transcript(session_id, session, evaluation)
    return {"completed": True, "evaluation": evaluation}


# --- transcript endpoints ---

@app.get("/api/transcripts")
def list_transcripts():
    with _db_connect() as conn:
        rows = conn.execute(
            "SELECT session_id, topic, source_docs, created_at FROM transcripts ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "session_id": r["session_id"],
            "topic": r["topic"],
            "source_docs": json.loads(r["source_docs"] or "[]"),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@app.get("/api/transcripts/{session_id}")
def get_transcript(session_id: str):
    with _db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM transcripts WHERE session_id = ?", (session_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "session_id": row["session_id"],
        "topic": row["topic"],
        "source_docs": json.loads(row["source_docs"] or "[]"),
        "argument": row["argument"],
        "exchanges": json.loads(row["exchanges"]),
        "evaluation": json.loads(row["evaluation"]),
        "created_at": row["created_at"],
    }


# --- static files ---

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/transcript/{session_id}")
def transcript_page(session_id: str):
    return FileResponse(str(STATIC_DIR / "transcript.html"))


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
