# Medical RAG source documents

Place reviewed, legally usable PDF, Markdown, or UTF-8 text references in
`backend/data/medical/` before building the local RAG index. Prefer primary
sources such as government health agencies or recognized clinical
organizations, and preserve publisher and publication date in each source or
its metadata. Do not put unreviewed internet content or patient records there.

The ingestion command indexes files from that directory only. Scanned PDFs
need searchable text from OCR, which is implemented in a later chunk. Generated
FAISS files live under `backend/data/faiss/` and are ignored by Git.

From `backend/`, run `python manage.py ingest_medical_documents` to rebuild
the index. The first embedding run downloads the configured Sentence
Transformers model. This project does not bundle medical source documents.
