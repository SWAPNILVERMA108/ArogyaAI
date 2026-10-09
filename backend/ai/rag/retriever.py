import os

from .embeddings import SentenceTransformerEmbeddings
from .vector_store import FaissVectorStore


class MedicalRetriever:
    def __init__(self, vector_store=None, embeddings=None):
        self.vector_store = vector_store or FaissVectorStore()
        self.embeddings = embeddings or SentenceTransformerEmbeddings()

    def search(self, query, top_k=4):
        if not self.vector_store.exists:
            return []
        query_vector = self.embeddings.embed_query(query)
        minimum_score = float(os.environ.get("RAG_MIN_SIMILARITY_SCORE", "0.20"))
        return [
            result
            for result in self.vector_store.search(query_vector, limit=top_k)
            if result["score"] >= minimum_score
        ]
