import json
import os

import numpy as np

from functools import lru_cache


@lru_cache(maxsize=1)
def _model():
    # Keep heavy imports and model loading out of API/test startup.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        local_files_only=os.environ.get("ATHENA_MODEL_DOWNLOADS", "0") != "1",
    )


class EmbeddingManager:

    def __init__(self):

        self.model = None

    def create_embedding(self, text):

        if self.model is None:
            self.model = _model()
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
