# Design Document: Phase 3 Enhancements

## Overview

Phase 3 closes the model improvement loop by adding:

1. **Active Learning** — surface the most uncertain predictions for human review
2. **Model Registry** — version, track, and deploy model checkpoints
3. **A/B Testing** — safely validate challenger models against production traffic
4. **Confidence Calibration** — temperature scaling to align confidence with true accuracy
5. **Automated Monitoring** — rolling accuracy, drift detection, and retrain alerts

## Architecture

### New Components

```
Backend (fake-news-api/src/)
├── api/main.py              ← new endpoints: /active-learning/*, /models/registry, /ab-test/*, /monitoring/*
├── models/inference.py      ← MODIFIED: temperature scaling, dynamic model loading
├── models/calibration.py    ← NEW: temperature scaling computation
├── utils/ab_router.py       ← NEW: deterministic A/B traffic routing
├── utils/drift_detector.py  ← NEW: Jensen-Shannon divergence computation
└── scripts/retrain.py       ← MODIFIED: --auto flag, registry insert, webhook

Frontend (frontend/src/)
├── pages/AnalyticsPage.jsx  ← MODIFIED: accuracy gauge, drift chart, retrain banner
└── pages/AnnotationQueue.jsx ← NEW: admin annotation interface
```

### Database Schema

```sql
CREATE TABLE model_registry (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      VARCHAR(50) NOT NULL,
    version         VARCHAR(20) NOT NULL,
    accuracy        FLOAT,
    f1_macro        FLOAT,
    training_samples INT,
    feedback_samples INT,
    temperature     FLOAT DEFAULT 1.0,
    trained_at      TIMESTAMPTZ DEFAULT NOW(),
    deployed_at     TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT FALSE,
    notes           TEXT
);

CREATE TABLE label_distributions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    week_start  DATE        NOT NULL,
    true_pct    FLOAT,
    fake_pct    FLOAT,
    satire_pct  FLOAT,
    bias_pct    FLOAT,
    total       INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS ab_variant VARCHAR(20);
ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS temperature FLOAT DEFAULT 1.0;
```

---

## Feature 1: Active Learning

### Uncertainty Sampling

```python
# fake-news-api/src/api/main.py

import math

@app.get("/active-learning/samples")
async def get_active_learning_samples(
    limit: int = Query(20, ge=1, le=100),
    strategy: str = Query("uncertainty"),
    authorization: Optional[str] = Header(None)
):
    if authorization != f"Bearer {os.getenv('ADMIN_TOKEN')}":
        raise HTTPException(status_code=401)

    # Get predictions without feedback
    predictions = supabase.client.table("predictions").select("*").execute().data
    feedback_ids = {f["article_id"] for f in supabase.client.table("feedback").select("article_id").execute().data}
    candidates = [p for p in predictions if p["article_id"] not in feedback_ids]

    # Score by uncertainty
    def entropy(scores: dict) -> float:
        return -sum(p * math.log(p + 1e-10) for p in scores.values())

    def margin(scores: dict) -> float:
        sorted_scores = sorted(scores.values(), reverse=True)
        return sorted_scores[0] - sorted_scores[1]

    if strategy == "uncertainty":
        candidates.sort(key=lambda p: entropy(p.get("scores", {})), reverse=True)
    else:
        candidates.sort(key=lambda p: margin(p.get("scores", {})))

    return {"samples": candidates[:limit], "strategy": strategy, "total_candidates": len(candidates)}
```

### Annotation Queue Frontend

```jsx
// frontend/src/pages/AnnotationQueue.jsx
export default function AnnotationQueue() {
  const [samples, setSamples] = useState([]);

  const handleLabel = async (articleId, predictedLabel, actualLabel) => {
    await submitFeedback(articleId, predictedLabel, actualLabel);
    setSamples((prev) => prev.filter((s) => s.article_id !== articleId));
  };

  return (
    <div>
      {samples.map((sample) => (
        <div key={sample.article_id}>
          <p>{sample.text_preview}</p>
          <p>
            Model predicted: <strong>{sample.predicted_label}</strong> (
            {Math.round(sample.confidence * 100)}%)
          </p>
          <div className="flex gap-2">
            {["True", "Fake", "Satire", "Bias"].map((label) => (
              <button
                key={label}
                onClick={() =>
                  handleLabel(sample.article_id, sample.predicted_label, label)
                }
                className={
                  label === sample.predicted_label
                    ? "border-2 border-[#d97757]"
                    : ""
                }
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Feature 2: Model Registry

### Registry Table Operations

```python
# In supabase_client.py

def register_model(self, model_name: str, version: str, accuracy: float,
                   f1_macro: float, training_samples: int, feedback_samples: int,
                   temperature: float = 1.0, notes: str = "") -> dict:
    data = {
        "model_name": model_name,
        "version": version,
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "training_samples": training_samples,
        "feedback_samples": feedback_samples,
        "temperature": temperature,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "is_active": False,
        "notes": notes
    }
    return self.client.table("model_registry").insert(data).execute().data

def deploy_model(self, registry_id: str, model_name: str):
    # Deactivate all versions of this model
    self.client.table("model_registry").update({"is_active": False}).eq("model_name", model_name).execute()
    # Activate the specified version
    self.client.table("model_registry").update({
        "is_active": True,
        "deployed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", registry_id).execute()
```

### Dynamic Model Loading

```python
# In inference.py - add reload capability

def reload_from_registry(self, registry_entry: dict):
    """Hot-reload model weights from a new registry entry."""
    new_source = registry_entry.get("hf_repo") or str(MODELS_DIR / self.model_key)
    self._model = None
    self._tokenizer = None
    self.temperature = registry_entry.get("temperature", 1.0)
    # Next call to .model property will trigger _load() with new source
```

---

## Feature 3: A/B Testing

### Deterministic Routing

```python
# fake-news-api/src/utils/ab_router.py

import hashlib

class ABRouter:
    def __init__(self):
        self.config = None  # loaded from Supabase on startup

    def get_variant(self, session_id: str) -> str:
        """Deterministically assign session to champion or challenger."""
        if not self.config or not self.config.get("is_active"):
            return "champion"

        # Hash session_id to get consistent 0-1 value
        hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        normalized = (hash_val % 10000) / 10000.0

        if normalized < self.config["traffic_split"]:
            return "challenger"
        return "champion"

    def load_config(self, supabase_client):
        rows = supabase_client.table("ab_tests").select("*").eq("is_active", True).execute().data
        self.config = rows[0] if rows else None

ab_router = ABRouter()
```

### A/B Results Endpoint

```python
@app.get("/ab-test/results")
async def get_ab_results(authorization: Optional[str] = Header(None)):
    if authorization != f"Bearer {os.getenv('ADMIN_TOKEN')}":
        raise HTTPException(status_code=401)

    # Get predictions tagged with ab_variant
    preds = supabase.client.table("predictions").select("ab_variant, article_id").execute().data
    feedback = {f["article_id"]: f for f in supabase.client.table("feedback").select("*").execute().data}

    champion = [p for p in preds if p.get("ab_variant") == "champion"]
    challenger = [p for p in preds if p.get("ab_variant") == "challenger"]

    def accuracy(group):
        labeled = [p for p in group if p["article_id"] in feedback]
        if not labeled:
            return None, 0
        correct = sum(1 for p in labeled if feedback[p["article_id"]]["actual_label"] == p.get("predicted_label"))
        return correct / len(labeled), len(labeled)

    champ_acc, champ_n = accuracy(champion)
    chal_acc, chal_n = accuracy(challenger)

    return {
        "champion": {"accuracy": champ_acc, "samples": champ_n},
        "challenger": {"accuracy": chal_acc, "samples": chal_n},
    }
```

---

## Feature 4: Confidence Calibration

### Temperature Scaling

```python
# fake-news-api/src/models/calibration.py

import torch
import numpy as np

def find_optimal_temperature(logits: np.ndarray, labels: np.ndarray,
                              temps: list = None) -> float:
    """
    Grid search for temperature that minimizes NLL on validation set.
    Returns optimal temperature scalar.
    """
    if temps is None:
        temps = [t / 10 for t in range(1, 50)]  # 0.1 to 4.9

    best_temp, best_nll = 1.0, float('inf')
    logits_t = torch.tensor(logits, dtype=torch.float32)
    labels_t = torch.tensor(labels, dtype=torch.long)

    for temp in temps:
        scaled = logits_t / temp
        nll = torch.nn.functional.cross_entropy(scaled, labels_t).item()
        if nll < best_nll:
            best_nll = nll
            best_temp = temp

    return best_temp


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error — lower is better."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        mask = (probs >= lo) & (probs < hi)
        if mask.sum() == 0:
            continue
        bin_acc = (labels[mask] == probs[mask].argmax(axis=1)).mean()
        bin_conf = probs[mask].max(axis=1).mean()
        ece += mask.mean() * abs(bin_acc - bin_conf)
    return float(ece)
```

### Apply Temperature in Inference

```python
# In FakeNewsClassifier.predict():

with torch.no_grad():
    outputs = self.model(**inputs)
    # Apply temperature scaling if set
    temperature = getattr(self, 'temperature', 1.0)
    calibrated_logits = outputs.logits / temperature
    probs = torch.softmax(calibrated_logits, dim=-1)[0].cpu().numpy()
```

---

## Feature 5: Monitoring & Drift Detection

### Rolling Accuracy

```python
@app.get("/monitoring/accuracy")
async def get_rolling_accuracy():
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    feedback = supabase.client.table("feedback").select("*").gte("created_at", cutoff).execute().data

    if not feedback:
        return {"rolling_accuracy": None, "total_feedback_last_7d": 0, "trend": "insufficient_data"}

    correct = sum(1 for f in feedback if f["predicted_label"] == f["actual_label"])
    accuracy = correct / len(feedback)

    if accuracy < 0.75:
        logger.warning(f"Model accuracy below threshold: {accuracy:.2%}")

    return {
        "rolling_accuracy": round(accuracy, 4),
        "total_feedback_last_7d": len(feedback),
        "accuracy_trend": "degrading" if accuracy < 0.75 else "stable",
    }
```

### Jensen-Shannon Drift Detection

```python
# fake-news-api/src/utils/drift_detector.py

import numpy as np

def jensen_shannon_divergence(p: dict, q: dict) -> float:
    """JS divergence between two label distributions. Range: [0, 1]."""
    labels = ['True', 'Fake', 'Satire', 'Bias']
    p_arr = np.array([p.get(l, 0) for l in labels], dtype=float)
    q_arr = np.array([q.get(l, 0) for l in labels], dtype=float)

    # Normalize
    p_arr = p_arr / p_arr.sum() if p_arr.sum() > 0 else p_arr
    q_arr = q_arr / q_arr.sum() if q_arr.sum() > 0 else q_arr

    m = (p_arr + q_arr) / 2
    def kl(a, b):
        mask = a > 0
        return np.sum(a[mask] * np.log(a[mask] / b[mask]))

    return float((kl(p_arr, m) + kl(q_arr, m)) / 2)
```

---

## Retrain Script Extensions

```python
# scripts/retrain.py additions

def auto_retrain(model_key: str, min_samples: int = 50):
    """Full automated pipeline: fetch → train → evaluate → register."""
    supabase = get_supabase_client()

    # Check if enough new feedback since last retrain
    last_retrain = supabase.client.table("model_registry") \
        .select("trained_at").eq("model_name", model_key).eq("is_active", True) \
        .execute().data
    cutoff = last_retrain[0]["trained_at"] if last_retrain else "2000-01-01"

    new_feedback = supabase.client.table("feedback") \
        .select("*").gte("created_at", cutoff).execute().data

    if len(new_feedback) < min_samples:
        print(f"Only {len(new_feedback)} new samples (need {min_samples}). Aborting.")
        return

    # Export feedback CSV
    csv_path = f"/tmp/feedback_{model_key}.csv"
    pd.DataFrame(new_feedback).to_csv(csv_path, index=False)

    # Train
    metrics = retrain(model_key, csv_path, epochs=3, output_dir=f"/tmp/{model_key}_retrained")

    # Register
    supabase.register_model(
        model_name=model_key,
        version=f"v{datetime.now().strftime('%Y%m%d')}",
        accuracy=metrics["eval_accuracy"],
        f1_macro=metrics["eval_f1_macro"],
        training_samples=metrics["train_samples"],
        feedback_samples=len(new_feedback),
    )

    # Webhook notification
    webhook_url = os.getenv("RETRAIN_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={
            "model": model_key,
            "accuracy": metrics["eval_accuracy"],
            "samples": len(new_feedback),
        })
```

---

## API Summary

| Method | Path                           | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| GET    | `/active-learning/samples`     | Top uncertain predictions for annotation |
| GET    | `/active-learning/queue`       | Formatted annotation queue               |
| GET    | `/models/registry`             | All model versions                       |
| POST   | `/models/registry/{id}/deploy` | Deploy a model version                   |
| GET    | `/models/calibration`          | ECE for each model                       |
| POST   | `/ab-test/start`               | Start A/B test                           |
| POST   | `/ab-test/stop`                | Stop A/B test                            |
| GET    | `/ab-test/results`             | Champion vs challenger accuracy          |
| GET    | `/monitoring/accuracy`         | Rolling 7-day accuracy                   |
| GET    | `/monitoring/drift`            | Label distribution drift score           |

---

## Free Tier Compliance

- Model registry: ~100 rows max, negligible storage
- A/B routing: in-memory hash, zero DB queries per request
- Temperature scaling: single float division, no overhead
- Drift detection: background task every 24h, not per-request
- Monitoring accuracy: 5-minute cache, ~1 Supabase query per 5 minutes
