"""
Downloads DistilBERT, RoBERTa, and XLNet base models from Hugging Face
and saves them to the models/ directory with the correct label configuration.
"""

from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig

MODELS = {
    "distilbert": {"name": "distilbert-base-uncased", "description": "66M parameters"},
    "roberta":    {"name": "roberta-base",             "description": "125M parameters"},
    "xlnet":      {"name": "xlnet-base-cased",         "description": "110M parameters"},
}

LABEL_MAP = {0: "True", 1: "Fake", 2: "Satire", 3: "Bias"}


def download_model(model_key: str, model_info: dict, base_dir: Path) -> bool:
    model_name = model_info["name"]
    save_path = base_dir / model_key

    print(f"\n{'='*60}")
    print(
        f"Downloading: {model_key} — {model_name} ({model_info['description']})")
    print(f"{'='*60}\n")

    try:
        save_path.mkdir(parents=True, exist_ok=True)

        print("[1/3] Tokenizer…")
        AutoTokenizer.from_pretrained(model_name).save_pretrained(save_path)

        print("[2/3] Config…")
        config = AutoConfig.from_pretrained(
            model_name,
            num_labels=4,
            id2label=LABEL_MAP,
            label2id={v: k for k, v in LABEL_MAP.items()},
        )
        config.save_pretrained(save_path)

        print("[3/3] Model weights…")
        AutoModelForSequenceClassification.from_pretrained(
            model_name, config=config).save_pretrained(save_path)

        with open(save_path / "model_info.txt", "w") as f:
            f.write(
                f"Model: {model_name}\nParameters: {model_info['description']}\nLabels: {LABEL_MAP}\nStatus: pre-trained\n")

        print(f"✅ {model_key} saved to {save_path}\n")
        return True

    except Exception as e:
        print(f"❌ {model_key} failed: {e}\n")
        return False


def main():
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    results = {key: download_model(key, info, models_dir)
               for key, info in MODELS.items()}

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for key, ok in results.items():
        print(f"  {key:15} {'✅' if ok else '❌'}")
    print(f"\n{sum(results.values())}/{len(results)} models downloaded")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
