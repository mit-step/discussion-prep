from fastembed import TextEmbedding


MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embedding_model = TextEmbedding(model_name=MODEL)

def generate_embedding(text):
    embeddings = embedding_model.embed([text])
    return embeddings[0].tolist()

def generate_embeddings(texts):
    embeddings = embedding_model.embed(texts)
    return [embedding.tolist() for embedding in embeddings]

