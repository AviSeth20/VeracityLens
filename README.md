<div align="center">

<img src="https://img.shields.io/badge/VeracityLens-AI%20News%20Verification-d97757?style=for-the-badge&logo=brain&logoColor=white" alt="VeracityLens" />

# VeracityLens — Fake News Detection

**Multi-class fake news detection powered by fine-tuned transformer models.**  
Classifies news articles into True, Fake, Satire, and Bias — with token-level explainability.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=flat-square&logo=vercel)](https://veracitylens.vercel.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-HuggingFace%20Spaces-yellow?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/aviseth/fake-news-api)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react)](https://react.dev)

</div>

---

## Overview

VeracityLens is an end-to-end fake news detection system trained on ~80,000 articles from ISOT, LIAR, BuzzFeed, PolitiFact, and satire sources. It uses three fine-tuned transformer models to classify news content into four categories and provides token-level explainability so users can understand _why_ a prediction was made.

---

## Features

- **Multi-class classification** — True, Fake, Satire, Bias
- **3 transformer models** — DistilBERT, RoBERTa, XLNet (switchable at runtime)
- **Ensemble model** — combines all 3 models with hard, soft, and weighted voting
- **Explainability** — gradient attention highlights + deep SHAP analysis
- **Live news feed** — real-time articles via GNews, click any to analyze
- **Newspaper view** — news grouped by predicted label across multiple topics
- **Analysis history** — session-based prediction history stored in Supabase
- **Dark mode** — full light/dark theme with system preference detection
- **Feedback system** — submit corrections for active learning via Supabase
- **Prediction stats** — live dashboard showing label distribution

---

## Models

All models fine-tuned on the same dataset with 4-class classification.

| Model      | Accuracy | Macro F1 | Parameters | HuggingFace                                                                       |
| ---------- | -------- | -------- | ---------- | --------------------------------------------------------------------------------- |
| DistilBERT | 85.9%    | 0.848    | 66M        | [aviseth/distilbert-fakenews](https://huggingface.co/aviseth/distilbert-fakenews) |
| RoBERTa    | 85.8%    | 0.845    | 125M       | [aviseth/roberta-fakenews](https://huggingface.co/aviseth/roberta-fakenews)       |
| XLNet      | 86.2%    | 0.851    | 110M       | [aviseth/xlnet-fakenews](https://huggingface.co/aviseth/xlnet-fakenews)           |

### Per-class F1 Scores

| Class  | DistilBERT | RoBERTa | XLNet |
| ------ | ---------- | ------- | ----- |
| True   | 0.889      | 0.888   | 0.892 |
| Fake   | 0.872      | 0.879   | 0.876 |
| Satire | 0.998      | 0.998   | 0.997 |
| Bias   | 0.633      | 0.615   | 0.638 |

---

## Dataset

Trained on ~80k articles aggregated from:

| Dataset                 | Type                             |
| ----------------------- | -------------------------------- |
| ISOT Fake News          | True / Fake                      |
| LIAR                    | Multi-class political statements |
| BuzzFeed Political News | True / Fake                      |
| PolitiFact              | True / Fake                      |
| The Onion / NotTheOnion | Satire                           |
| India MythFacts         | Bias / Misinformation            |
| Propaganda Dataset      | Bias                             |

The cleaned and merged dataset is publicly available on Kaggle:

[![Kaggle Dataset](https://img.shields.io/badge/Kaggle-Multi--Class%20Fake%20News%20Dataset-20beff?style=flat-square&logo=kaggle)](https://www.kaggle.com/datasets/aviseth20/multi-class-fake-news-dataset)

```python
import kagglehub
from kagglehub import KaggleDatasetAdapter

df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "aviseth20/multi-class-fake-news-dataset",
    "",
)
```

---

## Stack

| Layer            | Technology                                  |
| ---------------- | ------------------------------------------- |
| Backend          | FastAPI, Transformers, PyTorch, SHAP        |
| Frontend         | React 18, Vite, Tailwind CSS, Framer Motion |
| Database         | Supabase (PostgreSQL)                       |
| News API         | GNews                                       |
| Model Hosting    | HuggingFace Hub                             |
| Backend Hosting  | HuggingFace Spaces (Docker)                 |
| Frontend Hosting | Vercel                                      |

---

## Local Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git

### 1. Clone the repo

```bash
git clone https://github.com/AviSeth20/fake-news-detection.git
cd fake-news-detection
```

### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, GNEWS_API_KEY in .env
```

Run the Supabase schema by executing `scripts/setup_supabase.sql` in your Supabase SQL Editor.

### 3. Download models

```bash
python scripts/download_models.py
```

This downloads DistilBERT, RoBERTa, and XLNet base weights to `models/`.  
To use your own fine-tuned weights, replace the contents of each model folder.

### 4. Run the backend

```bash
# Run from the fake-news-api directory
cd fake-news-api
uvicorn src.api.main:app --reload --port 8000
# API running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
# Frontend running at http://localhost:5173
```

---

## Project Structure

```
fake-news-detection/
├── data/
│   ├── raw/               # Original datasets
│   └── processed/         # Cleaned training data
├── models/
│   ├── distilbert/        # Fine-tuned DistilBERT weights
│   ├── roberta/           # Fine-tuned RoBERTa weights
│   └── xlnet/             # Fine-tuned XLNet weights
├── notebooks/
│   ├── Dataset_Cleaning.ipynb
│   └── 03_model_training.ipynb
├── fake-news-api/         # Backend (FastAPI)
│   ├── src/
│   │   ├── api/main.py    # FastAPI application (start server from here)
│   │   ├── models/        # inference, ensemble, training, evaluation
│   │   ├── data/          # preprocessing, dataset, GNews collector
│   │   └── utils/         # Supabase client, GNews client
│   ├── scripts/
│   │   ├── download_models.py
│   │   └── setup_supabase.sql
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # React + Vite application
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── contexts/      # ThemeContext
│   │   ├── pages/         # HistoryPage, NewsPage
│   │   ├── services/      # API client
│   │   └── utils/         # sessionTracker
│   └── package.json
└── .env.example
```

> **Note:** The `src/` folder at the workspace root is an older copy and is not used. Always run the backend from `fake-news-api/`.

---

## API Endpoints

| Method | Endpoint             | Description                                  |
| ------ | -------------------- | -------------------------------------------- |
| POST   | `/predict`           | Classify text as True / Fake / Satire / Bias |
| POST   | `/predict/ensemble`  | Ensemble prediction (all 3 models + voting)  |
| POST   | `/explain`           | Gradient saliency + SHAP explainability      |
| GET    | `/history/{session}` | User prediction history                      |
| GET    | `/news`              | Live news via GNews                          |
| GET    | `/news/newspaper`    | News grouped by predicted label              |
| POST   | `/feedback`          | Submit label corrections                     |
| GET    | `/stats`             | Prediction statistics                        |
| GET    | `/storage`           | Database storage usage                       |
| GET    | `/health`            | Health check                                 |
| GET    | `/docs`              | Swagger UI                                   |

---

## Built By

| Name     | GitHub                                     | Email                 |
| -------- | ------------------------------------------ | --------------------- |
| Avi Seth | [@AviSeth20](https://github.com/AviSeth20) | aviseth6146@gmail.com |

---

<div align="center">
<sub>Built with PyTorch, HuggingFace Transformers, FastAPI, and React</sub>
</div>
