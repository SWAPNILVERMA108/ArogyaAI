# Testing

## Backend (pytest, 104 tests)
```
cd backend
pip install -r requirements-dev.txt
python -m pytest            # or: python manage.py test
```
`tests/test_security.py` covers anonymous access to every private endpoint,
cross-user data isolation, role escalation, upload validation, rate limiting,
error envelope and auth-event logging.

## Frontend (Vitest + React Testing Library)
```
cd frontend
npm test
```

## Frontend ↔ backend integration
Runs the real service layer (Axios interceptors, token refresh, every feature
API) against a live server on a throw-away database:
```
cd backend
set DATABASE_URL=sqlite:///C:/temp/int.sqlite3
python manage.py migrate
python manage.py seed_health_tips
python manage.py shell -c "from django.contrib.auth import get_user_model as g; U=g(); U.objects.create_user(email='doctor@example.com',password='StrongPass123!',name='Dr Rao',role='DOCTOR'); U.objects.create_user(email='admin@example.com',password='StrongPass123!',name='Admin',role='ADMIN')"
python manage.py runserver
```
then, in `frontend/`: `set VITE_API_BASE_URL=http://127.0.0.1:8000/api && npm run test:integration`
(the throttle allows ~10 auth calls/minute per IP; wait a minute between reruns).

## Manual
Swagger UI: http://localhost:8000/api/docs/
