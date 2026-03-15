"""
Evaluation utilities — metrics computed during and after training.
"""

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from transformers import EvalPrediction

LABEL_NAMES = ["True", "Fake", "Satire", "Bias"]


def compute_metrics(eval_pred: EvalPrediction) -> dict:
    """Called by HuggingFace Trainer after every eval step. Returns accuracy and macro/weighted F1."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy":    round(accuracy_score(labels, preds), 4),
        "f1_macro":    round(f1_score(labels, preds, average="macro",    zero_division=0), 4),
        "f1_weighted": round(f1_score(labels, preds, average="weighted", zero_division=0), 4),
    }


def full_report(model, tokenized_test, label_names=LABEL_NAMES) -> dict:
    """Run full evaluation on the test split. Returns per-class metrics and confusion matrix."""
    from transformers import Trainer

    trainer = Trainer(model=model, compute_metrics=compute_metrics)
    preds_out = trainer.predict(tokenized_test)

    preds = np.argmax(preds_out.predictions, axis=-1)
    labels = preds_out.label_ids

    report = classification_report(
        labels, preds, target_names=label_names, output_dict=True, zero_division=0)
    cm = confusion_matrix(labels, preds)

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(labels, preds,
          target_names=label_names, zero_division=0))
    print("Confusion Matrix:")
    print(cm)
    print("=" * 60 + "\n")

    return {"report": report, "confusion_matrix": cm.tolist()}
