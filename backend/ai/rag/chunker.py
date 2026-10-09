import os

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


def chunk_documents(documents, chunk_size=None, chunk_overlap=None):
    size = (
        chunk_size
        if chunk_size is not None
        else int(os.environ.get("RAG_CHUNK_SIZE", DEFAULT_CHUNK_SIZE))
    )
    overlap = (
        chunk_overlap
        if chunk_overlap is not None
        else int(os.environ.get("RAG_CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP))
    )
    if size < 100:
        raise ValueError("RAG chunk size must be at least 100 characters.")
    if overlap < 0 or overlap >= size:
        raise ValueError("RAG chunk overlap must be non-negative and smaller than chunk size.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    return [
        Document(
            page_content=chunk.page_content,
            metadata={**chunk.metadata, "chunk_index": index},
        )
        for index, chunk in enumerate(chunks)
        if chunk.page_content.strip()
    ]
