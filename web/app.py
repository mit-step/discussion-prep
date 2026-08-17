import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Agent/, Schemas/, Parley/ are flat top-level packages under evaluator-agent/,
# same as evaluator-agent/Agent/rag_tool.py reaches into rag_hybrid/.
_EVALUATOR_AGENT_PATH = Path(__file__).resolve().parent.parent / "evaluator-agent"
sys.path.insert(0, str(_EVALUATOR_AGENT_PATH))

from Agent.socratic_agent import SocraticAgent  # noqa: E402
from Schemas.schemas import SocraticExchange, StudentArgument  # noqa: E402

ROUNDS = 3
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI()


def load_rubric_items() -> list[dict]:
    rubric_path = _EVALUATOR_AGENT_PATH / "sample_rubric.json"
    import json

    return json.loads(rubric_path.read_text())["criteria"]


class Session:
    def __init__(self):
        self.agent = SocraticAgent(rubric_items=load_rubric_items(), reading_text=None)
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


class ArgumentIn(BaseModel):
    argument_text: str


class ResponseIn(BaseModel):
    response_text: str


@app.post("/api/session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session()
    return {"session_id": session_id, "rounds_total": ROUNDS}


@app.post("/api/session/{session_id}/argument")
def submit_argument(session_id: str, body: ArgumentIn):
    session = get_session(session_id)
    if session.status != "awaiting_argument":
        raise HTTPException(status_code=400, detail=f"Session is in state '{session.status}', not awaiting an argument")

    session.argument = StudentArgument(argument_text=body.argument_text)
    session.round_num = 1
    session.pending_question = session.agent.ask_question(session.argument)
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
        session.pending_question = session.agent.ask_question(session.argument)
        return {"round": session.round_num, "rounds_total": ROUNDS, "question": session.pending_question}

    session.status = "completed"
    session.pending_question = None
    result = session.agent.evaluate(session.argument)
    return {"completed": True, "evaluation": result.model_dump()}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
