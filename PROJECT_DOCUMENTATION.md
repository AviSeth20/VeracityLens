# VeracityLens — Complete Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Why This Project](#why-this-project)
3. [Architecture](#architecture)
4. [Dataset](#dataset)
5. [Model Training](#model-training)
6. [Ensemble System](#ensemble-system)
7. [Backend API](#backend-api)
8. [Frontend Application](#frontend-application)
9. [Deployment](#deployment)
10. [Workflow](#workflow)

---

## Project Overview

**VeracityLens** is an AI-powered fake news detection system that classifies news articles into four categories: **True**, **Fake**, **Satire**, and **Bias**. It uses three fine-tuned transformer models (DistilBERT, RoBERTa, XLNet) and provides explainability through token-level importance highlighting.

### Key Features

- Multi-class classification (4 categories)
- 3 transformer models + ensemble voting
- Token-level explainability (gradient attention + SHAP)
- Live news feed integration
- Session-based prediction history
- User feedback system for active learning

---

## Why This Project

### Problem Statement

Misinformation spreads rapidly online, making it difficult for users to distinguish between credible news and fake content. Traditional fact-checking is slow and doesn't scale.

### Solution

An automated system that:

1. **Classifies** news articles in real-time
2. **Explains** predictions with highlighted important words
3. **Learns** from user feedback
4. **Scales** to handle thousands of articles

### Use Cases

- **Journalists**: Quick verification of sources
- **Social Media Platforms**: Automated content moderation
- **Educators**: Teaching media literacy
- **General Public**: Personal fact-checking tool

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  React 18 + Vite + Tailwind CSS + Framer Motion           │
│  (Hosted on Vercel)                                        │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTPS/REST API
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                            │
│  FastAPI + Python 3.9+ (Hosted on HuggingFace Spaces)     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ DistilBERT   │  │   RoBERTa    │  │    XLNet     │     │
│  │   (66M)      │  │   (125M)     │  │   (110M)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                           │                                 │
│                    ┌──────▼──────┐                         │
│                    │  Ensemble   │                         │
│                    │   Voting    │                         │
│                    └─────────────┘                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                        │
├─────────────────────────────────────────────────────────────┤
│  • Supabase (PostgreSQL) - Predictions & History           │
│  • GNews API - Live news feed                              │
│  • HuggingFace Hub - Model hosting                         │
└─────────────────────────────────────────────────────────────┘
```

### Model Architecture

Each transformer model follows this structure:

```
Input Text
    │
    ▼
┌─────────────────┐
│  Tokenization   │  (Convert text to tokens)
│  Max 128 tokens │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embedding      │  (Token → Vector)
│  Layer          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transformer    │  (Self-attention layers)
│  Encoder        │  • DistilBERT: 6 layers
│  Layers         │  • RoBERTa: 12 layers
│                 │  • XLNet: 12 layers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classification │  (Dense layer)
│  Head           │  Output: [True, Fake, Satire, Bias]
│  (4 classes)    │
└────────┬────────┘
         │
         ▼
    Softmax
         │
         ▼
  Probabilities
```

---

## Dataset

### Data Sources

Aggregated from 8 public datasets (~80,000 articles):

| Dataset            | Articles | Labels      | Source                                                                               |
| ------------------ | -------- | ----------- | ------------------------------------------------------------------------------------ |
| ISOT Fake News     | 44,898   | True/Fake   | [Kaggle](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset) |
| LIAR               | 12,836   | Multi-class | [UCSB](https://sites.cs.ucsb.edu/~william/data/liar_dataset.zip)                     |
| BuzzFeed Political | 1,627    | True/Fake   | [GitHub](https://github.com/BuzzFeedNews/2016-10-facebook-fact-check)                |
| PolitiFact         | 1,284    | True/Fake   | [GitHub](https://github.com/several27/FakeNewsCorpus)                                |
| The Onion          | 9,000    | Satire      | [Kaggle](https://www.kaggle.com/datasets/chrisfilo/the-onion-news)                   |
| NotTheOnion        | 8,000    | Satire      | Reddit                                                                               |
| India MythFacts    | 2,500    | Bias        | Custom collection                                                                    |
| Propaganda Dataset | 1,200    | Bias        | [Propaganda Techniques](https://propaganda.qcri.org/)                                |

### Data Preprocessing

**Notebook**: `notebooks/Dataset_Cleaning.ipynb`

**Steps**:

1. **Load** all datasets
2. **Standardize** column names (text, label)
3. **Map labels** to 4 classes:
   - `0` → True
   - `1` → Fake
   - `2` → Satire
   - `3` → Bias
4. **Remove duplicates** (based on text similarity)
5. **Clean text**:
   - Remove URLs, emails, special characters
   - Lowercase conversion
   - Remove extra whitespace
6. **Balance classes** (undersampling majority classes)
7. **Train/Test split** (80/20)
8. **Save** to `data/processed/Dataset_Clean.csv`

### Final Dataset Statistics

| Class     | Training   | Testing    | Total      |
| --------- | ---------- | ---------- | ---------- |
| True      | 12,000     | 3,000      | 15,000     |
| Fake      | 12,000     | 3,000      | 15,000     |
| Satire    | 12,000     | 3,000      | 15,000     |
| Bias      | 8,000      | 2,000      | 10,000     |
| **Total** | **44,000** | **11,000** | **55,000** |

**Published on Kaggle**: [Multi-Class Fake News Dataset](https://www.kaggle.com/datasets/aviseth20/multi-class-fake-news-dataset)

---

## Model Training

### Training Configuration

**Script**: `fake-news-api/src/models/train.py`

**Hyperparameters**:

```python
{
    "epochs": 3,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "max_length": 128,  # tokens
    "weight_decay": 0.01,
    "warmup_ratio": 0.06,
    "optimizer": "AdamW",
    "scheduler": "Linear with warmup"
}
```

### Training Process

1. **Load Dataset**

   ```python
   from src.data.dataset import build_dataset
   tokenized = build_dataset(
       csv_path="data/processed/Dataset_Clean.csv",
       tokenizer_name="distilbert-base-uncased",
       max_length=128
   )
   ```

2. **Initialize Model**

   ```python
   from transformers import AutoModelForSequenceClassification
   model = AutoModelForSequenceClassification.from_pretrained(
       "distilbert-base-uncased",
       num_labels=4,
       id2label={0: "True", 1: "Fake", 2: "Satire", 3: "Bias"},
       label2id={"True": 0, "Fake": 1, "Satire": 2, "Bias": 3}
   )
   ```

3. **Train with HuggingFace Trainer**

   ```python
   from transformers import Trainer, TrainingArguments

   training_args = TrainingArguments(
       output_dir="models/distilbert/checkpoints",
       num_train_epochs=3,
       per_device_train_batch_size=16,
       eval_strategy="epoch",
       save_strategy="epoch",
       load_best_model_at_end=True,
       metric_for_best_model="f1_macro",
       fp16=True  # Mixed precision training
   )

   trainer = Trainer(
       model=model,
       args=training_args,
       train_dataset=tokenized["train"],
       eval_dataset=tokenized["test"],
       compute_metrics=compute_metrics
   )

   trainer.train()
   ```

4. **Save Model**

   ```python
   model.save_pretrained("models/distilbert")
   tokenizer.save_pretrained("models/distilbert")
   ```

5. **Upload to HuggingFace Hub**
   ```python
   model.push_to_hub("aviseth/distilbert-fakenews")
   tokenizer.push_to_hub("aviseth/distilbert-fakenews")
   ```

### Training Results

| Model      | Accuracy | Macro F1 | Training Time | GPU Used  |
| ---------- | -------- | -------- | ------------- | --------- |
| DistilBERT | 85.9%    | 0.848    | ~2 hours      | NVIDIA T4 |
| RoBERTa    | 85.8%    | 0.845    | ~4 hours      | NVIDIA T4 |
| XLNet      | 86.2%    | 0.851    | ~5 hours      | NVIDIA T4 |

### Per-Class Performance

| Class  | DistilBERT F1 | RoBERTa F1 | XLNet F1 |
| ------ | ------------- | ---------- | -------- |
| True   | 0.889         | 0.888      | 0.892    |
| Fake   | 0.872         | 0.879      | 0.876    |
| Satire | 0.998         | 0.998      | 0.997    |
| Bias   | 0.633         | 0.615      | 0.638    |

**Observation**: All models excel at detecting Satire (F1 > 0.99) but struggle with Bias (F1 ~ 0.63) due to subtle linguistic patterns.

---

## Ensemble System

### Voting Strategies

The ensemble combines predictions from all 3 models using three voting methods:

#### 1. Hard Voting

- Each model votes for one label
- Majority wins
- Tie-breaking: highest average confidence

```python
def hard_voting(predictions):
    votes = count_votes(predictions)
    winner = max(votes, key=votes.get)
    confidence = avg_confidence_for_label(predictions, winner)
    return winner, confidence
```

#### 2. Soft Voting (Confidence-Weighted)

- Average probability distributions
- Weighted by model confidence
- More confident models have more influence

```python
def soft_voting(predictions):
    weighted_scores = {}
    total_confidence = sum(p.confidence for p in predictions)

    for label in all_labels:
        weighted_sum = sum(
            p.scores[label] * p.confidence
            for p in predictions
        )
        weighted_scores[label] = weighted_sum / total_confidence

    return weighted_scores
```

#### 3. Weighted Voting (Per-Class F1)

- Uses class-specific F1 scores as weights
- Models weighted by their strength on each class
- Most accurate method

```python
def weighted_voting(predictions):
    class_weights = {
        'distilbert': {'True': 0.889, 'Fake': 0.872, ...},
        'roberta': {'True': 0.888, 'Fake': 0.879, ...},
        'xlnet': {'True': 0.892, 'Fake': 0.876, ...}
    }

    weighted_scores = {}
    for label in all_labels:
        weighted_sum = sum(
            p.scores[label] * class_weights[p.model][label]
            for p in predictions
        )
        weighted_scores[label] = weighted_sum / total_weight

    return weighted_scores
```

### Ensemble Metrics

The ensemble also provides:

- **Uncertainty**: `1 - max(confidence)` — how uncertain the prediction is
- **Model Agreement**: `% of models that agree` — consensus strength

### Performance Optimization

For CPU inference on HuggingFace Spaces:

- **Timeouts**: 45s per model, 60s total
- **Max tokens**: 128 (reduced from 256)
- **Text truncation**: 2000 characters
- **Inference mode**: `torch.inference_mode()` for speed

---

## Backend API

### Technology Stack

- **Framework**: FastAPI 0.104+
- **ML Libraries**: PyTorch 2.0+, Transformers 4.35+
- **Explainability**: SHAP 0.43+
- **Database**: Supabase (PostgreSQL)
- **News API**: GNews
- **Hosting**: HuggingFace Spaces (Docker)

### API Endpoints

#### 1. Single Model Prediction

```http
POST /predict
Content-Type: application/json

{
  "text": "Breaking news: Scientists discover...",
  "model": "distilbert"  // optional: distilbert, roberta, xlnet
}
```

**Response**:

```json
{
  "article_id": "uuid",
  "label": "True",
  "confidence": 0.92,
  "scores": {
    "True": 0.92,
    "Fake": 0.05,
    "Satire": 0.02,
    "Bias": 0.01
  },
  "model_used": "distilbert",
  "explanation": [
    { "token": "scientists", "score": 0.85 },
    { "token": "discover", "score": 0.72 }
  ]
}
```

#### 2. Ensemble Prediction

```http
POST /predict/ensemble
Content-Type: application/json
X-Session-ID: user-session-uuid

{
  "text": "Breaking news: Scientists discover..."
}
```

**Response**:

```json
{
  "article_id": "uuid",
  "primary_prediction": {
    "label": "True",
    "confidence": 0.94,
    "scores": {...}
  },
  "voting_strategies": {
    "hard_voting": {"label": "True", "confidence": 0.93},
    "soft_voting": {"label": "True", "confidence": 0.94},
    "weighted_voting": {"label": "True", "confidence": 0.95}
  },
  "uncertainty": 0.06,
  "model_agreement": 1.0,
  "individual_models": [...],
  "merged_explanation": [...],
  "execution_time_ms": 15234.5
}
```

#### 3. Explainability

```http
POST /explain
Content-Type: application/json

{
  "text": "Breaking news...",
  "model": "distilbert",
  "deep": true  // Include SHAP analysis
}
```

#### 4. Live News Feed

```http
GET /news?query=technology&max_results=10
```

#### 5. Prediction History

```http
GET /history/{session_id}?limit=100
```

#### 6. Statistics

```http
GET /stats
```

**Response**:

```json
{
  "total_predictions": 2041,
  "label_distribution": {
    "True": 45.2,
    "Fake": 28.3,
    "Satire": 15.1,
    "Bias": 11.4
  }
}
```

### Database Schema

**Supabase Tables**:

1. **predictions**

   ```sql
   CREATE TABLE predictions (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     article_id UUID UNIQUE NOT NULL,
     text TEXT NOT NULL,
     predicted_label VARCHAR(10) NOT NULL,
     confidence FLOAT NOT NULL,
     model_name VARCHAR(20) NOT NULL,
     explanation JSONB,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **user_analysis_history**

   ```sql
   CREATE TABLE user_analysis_history (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     session_id UUID NOT NULL,
     article_id UUID REFERENCES predictions(article_id),
     text TEXT NOT NULL,
     predicted_label VARCHAR(10) NOT NULL,
     confidence FLOAT NOT NULL,
     model_name VARCHAR(20) NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **feedback**
   ```sql
   CREATE TABLE feedback (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     article_id UUID REFERENCES predictions(article_id),
     predicted_label VARCHAR(10) NOT NULL,
     actual_label VARCHAR(10) NOT NULL,
     user_comment TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

---

## Frontend Application

### Technology Stack

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **State Management**: React Context API
- **Hosting**: Vercel

### Key Components

#### 1. Home Page

- Text input for article analysis
- Model selector (DistilBERT, RoBERTa, XLNet, Ensemble)
- Real-time prediction display
- Token-level explanation highlighting

#### 2. News Feed

- Live news from GNews API
- Click any article to analyze
- Category filters (technology, politics, health, etc.)

#### 3. Newspaper View

- News grouped by predicted label
- Multi-topic aggregation
- Visual label indicators

#### 4. History Page

- Session-based prediction history
- Filter by label, model, date
- Export functionality

#### 5. Statistics Dashboard

- Total predictions count
- Label distribution pie chart
- Real-time updates

### Theme System

```javascript
// ThemeContext.js
const ThemeContext = createContext({
  theme: "light",
  toggleTheme: () => {},
});

// Supports:
// - Light mode
// - Dark mode
// - System preference detection
// - Persistent storage (localStorage)
```

### Session Tracking

```javascript
// sessionTracker.js
export const getSessionId = () => {
  let sessionId = localStorage.getItem("sessionId");
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem("sessionId", sessionId);
  }
  return sessionId;
};
```

---

## Deployment

### Backend Deployment (HuggingFace Spaces)

**Dockerfile**:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download models at build time
RUN python scripts/download_models.py

# Expose port
EXPOSE 7860

# Run FastAPI
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Environment Variables**:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
GNEWS_API_KEY=xxx
HF_REPO_DISTILBERT=aviseth/distilbert-fakenews
HF_REPO_ROBERTA=aviseth/roberta-fakenews
HF_REPO_XLNET=aviseth/xlnet-fakenews
```

### Frontend Deployment (Vercel)

**vercel.json**:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "env": {
    "VITE_API_URL": "https://aviseth-fake-news-api.hf.space"
  }
}
```

### Model Hosting (HuggingFace Hub)

Models are hosted on HuggingFace Hub:

- `aviseth/distilbert-fakenews`
- `aviseth/roberta-fakenews`
- `aviseth/xlnet-fakenews`

Downloaded at runtime or build time using:

```python
from transformers import AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained(
    "aviseth/distilbert-fakenews"
)
```

---

## Workflow

### End-to-End Prediction Flow

```
1. User Input
   │
   ├─→ Frontend: User enters text or selects news article
   │
   ▼
2. API Request
   │
   ├─→ POST /predict or /predict/ensemble
   │   Headers: X-Session-ID
   │   Body: { text, model }
   │
   ▼
3. Backend Processing
   │
   ├─→ Load model(s) from cache or HuggingFace Hub
   │
   ├─→ Tokenize text (max 128 tokens)
   │
   ├─→ Run inference
   │   • Single model: 5-10s on CPU
   │   • Ensemble: 15-45s on CPU (3 models in parallel)
   │
   ├─→ Calculate token importance (gradient attention)
   │
   ├─→ Apply voting strategies (ensemble only)
   │
   ▼
4. Database Storage
   │
   ├─→ Store prediction in Supabase
   │   • predictions table
   │   • user_analysis_history table (if session_id provided)
   │
   ▼
5. Response
   │
   ├─→ Return JSON with:
   │   • Label & confidence
   │   • Probability distribution
   │   • Token explanations
   │   • Voting results (ensemble)
   │   • Uncertainty & agreement metrics
   │
   ▼
6. Frontend Display
   │
   ├─→ Show prediction with color-coded label
   │
   ├─→ Highlight important tokens
   │
   ├─→ Display voting strategies (ensemble)
   │
   └─→ Add to history
```

### Training to Deployment Flow

```
1. Data Collection
   │
   ├─→ Aggregate 8 datasets (~80k articles)
   │
   ▼
2. Data Preprocessing
   │
   ├─→ Clean, standardize, balance
   │   Notebook: Dataset_Cleaning.ipynb
   │
   ├─→ Save to data/processed/Dataset_Clean.csv
   │
   ▼
3. Model Training
   │
   ├─→ Train 3 models (DistilBERT, RoBERTa, XLNet)
   │   Script: src/models/train.py
   │   GPU: NVIDIA T4
   │   Time: 2-5 hours per model
   │
   ├─→ Evaluate on test set
   │   Script: src/models/evaluate.py
   │
   ▼
4. Model Upload
   │
   ├─→ Push to HuggingFace Hub
   │   • aviseth/distilbert-fakenews
   │   • aviseth/roberta-fakenews
   │   • aviseth/xlnet-fakenews
   │
   ▼
5. Backend Development
   │
   ├─→ Build FastAPI application
   │   • Inference endpoints
   │   • Ensemble logic
   │   • Explainability
   │
   ├─→ Test locally
   │
   ▼
6. Backend Deployment
   │
   ├─→ Deploy to HuggingFace Spaces
   │   • Docker container
   │   • Auto-download models
   │   • CPU inference
   │
   ▼
7. Frontend Development
   │
   ├─→ Build React application
   │   • UI components
   │   • API integration
   │   • Theme system
   │
   ├─→ Test locally
   │
   ▼
8. Frontend Deployment
   │
   ├─→ Deploy to Vercel
   │   • Automatic builds on push
   │   • CDN distribution
   │
   ▼
9. Integration Testing
   │
   ├─→ Test full flow
   │   • Prediction accuracy
   │   • Response times
   │   • Error handling
   │
   ▼
10. Production
    │
    └─→ Live at veracitylens.vercel.app
```

---

## Performance Metrics

### Inference Speed

| Environment                 | Single Model | Ensemble |
| --------------------------- | ------------ | -------- |
| Local GPU (NVIDIA RTX 3060) | 0.5-1s       | 1-2s     |
| HuggingFace Spaces CPU      | 5-10s        | 15-45s   |

### API Response Times

| Endpoint          | Average | P95 | P99 |
| ----------------- | ------- | --- | --- |
| /predict          | 6s      | 12s | 15s |
| /predict/ensemble | 25s     | 45s | 60s |
| /news             | 1s      | 2s  | 3s  |
| /history          | 0.5s    | 1s  | 2s  |

### Database Performance

- **Predictions stored**: 2000+
- **Average query time**: 50ms
- **Storage used**: ~15MB / 500MB limit

---

## Future Enhancements

1. **GPU Inference**: Migrate to GPU-enabled hosting for faster predictions
2. **Model Distillation**: Create smaller, faster models
3. **Multi-language Support**: Extend to non-English articles
4. **Real-time Monitoring**: Add model drift detection
5. **Active Learning**: Retrain models with user feedback
6. **Browser Extension**: Chrome/Firefox extension for in-page analysis
7. **Mobile App**: Native iOS/Android applications
8. **API Rate Limiting**: Implement tiered API access
9. **Caching**: Redis cache for frequently analyzed articles
10. **A/B Testing**: Compare model versions in production

---

## Team

| Name         | Role                 | GitHub                                           | Email                   |
| ------------ | -------------------- | ------------------------------------------------ | ----------------------- |
| Avi Seth     | ML Engineer, Backend | [@AviSeth20](https://github.com/AviSeth20)       | aviseth6146@gmail.com   |
| Shweta Bisht | Frontend Developer   | [@shweta-bisht](https://github.com/shweta-bisht) | sbshweta1311@gmail.com  |
| Aliza Khan   | Data Scientist       | [@alizakhann2](https://github.com/Alizakhann2)   | alizakhan.dps@gmail.com |

---

## Links

- **Live Demo**: [veracitylens.vercel.app](https://veracitylens.vercel.app)
- **API Docs**: [HuggingFace Spaces](https://huggingface.co/spaces/aviseth/fake-news-api)
- **GitHub**: [AviSeth20/VeracityLens](https://github.com/AviSeth20/VeracityLens)
- **Dataset**: [Kaggle](https://www.kaggle.com/datasets/aviseth20/multi-class-fake-news-dataset)
- **Models**:
  - [DistilBERT](https://huggingface.co/aviseth/distilbert-fakenews)
  - [RoBERTa](https://huggingface.co/aviseth/roberta-fakenews)
  - [XLNet](https://huggingface.co/aviseth/xlnet-fakenews)

---

<div align="center">
<sub>Built with PyTorch, HuggingFace Transformers, FastAPI, and React</sub>
</div>
