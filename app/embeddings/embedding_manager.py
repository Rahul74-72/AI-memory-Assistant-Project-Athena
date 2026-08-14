import json

import numpy as np

from sentence_transformers import SentenceTransformer


class EmbeddingManager:

    def __init__(self):

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        print("Embedding model loaded.")

    def create_embedding(self, text):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

    def serialize(self, embedding):

        return json.dumps(embedding)

    def deserialize(self, embedding):

        return json.loads(embedding)

    def similarity(self, embedding1, embedding2):

        vector1 = np.array(
            embedding1,
            dtype=np.float32
        )

        vector2 = np.array(
            embedding2,
            dtype=np.float32
        )

        return float(
            np.dot(vector1, vector2)
        )