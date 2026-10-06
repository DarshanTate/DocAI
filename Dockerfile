FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.docker.txt .

# Install CPU-only PyTorch.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

RUN pip install --no-cache-dir -r requirements.docker.txt

COPY app ./app
COPY scripts ./scripts
COPY alembic.ini .
COPY alembic ./alembic

RUN mkdir -p /app/storage/documents /app/storage/temp

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]