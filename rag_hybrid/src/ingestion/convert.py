from docling.document_converter import DocumentConverter
from docling_core.types.io import DocumentStream
from io import BytesIO
from pathlib import Path
import re
import sys
import zipfile
from pprint import pprint
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import RESOURCES_DIR

_BROKEN_BOOKMARK_REL_RE = re.compile(rb'<Relationship [^>]*Target="#[^"]*"[^>]*/>')


def retrieve_documents():
    data_folder_path = RESOURCES_DIR
    docs = [item for item in data_folder_path.iterdir() if item.is_file()]
    return docs

# docs = retrieve_documents()

def _repair_docx_bookmark_rels(src_path: Path) -> bytes | None:
    """Some legal-database "export to Word" tools (e.g. Westlaw/Lexis) emit internal
    hyperlink relationships (Target="#Bookmark_...") without the required
    TargetMode="External" attribute. Per OOXML, a fragment-only Target must be marked
    external; without it, python-docx treats the fragment as a real zip part and
    crashes. Returns repaired file bytes, or None if no repair was needed. Leaves the
    original file untouched."""

    def fix(match: re.Match) -> bytes:
        tag = match.group(0)
        return tag if b"TargetMode" in tag else tag[:-2] + b' TargetMode="External"/>'

    with zipfile.ZipFile(src_path) as zin:
        rels_names = [n for n in zin.namelist() if n.endswith(".rels")]
        originals = {n: zin.read(n) for n in rels_names}
        fixed = {n: _BROKEN_BOOKMARK_REL_RE.sub(fix, data) for n, data in originals.items()}

        if fixed == originals:
            return None

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = fixed.get(item.filename, zin.read(item.filename))
                zout.writestr(item, data)
    return buffer.getvalue()


def convert_documents(docs):
    converter = DocumentConverter()
    sources = []
    for doc_path in docs:
        repaired = _repair_docx_bookmark_rels(doc_path) if doc_path.suffix.lower() == ".docx" else None
        sources.append(DocumentStream(name=doc_path.name, stream=BytesIO(repaired)) if repaired else doc_path)
    docling_docs = [converter.convert(source).document for source in sources]
    return docling_docs

if __name__ == "__main__":
    docs = retrieve_documents()
    docs = convert_documents(docs) 
    # print(f"Converted {len(docs)} documents from {len(docs)} files")
    pprint(f'First doc object content: {docs[0].texts}')


