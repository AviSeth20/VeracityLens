"""
Training script for fake news detection.

Usage:
    python -m src.models.train --model distilbert
    python -m src.models.train --model roberta --epochs 5
    python -m src.models.train --all
"""

from src.data.dataset import build_dataset, LABEL2ID, ID2LABEL
from src.models.evaluate import compute_metrics, full_report
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parents[2]))
load_dotenv()


MODELS = {
    "distilbert": "distilbert-base-uncased",
    "roberta":    "roberta-base",
    "xlnet":      "xlnet-base-cased",
}

PROJECT_ROOT = Path(__file__).parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
DATA_CSV = PROJECT_ROOT / "data" / "processed" / "Dataset_Clean.csv"


def get_training_args(model_key, output_dir, epochs, batch_size, learning_rate, use_wandb) -> TrainingArguments:
    return TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.06,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=2,
        logging_dir=str(output_dir / "logs"),
        logging_steps=50,
        report_to="wandb" if use_wandb else "none",
        run_name=f"{model_key}-{datetime.now().strftime('%Y%m%d-%H%M')}",
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=0,
        push_to_hub=False,
    )


def train_model(model_key, epochs=3, batch_size=16, learning_rate=2e-5, max_length=256, use_wandb=False) -> dict:
    """Full training run for one model. Returns evaluation metrics."""
    model_name = MODELS[model_key]
    output_dir = MODELS_DIR / model_key

    print("\n" + "=" * 60)
    print(f"TRAINING: {model_key}  ({model_name})")
    print(f"Epochs: {epochs}  |  Batch: {batch_size}  |  LR: {learning_rate}")
    print(
        f"Device: {'GPU (' + torch.cuda.get_device_name(0) + ')' if torch.cuda.is_available() else 'CPU'}")
    print("=" * 60 + "\n")

    print("[1/4] Building dataset…")
    tokenized = build_dataset(
        csv_path=DATA_CSV, tokenizer_name=model_name, max_length=max_length)

    print("[2/4] Loading model…")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=4, id2label=ID2LABEL, label2id=LABEL2ID, ignore_mismatched_sizes=True,
    )

    print("[3/4] Setting up trainer…")
    output_dir.mkdir(parents=True, exist_ok=True)

    if use_wandb:
        import wandb
        wandb.init(
            project=os.getenv("WANDB_PROJECT", "fake-news-detection"),
            name=f"{model_key}-{datetime.now().strftime('%Y%m%d-%H%M')}",
            config={"model": model_name, "epochs": epochs, "batch_size": batch_size,
                    "learning_rate": learning_rate, "max_length": max_length},
        )

    trainer = Trainer(
        model=model,
        args=get_training_args(model_key, output_dir,
                               epochs, batch_size, learning_rate, use_wandb),
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("[4/4] Training…\n")
    trainer.train()

    print(f"\n[✓] Saving model to {output_dir}")
    trainer.save_model(str(output_dir))
    AutoTokenizer.from_pretrained(model_name).save_pretrained(str(output_dir))

    print("[✓] Evaluating on test set…")
    metrics = full_report(model, tokenized["test"])

    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics["report"], f, indent=2)
    print(f"[✓] Metrics saved to {metrics_path}")

    if use_wandb:
        import wandb
        wandb.log(metrics["report"])
        wandb.finish()

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Train fake news detection models")
    parser.add_argument(
        "--model",         choices=list(MODELS.keys()), default="distilbert")
    parser.add_argument("--all",           action="store_true",
                        help="Train all three models sequentially")
    parser.add_argument("--epochs",        type=int,   default=3)
    parser.add_argument("--batch-size",    type=int,   default=16)
    parser.add_argument("--lr",            type=float, default=2e-5)
    parser.add_argument("--max-length",    type=int,   default=256)
    parser.add_argument("--wandb",         action="store_true")
    args = parser.parse_args()

    targets = list(MODELS.keys()) if args.all else [args.model]
    all_metrics = {}
    for model_key in targets:
        all_metrics[model_key] = train_model(
            model_key=model_key, epochs=args.epochs, batch_size=args.batch_size,
            learning_rate=args.lr, max_length=args.max_length, use_wandb=args.wandb,
        )

    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    for key, m in all_metrics.items():
        r = m["report"]
        print(f"\n{key.upper()}")
        print(f"  Accuracy:    {r.get('accuracy', 'N/A'):.4f}")
        print(
            f"  Macro F1:    {r.get('macro avg', {}).get('f1-score', 'N/A'):.4f}")
        print(
            f"  Weighted F1: {r.get('weighted avg', {}).get('f1-score', 'N/A'):.4f}")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
