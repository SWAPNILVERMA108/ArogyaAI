from pathlib import Path

from django.conf import settings

from .chunker import chunk_documents
from .embeddings import SentenceTransformerEmbeddings
from .loader import load_documents
from .retriever import MedicalRetriever
from .vector_store import FaissVectorStore


class RAGPipeline:
    def __init__(self, documents_dir=None, index_dir=None, embeddings=None, vector_store=None):
        self.documents_dir = Path(documents_dir or settings.BASE_DIR / "data" / "medical")
        self.embeddings = embeddings or SentenceTransformerEmbeddings()
        self.vector_store = vector_store or FaissVectorStore(
            index_dir or settings.BASE_DIR / "data" / "faiss"
        )

    def ingest(self):
        documents = load_documents(self.documents_dir)
        if not documents:
            raise ValueError(
                f"No readable medical source documents were found in {self.documents_dir}."
            )

        chunks = chunk_documents(documents)
        vectors = self.embeddings.embed_documents([chunk.page_content for chunk in chunks])
        records = [
            {
                "text": chunk.page_content,
                "source": chunk.metadata["source"],
                "page": chunk.metadata.get("page"),
                "chunk_index": chunk.metadata["chunk_index"],
                "start_index": chunk.metadata.get("start_index"),
            }
            for chunk in chunks
        ]
        count = self.vector_store.save(vectors, records)
        return {"source_documents": len({document.metadata["source"] for document in documents}), "chunks": count}

    def retrieve(self, query, top_k=4):
        retriever = MedicalRetriever(self.vector_store, self.embeddings)
        return retriever.search(query, top_k=top_k)

    @staticmethod
    def format_context(results):
        passages = []
        for result in results:
            page = result.get("page")
            page_reference = f", page {page}" if page is not None else ""
            passages.append(
                f"[Source: {result['source']}{page_reference}]\n{result['text']}"
            )
        return "\n\n".join(passages)

    @staticmethod
    def source_references(results):
        references = []
        seen = set()
        for result in results:
            reference = (result["source"], result.get("page"))
            if reference in seen:
                continue
            seen.add(reference)
            item = {"source": reference[0]}
            if reference[1] is not None:
                item["page"] = reference[1]
            references.append(item)
        return references
