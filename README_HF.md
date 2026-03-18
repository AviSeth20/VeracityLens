---
title: Fake News Detection API
emoji: 🔍
colorFrom: orange
colorTo: red
sdk: docker
pinned: false
---

# Fake News Detection API

Multi-class fake news detection using fine-tuned DistilBERT, RoBERTa, and XLNet models.

Classifies news articles into: **True** · **Fake** · **Satire** · **Bias**

## Features

- 3 transformer models (DistilBERT, RoBERTa, XLNet) trained on 80k+ articles
- Real-time explainability via gradient saliency + SHAP
- Live news integration via GNews API
- Prediction statistics and user feedback collection
- FastAPI backend with Swagger docs at `/docs`

## Endpoints

- `POST /predict` — classify text as True / Fake / Satire / Bias
- `POST /explain` — gradient saliency + SHAP explainability
- `GET /news` — live news via GNews
- `GET /news/newspaper` — news grouped by predicted label
- `POST /feedback` — submit label corrections
- `GET /stats` — prediction statistics
- `GET /health` — health check
- `GET /docs` — Swagger UI

## Environment Variables

Set these in your Space settings:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
GNEWS_API_KEY=your_gnews_api_key
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

## Models

Models are automatically downloaded from:

- [aviseth/distilbert-fakenews](https://huggingface.co/aviseth/distilbert-fakenews)
- [aviseth/roberta-fakenews](https://huggingface.co/aviseth/roberta-fakenews)
- [aviseth/xlnet-fakenews](https://huggingface.co/aviseth/xlnet-fakenews)
