FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies required for document processing and OCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first.
# This allows Docker to cache this layer when application code changes.
COPY requirements.docker.txt .

RUN pip install --no-cache-dir -r requirements.docker.txt

# Copy application source
COPY app ./app
COPY scripts ./scripts
COPY alembic.ini .
COPY alembic ./alembic

# Create required runtime directories
RUN mkdir -p /app/storage/documents /app/storage/temp

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]