# Deployment

**Backend (Render/Railway/any Docker host)** — build `backend/Dockerfile`, set:

| Variable | Notes |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `SECRET_KEY` | long random value (production refuses the dev default) |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` |
| `ALLOWED_HOSTS` | your API hostname(s), comma separated |
| `CORS_ALLOWED_ORIGINS` | your Vercel URL, e.g. `https://app.vercel.app` |
| `GEMINI_API_KEY`, `VOICE_CLOUD_ENABLED`, `MAPS_USER_AGENT` | feature keys |

`render.yaml` is a ready blueprint. **Frontend (Vercel)** — root `frontend/`,
build `npm run build`, output `dist`, env `VITE_API_BASE_URL=https://<api-host>/api`
(`vercel.json` handles SPA routing).

## Known limitations to plan for
- **Uploaded reports are stored on local disk.** Container disks on Render/Railway are
  ephemeral: attach a persistent disk or move `MEDIA_ROOT` to object storage (S3) before real use.
- **Rate limits use per-process memory.** With more than one worker/instance, configure a shared
  cache (Redis) so limits are enforced globally.
- **The FAISS index is built per instance** (`python manage.py ingest_medical_documents`); no
  reviewed medical documents are bundled, so chat answers carry no citations until you add some.
- Medicine reminders are stored and displayed in-app only; there is no push/SMS delivery.
