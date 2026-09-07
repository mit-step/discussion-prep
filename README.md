# Socratic Discussion Prep Tool

Discussion Prep helps students rehearse their argument and hold their stance when counterarguments
are raised, pushing them to think critically about their position and stay fluent in the course material.

## How it works

1. **Login** — a name/email form (demo-only, no password — a placeholder for future MIT Touchstone
   SSO) identifies the student so their history and transcripts stay private to them.
2. **Reading library** — the student picks a reading from a searchable library of course materials,
   each showing their latest score on it if they've attempted it before. Search uses the same
   hybrid (vector + BM25) retrieval as grounding, and hides readings below a relevance threshold
   rather than just re-ranking them.
3. **Argument + Socratic rounds** — the student states an argument, then over 3 rounds the agent
   asks one probing question at a time (never supplying facts, counterarguments, or conclusions
   itself). Questions and evaluation are grounded primarily in the selected reading, but the agent
   can also cite other course materials to challenge the student like a real discussion partner
   would.
4. **Evaluation** — after the final round, the agent scores the full transcript on four holistic
   pillars (logical reasoning, organization, persuasiveness, clarity) plus a supplied grading
   rubric.
5. **History & transcripts** — every completed session is saved per user/reading; a clock icon in
   the chat view shows past attempts on that reading, and each session has a shareable transcript
   page.

## Project layout

```
web/              FastAPI backend + React frontend (login, library, chat, transcripts)
evaluator-agent/  Socratic agent: question generation, rubric-based evaluation, LLM client
rag_hybrid/       Ingestion (PDF → chunks → embeddings) and hybrid vector/BM25 search over SQLite
```

### `web/`
FastAPI app (`app.py`) serving both the API (under `/discussion-prep/api/...`) and the built React
frontend (`frontend/`, Vite + TypeScript). `db.py` owns `web/data/app.db` — a separate SQLite
database for users and transcripts, independent from the RAG corpus in `rag_hybrid/data/mvp.db`.
`readings_search.py` implements the library search/relevance-threshold logic.

### `evaluator-agent/`
- `Agent/socratic_agent.py` — `SocraticAgent`: builds prompts, asks questions, evaluates,
  validates the model's JSON output against a schema (with one retry on malformed JSON).
- `Agent/prompts.py` — system prompts for the Socratic questioning and rubric-based grading.
- `Agent/rag_tool.py` — two-tier grounding: passages from the selected reading (primary) plus a
  small cross-reference pool from the rest of the corpus (other).
- `Parley/parley.py` — thin client for MIT's [Parley](https://parley.api.mit.edu) LLM gateway
  (currently `bedrock/claude-haiku-4-5`).
- `Schemas/schemas.py` — Pydantic models for arguments, exchanges, and evaluation output.
- `main.py` — standalone CLI runner for the same flow (useful for testing without the web app).
- `sample_rubric.json` — example grading rubric (a law-school issue-spotter rubric).

### `rag_hybrid/`
- `src/ingestion/` — converts PDFs (via `docling`), chunks them, embeds chunks
  (`sentence-transformers/all-MiniLM-L6-v2` via `fastembed`), and indexes them into SQLite
  (`sqlite-vec` for vectors + FTS5 for lexical search).
- `src/retrieval/` — vector search, BM25 lexical search, and a weighted reciprocal-rank-fusion
  (`hybrid_search`) that combines both.
- `src/config.py` — single place to tune retrieval behavior (RRF weights, top-k values, search
  relevance thresholds).
- `data/mvp.db` — the ingested corpus (vectors, chunks, metadata) — not included in the repo.
- `resources/` — source reading files and their converted PDF previews — not included in the repo.

## Setup

Requires Python 3.10+, Node 20+, and an API key for the Parley gateway.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r evaluator-agent/requirements.txt -r web/requirements.txt -r rag_hybrid/requirements.txt

cd web/frontend
npm install
npm run build   # produces web/frontend/dist, served by the FastAPI app
cd ../..
```

Copy `.env.example` to `.env` and fill in your key:

```
PARLEY_API_KEY=your-key-here
```

**Get the course corpus** (not checked into git):

1. Download [`mvp.db`](https://mitprod-my.sharepoint.com/:u:/g/personal/cesiam_mit_edu/IQA96RxvsLbbSLy3uoonW9o_ASTQNMFygX_gyLx0kZ5Ftuk)
   and extract it into `rag_hybrid/data/` (→ `rag_hybrid/data/mvp.db`).
2. Download the [readings bundle](https://drive.google.com/file/d/1hvTNOZQyTjFAy8C57LP8BUoVnq0SVg9d/view?usp=sharing)
   and extract it into `rag_hybrid/resources/`.

`web/data/app.db` (users/transcripts) is created automatically on first run — no setup needed.

## Running

**Web app:**

```bash
cd web
uvicorn app:app --reload --port 8000
```

Then open `http://localhost:8000/discussion-prep/`.

**CLI (no server, terminal-only):**

```bash
python evaluator-agent/main.py
```

## Contributors

* Cesia Massott — Hybrid-search RAG · [cesiam@mit.edu](mailto:cesiam@mit.edu)
* Pipitchaya Sridam (Sprite) — Memo Evaluator Agent, Student UI · [sprite48@mit.edu](mailto:sprite48@mit.edu)
