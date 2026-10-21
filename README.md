# ArogyaAI

**An AI-powered health information assistant for rural and underserved communities.**

ArogyaAI helps people get general health information in simple English or Hindi, read their medical reports, keep track of medicines, find nearby care and reach emergency help, all from a mobile-friendly web app.

> **Medical safety notice**
> ArogyaAI is an information assistant, **not a doctor**. It does not diagnose conditions, prescribe medicines or calculate doses. Every AI answer carries a disclaimer, and users are told to contact a qualified professional or call emergency services (112 in India) when symptoms may be serious.

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Enabling the AI features](#enabling-the-ai-features)
- [User roles](#user-roles)
- [API documentation](#api-documentation)
- [Testing](#testing)
- [Docker](#docker)
- [Deployment](#deployment)
- [Security and privacy](#security-and-privacy)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Features

| Feature | What it does |
|---|---|
| **AI health chat** | Ask questions in English or Hindi. Keeps conversation history. Every answer includes a disclaimer. |
| **Grounded answers (RAG)** | Searches reviewed medical PDFs that you provide and shows the source file and page for each answer. |
| **Voice assistant** | Speak a question and listen to the answer (Hindi and English). Opt-in, with explicit consent. |
| **Report and prescription reading** | Upload a PDF, PNG or JPG and extract its text with OCR. Output is clearly labelled as text recognition, not a diagnosis. |
| **Medicines and reminders** | Add medicines, set reminder times and weekdays, and mark each dose as taken. |
| **Hospital finder** | Search by GPS or by city/PIN code for hospitals, clinics, pharmacies and emergency facilities using OpenStreetMap data. |
| **Emergency page** | One-tap call to the emergency number, first-aid guidance, personal emergency contacts and a ready-to-send location message. |
| **Health tips** | Wellness tips by category (nutrition, exercise, sleep, hydration, preventive care, general wellness) in English and Hindi. |
| **Doctor view** | A doctor sees a patient's summary only after the patient grants access, and the patient can revoke it at any time. |
| **Admin tools** | Search users, promote an account to Doctor, deactivate accounts and view platform totals. |

The interface is designed for low-literacy and mobile use: large buttons, simple navigation, bottom tab bar on phones, English/Hindi switch and clear error messages.

## Tech stack

**Frontend:** React 19, Vite, Tailwind CSS 4, React Router, Axios, React Hook Form, Lucide icons

**Backend:** Python, Django 5.2, Django REST Framework, SimpleJWT, drf-spectacular

**Database:** SQLite for development, PostgreSQL for production

**AI:** Google Gemini API (chat, speech, optional OCR), LangChain text splitters, sentence-transformers, FAISS

**OCR:** Tesseract, PyMuPDF, pypdf

**Maps:** OpenStreetMap (Overpass and Nominatim), no API key required

**Testing:** pytest, Django REST Framework tests, Vitest, React Testing Library

**DevOps:** Docker, Docker Compose, Render, Vercel

## Architecture

```
 Patient / Doctor / Admin
          |
    React frontend  (pages, components, context, hooks, one Axios client)
          |  HTTPS + JSON
    Django REST API  (JWT auth, roles, rate limits, one error format)
    accounts | patients | medicines | chat | reports | hospitals | emergency | voice | health
          |
   +------+-------------------+------------------+
   |                          |                  |
 AI service layer         Database          OpenStreetMap
 (backend/ai)          (SQLite/PostgreSQL)
 chat, Gemini, RAG,
 OCR, voice, safety prompts
```

Design rules used throughout the code:

- The frontend never touches the database. It only calls the REST API through `src/services/api.js`.
- Django views stay thin: check permissions, validate with a serializer, call a service.
- Business rules live in each app's `services.py`.
- All AI logic lives in `backend/ai`, never inside views.
- Secrets come from environment variables, never from the code.
- Every success and every error response follows one consistent JSON shape.

## Project structure

```
ArogyaAI/
├── backend/
│   ├── config/            settings (base, development, production) and URLs
│   ├── common/            shared helpers: error handling, responses, JSON logging
│   ├── apps/              accounts, patients, medicines, chat, reports,
│   │                      hospitals, emergency, voice, health
│   ├── ai/                llm, rag, ocr, voice, prompts, services
│   ├── data/              health_tips.json, medical/ (your reference PDFs)
│   ├── tests/             cross-cutting security tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/               pages, components, layouts, services, context,
│                          hooks, utils, constants, tests
├── docs/                  deployment and testing notes
├── docker-compose.yml
└── render.yaml
```

## Getting started

### Prerequisites

- Python 3.12 or newer
- Node.js 22 or 24 (LTS)
- Git
- Optional: PostgreSQL 16+ and Tesseract OCR

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ArogyaAI
```

### 2. Backend

Windows (Command Prompt):

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

macOS / Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Open `backend/.env` and set `SECRET_KEY`. Generate a value with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Then create the database and start the server:

```bash
python manage.py migrate
python manage.py seed_health_tips
python manage.py createsuperuser
python manage.py runserver
```

The API is now running at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/api/docs/` to see the interactive API documentation.

### 3. Frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env        # Windows: copy .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`, register a patient account and log in.

## Configuration

All backend settings are read from `backend/.env`. Rules for the file: one `NAME=value` per line, nothing before the name, no spaces around `=`, no quotes, and each name only once. Restart the server after every change.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs tokens and sessions. Required. Production refuses the default. |
| `DEBUG`, `ALLOWED_HOSTS` | Development flags and allowed host names. |
| `DATABASE_URL` | Leave blank for SQLite, or use `postgres://USER:PASSWORD@HOST:5432/DB_NAME`. |
| `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL` | Website addresses allowed to call the API. |
| `GEMINI_API_KEY` | Enables chat, voice and optional cloud OCR. Get one at [Google AI Studio](https://aistudio.google.com/apikey). |
| `GEMINI_MODEL` | Model used for chat answers. |
| `VOICE_CLOUD_ENABLED` | Set to `True` to enable voice. Audio is sent to Google. |
| `MAPS_USER_AGENT` | Identifies your app to OpenStreetMap, for example `ArogyaAI/1.0 (you@example.com)`. Needed for city/PIN search. |
| `TESSERACT_CMD`, `TESSERACT_LANGUAGES` | Path to Tesseract and the languages to use, such as `eng` or `eng+hin`. |
| `OCR_PROVIDER`, `OCR_CLOUD_ENABLED` | `tesseract` (default, local) or `gemini` (cloud vision, report images are sent to Google). |
| `EMERGENCY_SERVICES_NUMBER` | Emergency number shown in the app. Defaults to `112`. |
| `LOG_LEVEL` | Logging detail. Defaults to `INFO`. |

Frontend: `frontend/.env` needs only `VITE_API_BASE_URL` (default `http://localhost:8000/api`). Never put secrets in frontend variables, because the browser can read them.

## Enabling the AI features

**Chat.** Set `GEMINI_API_KEY` in `backend/.env` and restart the server.

**Grounded answers (RAG).** No medical documents are bundled. Add reviewed PDFs (for example WHO fact sheets or government health guidelines with selectable text) to `backend/data/medical/`, then build the search index:

```bash
python manage.py ingest_medical_documents
```

The first run downloads the embedding model (about 90 MB). After a restart, answers that use these documents show their sources.

**Voice.** Set `VOICE_CLOUD_ENABLED=True`. In the chat page, turn on Voice mode, tick the consent box and use the microphone button. Browsers allow the microphone only on `localhost` or HTTPS.

**Report OCR.** Choose one option:

- Local: install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) on the server and set `TESSERACT_CMD`.
- Cloud: set `OCR_PROVIDER=gemini` and `OCR_CLOUD_ENABLED=True`. This works better on phone photos but sends the image to Google.

End users never install anything. OCR runs on the server.

## User roles

| Role | Can do |
|---|---|
| **Patient** | Use chat, voice, reports, medicines, hospital finder, emergency page, health tips and manage their profile and doctor access. |
| **Doctor** | See the profile summary and active medicines of patients who granted access. Cannot see chats or reports. |
| **Admin** | Manage users and view platform totals. Cannot see private health content. |

To create a doctor, register a normal account, log in as the admin you created with `createsuperuser`, open **Users** in the app and change the role to Doctor. A patient then adds the doctor's email under **Profile** to allow access.

## API documentation

Interactive documentation is generated automatically:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

Main endpoint groups: `/api/auth/`, `/api/patients/`, `/api/medicines/`, `/api/chat/`, `/api/reports/`, `/api/hospitals/`, `/api/emergency/`, `/api/voice/`, `/api/health/`, `/api/doctor/`, `/api/admin/`.

Every response uses the same shape:

```json
{ "success": true, "data": { }, "message": "..." }
```

```json
{ "success": false, "error": { "code": "...", "message": "...", "details": { } } }
```

## Testing

```bash
# Backend: 108 tests, outside services are mocked so no keys are needed
cd backend
python -m pytest

# Frontend unit tests
cd frontend
npm test

# Frontend against a live backend (see docs/testing.md for setup)
npm run test:integration
```

The backend suite includes security tests: anonymous access is rejected on every private endpoint, users cannot read each other's data, nobody can self-register as an admin, fake uploads are rejected, errors never include stack traces and failed logins are logged without credentials.

## Docker

```bash
cp backend/.env.example backend/.env    # add your keys
docker compose up --build
```

This starts PostgreSQL, the backend (`http://localhost:8000`) and the frontend (`http://localhost:5173`). The backend image includes Tesseract with Hindi data. Set `POSTGRES_PASSWORD` in your shell for anything other than local testing.

## Deployment

- **Frontend:** Vercel. Root directory `frontend`, build command `npm run build`, output `dist`, environment variable `VITE_API_BASE_URL=https://<your-api-host>/api`. `vercel.json` handles page routing.
- **Backend:** Render (a `render.yaml` blueprint and `backend/Dockerfile` are included) or any Docker host. Set `DJANGO_SETTINGS_MODULE=config.settings.production`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `GEMINI_API_KEY` and `MAPS_USER_AGENT`.
- **Database:** managed PostgreSQL.

See [docs/deployment.md](docs/deployment.md) for details.

## Security and privacy

- Passwords are hashed with Django's password hashers. JWT access tokens last 15 minutes, refresh tokens last 7 days, rotate on use and are blacklisted on logout.
- Role checks plus ownership filtering: another user's record returns 404.
- Uploads are validated by extension, size (10 MB) and file signature, and stored under random names.
- Rate limits on login, chat, map search, voice and doctor lookup.
- Production settings enable HTTPS redirect, HSTS and secure cookies, and refuse to start without a real secret key.
- Voice and cloud OCR are off by default. Audio and location are not stored.
- Logs are structured JSON and never contain passwords, tokens, medical text or the email used in a failed login.
- `.env` files are ignored by Git. Never commit them.

## Known limitations

- Medicine reminders are stored and displayed in the app only. There is no push, SMS or WhatsApp delivery yet.
- Reports get text extraction only. AI summaries are intentionally not generated.
- Without reviewed PDFs in `backend/data/medical/`, chat answers have no citations.
- Tesseract is weak on handwriting. Cloud OCR is better but needs consent and a key.
- Hospital search relies on the free OpenStreetMap servers, which can be slow or busy in dense cities. Data can be incomplete.
- Uploaded reports are stored on local disk. On hosts with temporary disks, use object storage such as S3 before real use.
- Rate limits are counted per server process. Use a shared cache such as Redis when running several servers.
- Password reset and email verification are not implemented yet.
- Free Gemini tiers have rate limits and different data terms. Use only fake data for demos.

## Roadmap

- Medicine reminder delivery by push notification, SMS or WhatsApp
- Emergency keyword detection that shows a call banner instantly
- Password reset and email verification
- Cloud storage for uploaded reports
- Report summaries with clinical review
- More Indian languages
- Installable offline-friendly app (PWA)
- GitHub Actions workflow to run tests on every push

---

*Built as a final-year B.Tech Computer Science project. ArogyaAI provides general information only and is not a substitute for professional medical advice, diagnosis or treatment.*