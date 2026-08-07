from tokenizers import Tokenizer
from tokenizers.models import BPE
from convert import docling_docs
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from uuid import uuid4


tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
    max_tokens=384,
)
chunker = HybridChunker(tokenizer=tokenizer)
recorded_chunks = []
for doc in docling_docs:
    doc_uuid = str(uuid4())
    for chunk in chunker.chunk_document(doc):
        recorded_chunks.append({
            "chunk_uuid": str(uuid4()),
            "doc_uuid": doc_uuid,
            "text": chunk.text,
            "headings": chunk.meta.headings,
            "page_no": chunk.meta.doc_items[0].prov[0].page_no if chunk.meta.doc_items and chunk.meta.doc_items[0].prov else None,
            "filename": chunk.meta.origin.filename if chunk.meta.origin else None,
        })

