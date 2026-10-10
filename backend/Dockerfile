FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# tesseract-ocr (+ Hindi data) powers report OCR; libgomp1 is needed by faiss.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-hin libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# CPU-only PyTorch keeps the image far smaller than the default CUDA build.
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu torch \
    && pip install -r requirements.txt

COPY . .
RUN useradd --create-home appuser && mkdir -p media data/faiss && chown -R appuser /app
USER appuser

EXPOSE 8000
# No secrets here: SECRET_KEY, DATABASE_URL, GEMINI_API_KEY etc. come from the environment.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_health_tips && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
