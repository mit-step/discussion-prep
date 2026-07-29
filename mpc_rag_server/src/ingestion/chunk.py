from tokenizers import Tokenizer
from tokenizers.models import BPE
from convert import docling_docs
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer


EMBED_MODEL_ID = 'nomic-ai/nomic-embed-text-v1.5'

tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
)
chunker = HybridChunker(tokenizer=tokenizer)
chunked_docs = []
for doc in docling_docs:
    doc_uuid = None
    for chunk in chunker.chunk(doc):
        chunk_uuid = None
        chunk.metadata['doc_uuid'] = doc_uuid
        chunk.metadata['chunk_uuid'] = chunk_uuid  
        chunked_docs.append(chunk)

