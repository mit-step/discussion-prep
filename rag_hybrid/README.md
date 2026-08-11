# rag_hybrid

A hybrid retrieval-augmented-generation (RAG) pipeline, intended to run as an MCP server that grounds a grading LLM's answers in source PDFs (and other Docling-supported formats) provided by the instructor.

**Status:** ingestion pipeline is scaffolded; the MCP server layer and semantic retrieval are not yet implemented (see Known Gaps below).

## How it's meant to work

```
data/*.pdf  ->  convert.py  ->  chunk.py  ->  embed.py  ->  index.py  ->  mvp.db (SQLite)
                                                                              |
                                                              retrieval/lexical.py (BM25 search)
```

1. **Input**: files placed in `data/` (gitignored, not committed). Any file Docling can parse — PDF, DOCX, PPTX, XLSX, HTML, Markdown, images via OCR.
2. **Convert** (`src/ingestion/convert.py`): reads every file in `data/` and converts it to a Docling `Document` via `DocumentConverter`.
3. **Chunk** (`src/ingestion/chunk.py`): splits each document into ≤256-token chunks using Docling's `HybridChunker`, tokenized with `sentence-transformers/all-MiniLM-L6-v2`. Each chunk keeps its heading path, page number, source filename, and a generated UUID.
4. **Embed** (`src/ingestion/embed.py`): generates 384-dim embeddings for each chunk using FastEmbed with the same MiniLM-L6-v2 model.
5. **Index** (`src/ingestion/index.py`): stores everything in a local SQLite database (`mvp.db`):
   - `embeddings_meta` — chunk text + metadata (doc/chunk UUIDs, source type, JSON metadata).
   - `vec_embeddings` — a `sqlite-vec` virtual table holding the embedding vectors (cosine distance).
   - `embeddings_fts` — an FTS5 virtual table auto-synced via triggers, for keyword search.
6. **Retrieve** (`src/retrieval/lexical.py`): runs a BM25 keyword search against `embeddings_fts` and returns the top-k matching chunks.

The grading LLM is intended to call this retrieval step (eventually via an MCP tool) to pull relevant chunks from the source PDFs and ground its answers/feedback in them rather than relying on its own memory.

## Running it (ingestion)

```bash
cd src/ingestion
python index.py   # runs convert -> chunk -> embed -> store, end to end
```

Requires `docling`, `docling_core`, `transformers`, `fastembed`, and `sqlite-vec` installed (not all are currently listed correctly in `requirements.txt` — see below).

## Known gaps / bugs

- **Fixed (evaluator-agent integration):** `src/ingestion/index.py`'s `from embedding import generate_embedding` (wrong module name) and `src/retrieval/lexical.py`'s missing `pathlib` import were both broken imports blocking `bm25_search` and `index.py`'s `main()`; both are now fixed so ingestion and BM25 search run end to end. `*.db` was also added to `.gitignore` since ingestion writes `mvp.db` locally and it holds indexed course materials.
- **No MCP server yet** — this repo only implements the ingestion + lexical-search pieces; there's no server exposing retrieval as an MCP tool. (`evaluator-agent/` currently calls `bm25_search` directly as a Python function rather than through MCP, as a stand-in until this exists.)
- **No semantic/vector search** — `vec_embeddings` is populated but nothing queries it yet; only lexical (BM25) search is implemented.
- **No hybrid fusion** — lexical and vector results aren't combined/reranked (despite the "hybrid" name).
- **`convert_documents()` (`src/ingestion/convert.py:14`) aborts the whole ingestion batch on one bad file.** It's a single list comprehension that converts every file before returning, so a single unparseable file raises before any chunking/embedding/inserting happens — none of the other successfully-converted documents get persisted either. TODO: convert per-file with a try/except that logs and skips failures instead of raising. One real file has already hit this: `Lujan v. Defenders of Wildlife_ 504 U.S. 555 Excerpts.docx` has a corrupt internal bookmark reference (`word/#Bookmark_LEDHN12` missing from the .docx zip) that Docling's Word backend can't parse; it's been moved to `data_quarantine/` (gitignored) pending a repaired copy.
- `src/config.py` is empty; model name, DB path, and chunk size are duplicated across files instead of centralized.
- `requirements.txt` lists some standard-library modules as if they were pip packages, and is missing `sqlite-vec`, `transformers`, and `docling-core`.
- No `__init__.py` files — scripts use flat imports and must be run from within their own subfolder.
