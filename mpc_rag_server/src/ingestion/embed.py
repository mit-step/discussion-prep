from fastembed import TextEmbedding


MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embedding_model = TextEmbedding(model_name=MODEL)

def generate_embedding(text):
    embeddings = embedding_model.embed([text])
    return embeddings[0].tolist()

def generate_embeddings(texts):
    embeddings = embedding_model.embed(texts)
    return [embedding.tolist() for embedding in embeddings]

if __name__ == "__main__":
    sample_texts = [
        "This is the first sample text.",
        "Here is another example of text.",
        "FastEmbed is a great library for embeddings."
    ]
    embeddings = generate_embeddings(sample_texts)
    for i, embedding in enumerate(embeddings):
        print(f"Text: {sample_texts[i]}")
        print(f"Embedding: {embedding[:10]}... (length: {len(embedding)})\n")