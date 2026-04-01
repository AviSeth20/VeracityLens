# Design Document: Phase 2 Enhancements

## Overview

Phase 2 adds three major capabilities to VeracityLens:

1. **URL Analysis** — fetch and analyze articles directly from URLs using `newspaper3k`
2. **Analytics Dashboard** — platform-wide and per-user prediction statistics with charts
3. **Feedback-Driven Retraining** — export corrections as training data and fine-tune models

All features extend the existing FastAPI backend and React frontend without changing the core inference pipeline.

## Architecture

### New Components

```
Backend (fake-news-api/src/)
├── api/main.py              ← new endpoints: /analyze/url, /feedback/stats, /feedback/export, extended /stats
├── utils/article_extractor.py  ← NEW: URL fetch + article text extraction
└── scripts/retrain.py       ← NEW: feedback-driven fine-tuning script

Frontend (frontend/src/)
├── pages/AnalyticsPage.jsx  ← NEW: platform analytics dashboard
├── components/AnalysisInput.jsx  ← MODIFIED: add URL tab
├── components/ResultCard.jsx     ← MODIFIED: share button, confidence calibration, source badge
└── components/Header.jsx         ← MODIFIED: add Analytics nav link
```

---

## Feature 1: URL Analysis

### Backend — Article Extractor

**Location**: `fake-news-api/src/utils/article_extractor.py`

Uses `newspaper3k` (already in requirements.txt) for extraction with a `requests` fallback.

```python
import requests
from newspaper import Article
from typing import Optional

def extract_article(url: str, timeout: int = 10) -> dict:
    """
    Fetch and extract article text from a URL.
    Returns: { text, title, source_domain, word_count }
    Raises: ValueError with user-friendly message on failure
    """
    # Validate URL scheme
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        raise ValueError(f"Could not fetch article: {str(e)}")

    text = article.text.strip()
    if len(text) < 100:
        raise ValueError("Could not extract article content")

    return {
        "text": text,
        "title": article.title or "",
        "source_domain": article.source_url or "",
        "word_count": len(text.split()),
    }
```

### Backend — New Endpoint

```python
class UrlAnalysisRequest(BaseModel):
    url: str
    model: Optional[str] = "distilbert"

@app.post("/analyze/url")
async def analyze_url(request: UrlAnalysisRequest, background_tasks: BackgroundTasks,
                      x_session_id: Optional[str] = Header(None)):
    try:
        extracted = extract_article(request.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Reuse existing predict logic
    result = predict(extracted["text"], request.model)
    result["source_url"] = request.url
    result["source_domain"] = extracted["source_domain"]
    result["extracted_text"] = extracted["text"]

    # Store with source_url
    background_tasks.add_task(store_prediction_bg, ...)
    return result
```

### Frontend — URL Tab in AnalysisInput

Add a tab switcher to `AnalysisInput.jsx`:

```jsx
const [inputMode, setInputMode] = useState('text') // 'text' | 'url'
const [urlInput, setUrlInput] = useState('')

// Tab bar
<div className="flex border-b ...">
  <button onClick={() => setInputMode('text')} className={inputMode === 'text' ? 'active' : ''}>
    Text
  </button>
  <button onClick={() => setInputMode('url')} className={inputMode === 'url' ? 'active' : ''}>
    URL
  </button>
</div>

// Conditional input
{inputMode === 'url' ? (
  <input
    type="url"
    value={urlInput}
    onChange={e => setUrlInput(e.target.value)}
    placeholder="https://example.com/article"
  />
) : (
  <textarea value={text} onChange={...} />
)}
```

When URL analysis completes, switch to text tab and populate with extracted text.

---

## Feature 2: Analytics Dashboard

### Backend — Extended `/stats` Endpoint

Extend `get_prediction_stats()` in `supabase_client.py`:

```python
def get_prediction_stats(self) -> Dict[str, Any]:
    total = self.client.table("predictions").select("*", count="exact").execute()

    # by_label
    rows = self.client.table("predictions").select("predicted_label, model_name, created_at").execute()

    by_label = {}
    by_model = {}
    daily_counts = {}  # last 7 days: { "2026-03-29": 12, ... }

    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    for row in rows.data:
        # label counts
        lbl = row["predicted_label"]
        by_label[lbl] = by_label.get(lbl, 0) + 1

        # model counts
        mdl = row["model_name"]
        by_model[mdl] = by_model.get(mdl, 0) + 1

        # daily counts (last 7 days)
        if row["created_at"] >= cutoff:
            day = row["created_at"][:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1

    return {
        "total_predictions": total.count,
        "by_label": by_label,
        "by_model": by_model,
        "daily_counts": daily_counts,
    }
```

Add 60-second response caching using a simple in-memory dict with timestamp.

### Backend — Extended `/history/{session_id}`

Add `summary` field to the history response:

```python
summary = {
    "total": len(history),
    "by_label": {},
    "avg_confidence": 0.0,
    "most_used_model": None,
}
if history:
    for item in history:
        lbl = item["predicted_label"]
        summary["by_label"][lbl] = summary["by_label"].get(lbl, 0) + 1
    summary["avg_confidence"] = round(
        sum(h["confidence"] for h in history) / len(history), 4
    )
    summary["most_used_model"] = max(
        {h["model_name"] for h in history},
        key=lambda m: sum(1 for h in history if h["model_name"] == m)
    )
```

### Frontend — AnalyticsPage

**Location**: `frontend/src/pages/AnalyticsPage.jsx`

Uses Recharts (lightweight, tree-shakeable) for charts.

```jsx
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const LABEL_COLORS = {
  True: "#16a34a",
  Fake: "#dc2626",
  Satire: "#7c3aed",
  Bias: "#d97706",
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () =>
      getStats()
        .then(setStats)
        .catch(() => setError(true))
        .finally(() => setLoading(false));
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, []);

  // Label distribution pie chart
  // Model usage bar chart
  // 7-day volume trend bar chart
  // Feedback agreement rate
}
```

---

## Feature 3: Feedback Enhancement & Export

### Backend — Updated Feedback Storage

Add `session_id` to feedback table:

```sql
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
```

Update `store_feedback()` to accept and store `session_id`.

### Backend — `/feedback/stats` Endpoint

```python
@app.get("/feedback/stats")
async def get_feedback_stats():
    rows = supabase.client.table("feedback").select("predicted_label, actual_label").execute()
    total = len(rows.data)
    agreed = sum(1 for r in rows.data if r["predicted_label"] == r["actual_label"])
    by_label = {}
    for r in rows.data:
        lbl = r["actual_label"]
        by_label[lbl] = by_label.get(lbl, 0) + 1
    return {
        "total_corrections": total,
        "agreement_rate": round(agreed / total, 4) if total else 0,
        "corrections_by_label": by_label,
    }
```

### Backend — `/feedback/export` Endpoint

```python
import csv, io
from fastapi.responses import StreamingResponse

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

@app.get("/feedback/export")
async def export_feedback(authorization: Optional[str] = Header(None)):
    if not ADMIN_TOKEN or authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Join feedback with predictions to get article text
    feedback = supabase.client.table("feedback").select("*").execute().data
    corrections = [f for f in feedback if f["predicted_label"] != f["actual_label"]]

    # Deduplicate by article_id (keep most recent)
    seen = {}
    for row in sorted(corrections, key=lambda x: x["created_at"]):
        seen[row["article_id"]] = row

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["article_id", "actual_label", "created_at"])
    writer.writeheader()
    writer.writerows(seen.values())

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback_corrections.csv"}
    )
```

### Retraining Script

**Location**: `fake-news-api/scripts/retrain.py`

```python
"""
Fine-tune a model on user feedback corrections.

Usage:
    python scripts/retrain.py --model distilbert --feedback-csv feedback.csv --epochs 3 --output-dir models/distilbert-v2
"""
import argparse, json
from pathlib import Path
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score

LABEL2ID = {"True": 0, "Fake": 1, "Satire": 2, "Bias": 3}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}

def load_and_merge(feedback_csv: str, original_csv: str, sample_size: int = 1000) -> pd.DataFrame:
    """Merge feedback corrections with a sample of original data to prevent forgetting."""
    feedback = pd.read_csv(feedback_csv)
    feedback = feedback.rename(columns={"actual_label": "label_text"})

    original = pd.read_csv(original_csv).sample(min(sample_size, len(pd.read_csv(original_csv))))

    combined = pd.concat([feedback, original], ignore_index=True)
    combined["label"] = combined["label_text"].map(LABEL2ID)
    return combined.dropna(subset=["text", "label"])

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
    }

def retrain(model_key: str, feedback_csv: str, epochs: int, output_dir: str):
    model_path = str(Path(__file__).parents[1] / "models" / model_key)
    original_csv = str(Path(__file__).parents[2] / "data" / "processed" / "Dataset_Clean.csv")

    df = load_and_merge(feedback_csv, original_csv)
    split = int(len(df) * 0.9)
    train_df, val_df = df[:split], df[split:]

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=4)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=256, padding="max_length")

    train_ds = Dataset.from_pandas(train_df[["text", "label"]]).map(tokenize, batched=True)
    val_ds = Dataset.from_pandas(val_df[["text", "label"]]).map(tokenize, batched=True)

    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=16,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
    )

    trainer = Trainer(model=model, args=args, train_dataset=train_ds,
                      eval_dataset=val_ds, compute_metrics=compute_metrics)
    trainer.train()

    # Evaluate and guard against regression
    metrics = trainer.evaluate()
    log = {"model": model_key, "epochs": epochs, "metrics": metrics}
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "retrain_log.json").write_text(json.dumps(log, indent=2))

    # Load original accuracy from metrics.json
    orig_metrics_path = Path(model_path) / "metrics.json"
    if orig_metrics_path.exists():
        orig = json.loads(orig_metrics_path.read_text())
        orig_acc = orig.get("eval_accuracy", 0)
        new_acc = metrics.get("eval_accuracy", 0)
        if new_acc < orig_acc - 0.02:
            print(f"⚠️  Accuracy dropped from {orig_acc:.3f} to {new_acc:.3f} — aborting save")
            return

    trainer.save_model(output_dir)
    print(f"✅ Saved retrained model to {output_dir}")
    print(f"   Accuracy: {metrics.get('eval_accuracy', 0):.4f}")
    print(f"   F1 Macro: {metrics.get('eval_f1_macro', 0):.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=["distilbert", "roberta", "xlnet"])
    parser.add_argument("--feedback-csv", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    retrain(args.model, args.feedback_csv, args.epochs, args.output_dir)
```

---

## Feature 4: ResultCard Enhancements

### Confidence Calibration Badge

Add to `ResultCard.jsx`:

```jsx
function ConfidenceBadge({ confidence }) {
  const pct = Math.round(confidence * 100);
  if (pct >= 90)
    return (
      <span className="text-xs text-green-600 dark:text-green-400">
        High confidence
      </span>
    );
  if (pct >= 65)
    return (
      <span className="text-xs text-amber-600 dark:text-amber-400">
        Moderate confidence
      </span>
    );
  return (
    <span className="text-xs text-red-600 dark:text-red-400">
      Low confidence — treat with caution
    </span>
  );
}
```

### Share Button

```jsx
async function handleShare(label, confidence) {
  const text = `VeracityLens analyzed this article as ${label} with ${Math.round(confidence * 100)}% confidence. Check it at https://veracitylens.vercel.app`;
  try {
    await navigator.clipboard.writeText(text);
    setToast("Copied to clipboard!");
    setTimeout(() => setToast(null), 2000);
  } catch {
    setShowShareModal(true);
  }
}
```

### Download Report

```jsx
function downloadReport(result) {
  const lines = [
    `VeracityLens Analysis Report`,
    `Generated: ${new Date().toLocaleString()}`,
    ``,
    `Prediction: ${result.label || result.primary_prediction?.label}`,
    `Confidence: ${Math.round((result.confidence || result.primary_prediction?.confidence) * 100)}%`,
    `Model: ${result.model_used || "ensemble"}`,
    ``,
    `Article Preview:`,
    result._text?.slice(0, 500) || "",
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `veracitylens-report-${Date.now()}.txt`;
  a.click();
}
```

---

## Database Changes

```sql
-- Add source_url to predictions table
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS source_url TEXT;

-- Add session_id to feedback table
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
```

---

## API Summary

| Method | Path                    | Description                               |
| ------ | ----------------------- | ----------------------------------------- |
| POST   | `/analyze/url`          | Fetch and analyze article from URL        |
| GET    | `/stats`                | Extended: includes by_model, daily_counts |
| GET    | `/history/{session_id}` | Extended: includes summary field          |
| GET    | `/feedback/stats`       | Agreement rate and correction counts      |
| GET    | `/feedback/export`      | CSV export of corrections (admin only)    |

---

## Free Tier Compliance

- `newspaper3k` runs in-process on HF Spaces CPU — no external service needed
- Recharts adds ~50KB gzipped to the frontend bundle — well within Vercel limits
- Stats caching (60s) reduces Supabase queries from ~1/request to ~1/minute
- Retraining runs locally or on Colab — not on HF Spaces
