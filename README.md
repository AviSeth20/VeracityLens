# Fake News Detection

A multi-class fake news detection system powered by fine-tuned transformer models. It classifies news articles into four categories — **True**, **Fake**, **Satire**, and **Bias** — with real-time explainability via gradient saliency and SHAP. Built as an NTCC project using DistilBERT, RoBERTa, and XLNet trained on a combined dataset of ~80k articles from ISOT, LIAR, BuzzFeed, PolitiFact, and satire sources.

The system includes a FastAPI backend, a React + Tailwind frontend with a live news feed powered by GNews, user feedback collection stored in Supabase for active learning, and an explainability tab showing per-word attention highlights and on-demand SHAP analysis using RoBERTa.

---

## Models

| Model      | Metrics                          |
| ---------- | -------------------------------- |
| DistilBERT | `models/distilbert/metrics.json` |
| RoBERTa    | `models/roberta/metrics.json`    |
| XLNet      | `models/xlnet/metrics.json`      |

All models are fine-tuned on `data/processed/Dataset_Clean.csv` and stored locally under `models/`.

---

## Setup

**Prerequisites:** Python 3.9+, Node.js 18+

```bash
git clone https://github.com/your-org/fake-news-detection.git
cd fake-news-detection
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, GNEWS_API_KEY
```

Run `scripts/setup_supabase.sql` in the Supabase SQL Editor to create the schema.

```bash
# Backend
python -m uvicorn src.api.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173` — API: `http://localhost:8000` — Docs: `http://localhost:8000/docs`

---

## Usage

- Paste any news article text, select a model, and click Analyze
- The result card shows the predicted label, confidence, per-class probabilities, and an Explain tab
- The Explain tab auto-loads gradient saliency highlights; click "Explain Deeply" for SHAP analysis (uses RoBERTa, ~15s on CPU)
- The Live News tab shows real-time articles from GNews — click any to analyze
- The News page (`/news`) shows a newspaper layout with articles grouped by predicted label
- Use the feedback panel to submit corrections for active learning

---

## Project Structure

```
fake-news-detection/
├── data/
│   ├── raw/               # Original datasets
│   └── processed/         # Cleaned training data
├── models/
│   ├── distilbert/
│   ├── roberta/
│   └── xlnet/
├── notebooks/
├── scripts/
│   ├── setup_supabase.sql
│   └── download_models.py
├── src/
│   ├── api/main.py
│   ├── models/            # inference, train, evaluate
│   ├── data/              # preprocessing, dataset, gnews_collector
│   └── utils/             # supabase_client, gnews_client
├── frontend/
├── .env.example
├── requirements.txt
└── docker-compose.yml
```

---

## Stack

- **Backend:** FastAPI, supabase-py v2, transformers, torch, shap
- **Frontend:** React, Vite, Tailwind CSS, Framer Motion, Axios
- **Database:** Supabase (PostgreSQL)
- **News API:** GNews
- **Training:** HuggingFace Trainer, Weights & Biases
