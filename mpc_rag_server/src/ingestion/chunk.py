from tokenizers import Tokenizer
from tokenizers.models import BPE
from convert import docling_docs
from docling.chunkers import HybridChunker

tokenizer = Tokenizer(BPE())
chunker = HybridChunker(tokenizer="sentence-transformers/all-MiniLM-L6-v2")
doucument = docling_docs[0] 
chunk_stream = chunker.chunk(docling_doc)
print("\n--- Extracted Chunks ---")
for i, chunk in enumerate(chunk_stream):
    serialized_text = chunker.serialize(chunk)
    
    print(f"\n[Chunk {i+1}]")
    print(f"Text Content: {serialized_text[:200]}...")
    print(f"Metadata (Page/BBox): {chunk.meta}")