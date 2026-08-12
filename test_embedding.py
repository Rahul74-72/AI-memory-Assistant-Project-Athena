from sentence_transformers import SentenceTransformer

print("Loading model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model loaded successfully!")

sentences = [
    "I like Python",
    "I enjoy programming in Python",
    "I love cricket"
]

embeddings = model.encode(sentences)
print("\nEmbedding shape:")
print(embeddings.shape)
print("\nFirst embedding:")
print(embeddings[0])
