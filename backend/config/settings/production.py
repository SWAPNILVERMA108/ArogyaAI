"""Production settings loaded through deployment environment variables."""

from .base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = [host for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host]

if SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError("Set a non-development SECRET_KEY before deploying ArogyaAI.")

DATABASES = {"default": env.db("DATABASE_URL")}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
