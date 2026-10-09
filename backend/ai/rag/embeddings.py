import os
from functools import lru_cache

import numpy as np


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model(model_name):
    from sentence_transformers import SentenceTransformer

    device = os.environ.get("RAG_EMBEDDING_DEVICE", "cpu")
    return SentenceTransformer(
        model_name,
        device=device,
        trust_remote_code=False,
    )


class SentenceTransformerEmbeddings:
    """Lazy, local sentence embeddings shared by ingestion and retrieval."""

    def __init__(self, model_name=None):
        self.model_name = model_name or os.environ.get(
            "RAG_EMBEDDING_MODEL",
            DEFAULT_EMBEDDING_MODEL,
        )

    @property
    def model(self):
        return _load_model(self.model_name)

    def embed_documents(self, texts):
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        vectors = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.ascontiguousarray(vectors, dtype=np.float32)

    def embed_query(self, text):
        vector = self.model.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.ascontiguousarray(vector, dtype=np.float32)
