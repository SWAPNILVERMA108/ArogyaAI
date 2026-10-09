# ArogyaAI

ArogyaAI is an AI-powered rural healthcare information assistant, built
incrementally as a React/Vite frontend and Django REST API backend.

> Medical safety: ArogyaAI will provide general health information and will not
> diagnose conditions, replace clinicians, or act as an emergency response service.

## Current status

Chunks 1–11 establish the monorepo, Django REST configuration, JWT accounts,
patient profile APIs, medicine/reminder APIs, chat history and Gemini replies,
plus local document retrieval, report OCR, and OSM facility lookup. Voice and
remaining healthcare features are implemented in later chunks.

The chat reply endpoint requires `GEMINI_API_KEY` in `backend/.env`.
Set `LLM_PROVIDER=gemini` and optionally `GEMINI_MODEL` there as well. The
project does not return a mock answer when configuration is missing; the
endpoint returns a service-unavailable error instead.

Chunk 8 adds local medical-reference retrieval. Place reviewed PDFs, Markdown,
or UTF-8 text in `backend/data/medical/`, then from `backend/` run
`python manage.py ingest_medical_documents`. The local FAISS index is ignored
by Git. No source reference documents are bundled; until reviewed references
are indexed, chat responses receive no retrieved citations. The first
indexing run downloads the configured embedding model.

Chunks 9–10 add authenticated report uploads at `POST /api/reports/upload/`
using multipart form data with a `file` field. PDF, PNG, JPG, and JPEG files
up to 10 MB are accepted. Run OCR for an owned report with
`POST /api/reports/{id}/process/`. Searchable PDFs use local text extraction;
images and scanned PDF pages require Tesseract OCR installed on the backend.
Set `TESSERACT_CMD` and `TESSERACT_LANGUAGES` in `backend/.env`; English is the
default. OCR returns extracted text only, not a medical interpretation. See
[Tesseract's Windows installation instructions](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md).

Chunk 11 adds authenticated facility searches at
`GET /api/hospitals/nearby/`. Provide `latitude` and `longitude`, or a `city`
and/or `pincode`, with optional `radius` (100–25,000 meters) and `category`
(`hospital`, `clinic`, `pharmacy`, or `emergency`). Results are sourced live
from OpenStreetMap and include attribution. For city/postcode searches, set
`MAPS_USER_AGENT` in `backend/.env` to an identifying application string with
real contact information. Location coordinates or city/postcode are sent to
the configured map provider for this search. The public Nominatim service is
strictly limited and must only be used for end-user-initiated lookups; review its
[usage policy](https://operations.osmfoundation.org/policies/nominatim/).

## Repository layout

- `backend/` — Django project and future domain apps
- `frontend/` — React and Vite application
- `docs/` — architecture and project documentation

See [docs/architecture.md](docs/architecture.md) for the planned structure.

## Run locally

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

```powershell
cd frontend
npm.cmd run dev
```
