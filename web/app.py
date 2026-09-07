from __future__ import annotations

import json
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

# Agent/, Schemas/, Parley/ are flat top-level packages under evaluator-agent/,
# same as evaluator-agent/Agent/rag_tool.py reaches into rag_hybrid/.
_EVALUATOR_AGENT_PATH = Path(__file__).resolve().parent.parent / "evaluator-agent"
sys.path.insert(0, str(_EVALUATOR_AGENT_PATH))

from Agent.socratic_agent import SocraticAgent  # noqa: E402
from Schemas.schemas import SocraticExchange, StudentArgument  # noqa: E402

import db  # noqa: E402
import readings_search  # noqa: E402

ROUNDS = 3

KNOWLEDGE_GRAPH_PATH = Path(__file__).resolve().parent.parent / "knowledge_graph" / "graph.html"

# Demo is hosted under this path prefix (matches the <base> tag in static/index.html
# and static/transcript.html) rather than at the domain root.
ROUTE_PREFIX = "/discussion-prep"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_app_db()
    db.READINGS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix=ROUTE_PREFIX)


# --- auth (demo placeholder — NOT real security) ---

def get_current_user_id(x_user_id: str = Header(...)) -> str:
    """DEMO ONLY — trusts a client-supplied header with zero verification;
    anyone can spoof any user_id. Replace with real Touchstone-backed session
    auth before any non-demo use."""
    return x_user_id


class LoginIn(BaseModel):
    name: str
    email: str


@router.post("/api/auth/login")
def login(body: LoginIn):
    user = db.get_or_create_user(body.name, body.email)
    return {"user_id": user["user_id"], "name": user["name"], "email": user["email"]}


# --- readings catalog + search ---

@router.get("/api/readings")
def list_readings(user_id: str = Depends(get_current_user_id)):
    return db.readings_with_evaluations(user_id)


@router.get("/api/readings/search")
def search_readings(q: str, user_id: str = Depends(get_current_user_id)):
    return readings_search.search_readings(q, user_id)


# --- knowledge graph (citation map across the corpus, built offline by
# knowledge_graph/build_graph.py) ---

@router.get("/api/knowledge-graph")
def get_knowledge_graph():
    if not KNOWLEDGE_GRAPH_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Knowledge graph not built — run knowledge_graph/build_graph.py",
        )
    return FileResponse(str(KNOWLEDGE_GRAPH_PATH))


# --- session management ---

def load_rubric_items() -> list[dict]:
    rubric_path = _EVALUATOR_AGENT_PATH / "sample_rubric.json"
    return json.loads(rubric_path.read_text())["criteria"]


class Session:
    def __init__(self, doc_uuid: str, user_id: str, title: str):
        self.doc_uuid = doc_uuid
        self.user_id = user_id
        self.title = title
        self.agent = SocraticAgent(rubric_items=load_rubric_items(), reading_text=None, doc_uuid=doc_uuid)
        self.argument: StudentArgument | None = None
        self.round_num = 0
        self.pending_question: str | None = None
        self.status = "awaiting_argument"


sessions: dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return session


# --- request models ---

class SessionIn(BaseModel):
    doc_uuid: str


class ArgumentIn(BaseModel):
    argument_text: str


class ResponseIn(BaseModel):
    response_text: str


# --- session endpoints ---

@router.post("/api/session")
def create_session(body: SessionIn, user_id: str = Depends(get_current_user_id)):
    reading = db.get_reading(body.doc_uuid)
    if reading is None:
        raise HTTPException(status_code=404, detail="Unknown doc_uuid")
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session(doc_uuid=body.doc_uuid, user_id=user_id, title=reading["title"])
    return {"session_id": session_id, "rounds_total": ROUNDS, "reading_title": reading["title"]}


@router.post("/api/session/{session_id}/argument")
def submit_argument(session_id: str, body: ArgumentIn):
    session = get_session(session_id)
    if session.status != "awaiting_argument":
        raise HTTPException(status_code=400, detail=f"Session is in state '{session.status}', not awaiting an argument")

    session.argument = StudentArgument(argument_text=body.argument_text)
    session.round_num = 1
    session.pending_question = session.agent.ask_question(session.argument, round_num=1)
    session.status = "in_round"
    return {"round": session.round_num, "rounds_total": ROUNDS, "question": session.pending_question}


@router.post("/api/session/{session_id}/respond")
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
    exchanges = [{"question": ex.question, "response": ex.response} for ex in session.argument.rounds]
    db.save_transcript(
        session_id=session_id,
        user_id=session.user_id,
        reading_id=session.doc_uuid,
        argument=session.argument.argument_text,
        exchanges=exchanges,
        evaluation=evaluation,
    )
    return {"completed": True, "evaluation": evaluation}


# --- per-reading history ---

@router.get("/api/readings/{doc_uuid}/history")
def reading_history(doc_uuid: str, user_id: str = Depends(get_current_user_id)):
    history = []
    for row in db.list_reading_history(user_id, doc_uuid):
        evaluation = json.loads(row["evaluation"])
        history.append({
            "session_id": row["session_id"],
            "created_at": row["created_at"],
            **db.summarize_evaluation(evaluation),
        })
    return history


# --- transcript detail (ownership-checked — never distinguishes "not found" from "not yours") ---

@router.get("/api/transcripts/{session_id}")
def get_transcript(session_id: str, user_id: str = Depends(get_current_user_id)):
    row = db.get_transcript(session_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "session_id": row["session_id"],
        "reading_id": row["reading_id"],
        "argument": row["argument"],
        "exchanges": json.loads(row["exchanges"]),
        "evaluation": json.loads(row["evaluation"]),
        "created_at": row["created_at"],
    }


# --- static files ---
# The React SPA build (web/frontend/, `npm run build`). web/static/* (the old
# vanilla-JS UI) is no longer served — this replaces it.
FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

# check_dir=False: rag_hybrid/resources/readings/ is populated by the one-time
# PDF migration script and won't exist until that's been run.
app.mount(
    f"{ROUTE_PREFIX}/readings-pdf",
    StaticFiles(directory=str(db.READINGS_DIR), check_dir=False),
    name="readings-pdf",
)
app.mount(
    f"{ROUTE_PREFIX}/assets",
    StaticFiles(directory=str(FRONTEND_DIST / "assets"), check_dir=False),
    name="frontend-assets",
)


# SPA fallback — must be the LAST route registered on `router` so every
# /api/... route above takes precedence. React Router owns everything else
# under the prefix (/login, /library, /chat/:docUuid, /transcript/:id).
@router.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built — run `npm run build` in web/frontend/",
        )
    # Vite copies web/frontend/public/* (favicon.svg, kelo-syllabus.png, ...)
    # straight into dist/ root rather than dist/assets/, so they're only
    # reachable here — serve them if the path resolves to a real file.
    if full_path:
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(str(candidate))
    return FileResponse(str(index_path))


app.include_router(router)


@app.get("/")
def root_redirect():
    return RedirectResponse(url=f"{ROUTE_PREFIX}/")
