"""
Script to download pre-trained models from Hugging Face
Downloads DistilBERT, RoBERTa, and XLNet models for fake news detection
"""

import os
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoConfig
)

# Model configurations
MODELS = {
    "distilbert": {
        "name": "distilbert-base-uncased",
        "num_labels": 4,
        "description": "Lightweight BERT variant (66M parameters)"
    },
    "roberta": {
        "name": "roberta-base",
        "num_labels": 4,
        "description": "Robustly optimized BERT (125M parameters)"
    },
    "xlnet": {
        "name": "xlnet-base-cased",
        "num_labels": 4,
        "description": "Permutation language model (110M parameters)"
    }
}

# Label mapping
LABEL_MAP = {
    0: "True",
    1: "Fake",
    2: "Satire",
    3: "Bias"
}


def download_model(model_key: str, model_info: dict, base_dir: Path):
    """
    Download a model and tokenizer from Hugging Face

    Args:
        model_key: Short name for the model (e.g., 'distilbert')
        model_info: Dictionary with model configuration
        base_dir: Base directory to save models
    """
    model_name = model_info["name"]
    num_labels = model_info["num_labels"]
    save_path = base_dir / model_key

    print(f"\n{'='*60}")
    print(f"Downloading: {model_key}")
    print(f"Model: {model_name}")
    print(f"Description: {model_info['description']}")
    print(f"Save path: {save_path}")
    print(f"{'='*60}\n")

    try:
        # Create directory
        save_path.mkdir(parents=True, exist_ok=True)

        # Download tokenizer
        print(f"[1/3] Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(save_path)
        print(f"✅ Tokenizer saved to {save_path}")

        # Download config
        print(f"[2/3] Downloading config...")
        config = AutoConfig.from_pretrained(
            model_name,
            num_labels=num_labels,
            id2label={i: label for i, label in LABEL_MAP.items()},
            label2id={label: i for i, label in LABEL_MAP.items()}
        )
        config.save_pretrained(save_path)
        print(f"✅ Config saved to {save_path}")

        # Download model
        print(f"[3/3] Downloading model (this may take a few minutes)...")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            config=config
        )
        model.save_pretrained(save_path)
        print(f"✅ Model saved to {save_path}")

        # Save metadata
        metadata_path = save_path / "model_info.txt"
        with open(metadata_path, 'w') as f:
            f.write(f"Model: {model_name}\n")
            f.write(f"Type: {model_key}\n")
            f.write(f"Parameters: {model_info['description']}\n")
            f.write(f"Num Labels: {num_labels}\n")
            f.write(f"Labels: {LABEL_MAP}\n")
            f.write(f"Status: Pre-trained (not fine-tuned)\n")

        print(f"✅ Successfully downloaded {model_key}!\n")
        return True

    except Exception as e:
        print(f"❌ Error downloading {model_key}: {str(e)}\n")
        return False


def main():
    """Main function to download all models"""
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    models_dir = project_root / "models"

    print("\n" + "="*60)
    print("FAKE NEWS DETECTION - MODEL DOWNLOADER")
    print("="*60)
    print(f"\nProject root: {project_root}")
    print(f"Models directory: {models_dir}")
    print(f"\nModels to download: {len(MODELS)}")
    for key, info in MODELS.items():
        print(f"  - {key}: {info['name']}")

    # Create models directory
    models_dir.mkdir(parents=True, exist_ok=True)

    # Download each model
    results = {}
    for model_key, model_info in MODELS.items():
        success = download_model(model_key, model_info, models_dir)
        results[model_key] = success

    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    successful = sum(results.values())
    total = len(results)

    for model_key, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{model_key:15} {status}")

    print(f"\nTotal: {successful}/{total} models downloaded successfully")

    if successful == total:
        print("\n🎉 All models downloaded successfully!")
        print(f"\nModels are saved in: {models_dir}")
        print("\nNext steps:")
        print("1. Fine-tune models on your dataset using src/models/train.py")
        print("2. Update API to load models from models/ directory")
        print("3. Test predictions with the API")
    else:
        print("\n⚠️  Some models failed to download. Check errors above.")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
