"""
Fetches live GNews articles and appends them to the training dataset.

Usage:
    python -m src.data.gnews_collector              # fetch and save
    python -m src.data.gnews_collector --preview    # print without saving
    python -m src.data.gnews_collector --label --model-path models/distilbert --merge
"""

from src.data.preprocessing import clean_text
from src.utils.gnews_client import GNewsClient
import os
import sys
import uuid
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parents[2]))
load_dotenv()


PROJECT_ROOT = Path(__file__).parents[2]
AUGMENTED_DIR = PROJECT_ROOT / "data" / "augmented"
CLEAN_CSV = PROJECT_ROOT / "data" / "processed" / "Dataset_Clean.csv"

FETCH_TOPICS = [
    "scientific research breakthrough",
    "official government announcement",
    "verified breaking news",
    "conspiracy theory debunked",
    "fact check false claim",
    "misinformation viral",
    "satire news comedy",
    "parody news article",
    "political opinion editorial",
    "partisan news analysis",
]

MAX_PER_TOPIC = 5


def fetch_articles(max_per_topic: int = MAX_PER_TOPIC) -> list[dict]:
    client = GNewsClient()
    all_articles = []
    seen_urls: set[str] = set()

    for topic in FETCH_TOPICS:
        try:
            articles = client.search_news(
                query=topic, max_results=max_per_topic)
            for a in articles:
                url = a.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(a)
            print(f"  ✓ '{topic}' → {len(articles)} articles")
        except Exception as e:
            print(f"  ✗ '{topic}' → error: {e}")

    print(f"\n[collector] Fetched {len(all_articles)} unique articles\n")
    return all_articles


def articles_to_dataframe(articles: list[dict]) -> pd.DataFrame:
    """Convert raw GNews articles to Dataset_Clean.csv schema. Labels are set to -1 (unlabelled)."""
    rows = []
    for a in articles:
        title = clean_text(a.get("title", ""))
        content = clean_text(a.get("content", "") or a.get("description", ""))
        text = content if len(content) > 30 else title
        if len(text) < 10:
            continue
        rows.append({
            "id":             f"GNEWS_{uuid.uuid4().hex[:8].upper()}",
            "title":          title,
            "content":        content,
            "label": -1,
            "label_text":     "UNLABELLED",
            "label_original": "gnews_live",
            "source_dataset": "GNews_Live",
            "topic":          "",
            "url":            a.get("url", ""),
            "speaker":        a.get("source", ""),
            "fetched_at":     datetime.utcnow().isoformat(),
        })
    return pd.DataFrame(rows)


def pseudo_label(df: pd.DataFrame, model_path: str) -> pd.DataFrame:
    """Assign pseudo-labels to unlabelled articles using a trained model."""
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    ID2LABEL = {0: "True", 1: "Fake", 2: "Satire", 3: "Bias"}
    print(f"[pseudo_label] Loading model from {model_path}…")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    texts = df["content"].fillna(df["title"]).tolist()
    labels = []
    confidences = []

    for i in range(0, len(texts), 16):
        batch = texts[i: i + 16]
        enc = tokenizer(batch, padding=True, truncation=True,
                        max_length=256, return_tensors="pt").to(device)
        with torch.no_grad():
            probs = torch.softmax(model(**enc).logits, dim=-1)
        labels.extend(probs.argmax(dim=-1).cpu().tolist())
        confidences.extend(probs.max(dim=-1).values.cpu().tolist())

    df = df.copy()
    df["label"] = labels
    df["label_text"] = [ID2LABEL[l] for l in labels]
    df["confidence"] = [round(c, 4) for c in confidences]
    print(
        f"[pseudo_label] Label distribution:\n{df['label_text'].value_counts().to_string()}")
    return df


def save_augmented(df: pd.DataFrame, tag: str = "") -> Path:
    AUGMENTED_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"gnews_{ts}{('_' + tag) if tag else ''}.csv"
    path = AUGMENTED_DIR / name
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"[collector] Saved {len(df)} rows → {path}")
    return path


def merge_into_training(augmented_path: Path, min_confidence: float = 0.80) -> int:
    """Merge pseudo-labelled articles into Dataset_Clean.csv, filtered by confidence threshold."""
    aug_df = pd.read_csv(augmented_path)
    if "confidence" in aug_df.columns:
        aug_df = aug_df[aug_df["confidence"] >= min_confidence]
    aug_df = aug_df[aug_df["label"] != -1]

    if len(aug_df) == 0:
        print("[merge] No rows met the confidence threshold.")
        return 0

    keep_cols = ["id", "title", "content", "label", "label_text",
                 "label_original", "source_dataset", "topic", "url", "speaker"]
    aug_df = aug_df[[c for c in keep_cols if c in aug_df.columns]]
    aug_df.to_csv(CLEAN_CSV, mode="a", header=False,
                  index=False, encoding="utf-8")
    print(f"[merge] Added {len(aug_df)} rows to {CLEAN_CSV}")
    return len(aug_df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview",       action="store_true")
    parser.add_argument("--label",         action="store_true")
    parser.add_argument("--model-path",    type=str,
                        default="models/distilbert")
    parser.add_argument("--merge",         action="store_true")
    parser.add_argument("--min-conf",      type=float, default=0.80)
    parser.add_argument("--max-per-topic", type=int,   default=MAX_PER_TOPIC)
    args = parser.parse_args()

    articles = fetch_articles(max_per_topic=args.max_per_topic)
    df = articles_to_dataframe(articles)

    if args.preview:
        print(df[["title", "source_dataset", "url"]].to_string())
        return

    raw_path = save_augmented(df, tag="raw")

    if args.label:
        model_path = str(PROJECT_ROOT / args.model_path)
        if not Path(model_path).exists():
            print(f"[error] Model not found at {model_path}")
            return
        df = pseudo_label(df, model_path)
        labelled_path = save_augmented(df, tag="labelled")
        if args.merge:
            merge_into_training(labelled_path, min_confidence=args.min_conf)


if __name__ == "__main__":
    main()
