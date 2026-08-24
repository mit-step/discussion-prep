# Socratic Discussion Prep Tool

Discussion Prep helps students rehearse their argument and hold their stance when counterarguments 
are raised, pushing them to think critically about their position and stay fluent in the course material.

## How it works

1. **Topic / argument** — the student states an argument (typed) in the web UI.
2. **Grounding** — the argument is embedded and matched against the course reading via hybrid
   (vector + BM25) search, so follow-up questions and evaluation can reference the actual source
   material.
3. **Socratic rounds** — over 3 rounds, the agent asks one probing question at a time (never
   supplying facts, counterarguments, or conclusions itself) and the student responds.
4. **Evaluation** — after the final round, the agent scores the full transcript on four holistic
   pillars (logical reasoning, organization, persuasiveness, clarity) plus a supplied grading
   rubric, and returns groundedness notes.
5. **Transcripts** — each session is saved to SQLite and viewable later at `/transcript/{session_id}`.

## Project layout

```
web/              FastAPI backend + static frontend (chat UI, voice input, transcript viewer)
evaluator-agent/  Socratic agent: question generation, rubric-based evaluation, LLM client
rag_hybrid/       Ingestion (PDF → chunks → embeddings) and hybrid vector/BM25 search over SQLite
```

### `web/`
FastAPI app (`app.py`) exposing a session-based API (`/api/session`, `.../topic`,
`.../argument`, `.../respond`, `/api/transcripts`) and serving the static chat UI
(`static/index.html`, `app.js`, `style.css`) with browser speech-to-text input and a transcript
viewer page.

### `evaluator-agent/`
- `Agent/socratic_agent.py` — `SocraticAgent`: builds prompts, asks questions, evaluates,
  validates the model's JSON output against a schema (with one retry on malformed JSON).
- `Agent/prompts.py` — system prompts for the Socratic questioning and rubric-based grading.
- `Agent/rag_tool.py` — bridges into `rag_hybrid` to fetch grounding passages for a claim.
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
- `data/mvp.db` — the SQLite database (vectors, chunks, metadata, and transcripts).
- `resources/` — source documents to ingest.
- `scripts/` — standalone test/debug scripts for each pipeline stage.

## Setup

Requires Python 3.12+ and an API key for the Parley gateway.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r evaluator-agent/requirements.txt -r web/requirements.txt -r rag_hybrid/requirements.txt
```

Copy `.env.example` to `.env` and fill in your key:

```
PARLEY_API_KEY=your-key-here
```

## Running

**Web app:**

```bash
cd web
uvicorn app:app --reload
```

Then open `http://localhost:8000/`.

**CLI (no server, terminal-only):**

```bash
python evaluator-agent/main.py
```

## Contributors

* Cesia Massott — Hybrid-search RAG · [cesiam@mit.edu](mailto:cesiam@mit.edu)
* Pipitchaya Sridam (Sprite) — Memo Evaluator Agent · [sprite48@mit.edu](mailto:sprite48@mit.edu)

