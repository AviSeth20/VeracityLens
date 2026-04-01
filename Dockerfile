FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Cache bust: 2026-03-29-v7 (fix __init__ imports + pin tokenizers 0.19)

ENV PORT=7860
EXPOSE 7860

CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
