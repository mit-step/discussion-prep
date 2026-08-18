import sys
import os

def mini_test_embed():
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'ingestion'))
    # print(folder_path)
    sys.path.append(folder_path)
    from embed import generate_embeddings
    from convert import retrieve_documents, convert_documents
    from chunking import build_chunker, chunk_documents

    docs = retrieve_documents()
    converted_docs = convert_documents(docs)
    chunker = build_chunker()
    recorded_chunks = chunk_documents(converted_docs, chunker)
    embedded_chunks = generate_embeddings([record["text"] for record in recorded_chunks])

    # print(f"Embedded {len(embedded_chunks)} chunks from {len(recorded_chunks)} recorded chunks")
    print(f"Sample embedded chunk: {embedded_chunks[4] if embedded_chunks and len(embedded_chunks) > 4 else 'No embeddings generated'}")

if __name__ == "__main__":
    mini_test_embed()