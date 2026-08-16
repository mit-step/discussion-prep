from convert import retrieve_documents, convert_documents
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from uuid import uuid4

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 256


def build_chunker():
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBEDDING_MODEL),
        max_tokens=MAX_TOKENS,
    )
    return HybridChunker(tokenizer=tokenizer)


def chunk_documents(docs, chunker):
    recorded_chunks = []
    for doc in docs:
        doc_uuid = str(uuid4())
        for chunk in chunker.chunk(doc):
            recorded_chunks.append({
                "chunk_uuid": str(uuid4()),
                "doc_uuid": doc_uuid,
                "text": chunk.text,
                "headings": chunk.meta.headings,
                "page_no": (
                    chunk.meta.doc_items[0].prov[0].page_no
                    if chunk.meta.doc_items and chunk.meta.doc_items[0].prov
                    else None
                ),
                "filename": chunk.meta.origin.filename if chunk.meta.origin else None,
            })
    return recorded_chunks


if __name__ == "__main__":
    docs = retrieve_documents()
    converted_docs = convert_documents(docs)
    chunker = build_chunker()
    recorded_chunks = chunk_documents(converted_docs, chunker)
    print(f"Chunked {len(recorded_chunks)} chunks from {len(converted_docs)} docs")
    print(f"Sample chunk: {recorded_chunks[4] if recorded_chunks else 'No chunks generated'}")

