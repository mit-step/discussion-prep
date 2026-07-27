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
document = docling_docs[0] 
chunk_stream = chunker.chunk(document)
print("\n--- Extracted Chunks ---")
for i, chunk in enumerate(chunk_stream):
    serialized_text = chunker.serialize(chunk)
    
    print(f"\n[Chunk {i+1}]")
    print(f"Text Content: {serialized_text[:200]}...")
    print(f"Metadata (Page/BBox): {chunk.meta}")