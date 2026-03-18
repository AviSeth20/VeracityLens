FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example .env.example

# Download models from HuggingFace Hub at build time
RUN mkdir -p models && \
    huggingface-cli download aviseth/distilbert-fakenews --local-dir models/distilbert --exclude "checkpoints/*" && \
    huggingface-cli download aviseth/roberta-fakenews --local-dir models/roberta --exclude "checkpoints/*" && \
    huggingface-cli download aviseth/xlnet-fakenews --local-dir models/xlnet --exclude "checkpoints/*"

# HuggingFace Spaces uses port 7860
ENV PORT=7860
EXPOSE 7860

CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
