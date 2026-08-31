# One-time DOCX/DOC -> PDF conversion for the readings library's PDF-preview
# feature. Delete this file once rag_hybrid/resources/readings/ has all 51
# converted PDFs confirmed present — it's a throwaway migration script, not
# part of the running app.
#
# This does NOT touch mvp.db and does NOT re-run ingestion/chunking/embedding.
# It only reads mvp.db (read-only) to look up each document's doc_uuid, so the
# converted files can be named to match what web/app.py serves them as.
#
# Prerequisites:
#   brew install libreoffice
#   Place the 51 original source files (matching the filenames already in
#   mvp.db's embeddings_meta.metadata) into:
#     rag_hybrid/resources/readings_source/
#
# Run from the repo root:
#   .venv/bin/python rag_hybrid/scripts/one_time_convert_readings_to_pdf.py

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import DATABASE_PATH, RESOURCES_DIR  # noqa: E402

SOURCE_DIR = RESOURCES_DIR / "readings_source"
OUTPUT_DIR = RESOURCES_DIR / "readings"
CONVERTIBLE_EXTENSIONS = {".docx", ".doc"}
CONVERSION_TIMEOUT_SECONDS = 60


def load_catalog() -> list[dict]:
    if not DATABASE_PATH.exists():
        print(f"mvp.db not found at {DATABASE_PATH} — nothing to do.")
        return []
    conn = sqlite3.connect(str(DATABASE_PATH))
    rows = conn.execute("SELECT doc_uuid, MIN(metadata) AS metadata FROM embeddings_meta GROUP BY doc_uuid").fetchall()
    conn.close()

    catalog = []
    for doc_uuid, metadata in rows:
        meta = json.loads(metadata) if metadata else {}
        filename = meta.get("filename")
        if filename:
            catalog.append({"doc_uuid": doc_uuid, "filename": filename})
    return catalog


def find_source_file(filename: str) -> Path | None:
    """Case-insensitive match — the corpus mixes .pdf/.PDF/.docx/.DOCX."""
    target = filename.lower()
    for candidate in SOURCE_DIR.iterdir():
        if candidate.is_file() and candidate.name.lower() == target:
            return candidate
    return None


def convert_to_pdf(source: Path, dest: Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            result = subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp_dir, str(source)],
                capture_output=True,
                text=True,
                timeout=CONVERSION_TIMEOUT_SECONDS,
            )
        except FileNotFoundError:
            print("  ERROR: `soffice` not found on PATH — install LibreOffice first (brew install libreoffice).")
            return False
        except subprocess.TimeoutExpired:
            print(f"  ERROR: conversion of {source.name} timed out after {CONVERSION_TIMEOUT_SECONDS}s")
            return False

        if result.returncode != 0:
            print(f"  ERROR: soffice failed on {source.name}: {result.stderr.strip()}")
            return False

        converted = Path(tmp_dir) / f"{source.stem}.pdf"
        if not converted.exists():
            print(f"  ERROR: expected output {converted.name} not found after conversion")
            return False

        shutil.move(str(converted), str(dest))
        return True


def main() -> None:
    catalog = load_catalog()
    if not catalog:
        return

    if not SOURCE_DIR.exists():
        print(f"Source directory not found: {SOURCE_DIR}")
        print("Create it and place the 51 original files there first.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    converted, copied, skipped, failed = [], [], [], []

    for entry in catalog:
        doc_uuid, filename = entry["doc_uuid"], entry["filename"]
        dest = OUTPUT_DIR / f"{doc_uuid}.pdf"
        if dest.exists():
            skipped.append(filename)
            continue

        source = find_source_file(filename)
        if source is None:
            failed.append((filename, "source file not found"))
            continue

        if source.suffix.lower() == ".pdf":
            shutil.copyfile(source, dest)
            copied.append(filename)
        elif source.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            print(f"Converting {filename}…")
            if convert_to_pdf(source, dest):
                converted.append(filename)
            else:
                failed.append((filename, "conversion failed"))
        else:
            failed.append((filename, f"unsupported extension {source.suffix}"))

    print("\n=== Summary ===")
    print(f"Copied as-is (already PDF): {len(copied)}")
    print(f"Converted from DOCX/DOC:    {len(converted)}")
    print(f"Already present, skipped:   {len(skipped)}")
    print(f"Failed ({len(failed)}):")
    for filename, reason in failed:
        print(f"  - {filename}: {reason}")

    total_present = len(copied) + len(converted) + len(skipped)
    print(f"\n{total_present}/{len(catalog)} readings now have a PDF in {OUTPUT_DIR}")
    if not failed:
        print("All readings converted successfully — delete this script now.")


if __name__ == "__main__":
    main()
