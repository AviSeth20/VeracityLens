"""
Model inference — lazy-loads fine-tuned models and runs predictions with explainability.
"""

import torch
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from dotenv import load_dotenv

load_dotenv()

ID2LABEL = {0: "True", 1: "Fake", 2: "Satire", 3: "Bias"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}

PROJECT_ROOT = Path(__file__).parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_NAMES = {
    "distilbert": "distilbert-base-uncased",
    "roberta":    "roberta-base",
    "xlnet":      "xlnet-base-cased",
}


class FakeNewsClassifier:
    """Wraps a fine-tuned HuggingFace model. Lazy-loads on first call and caches in memory."""

    def __init__(self, model_key: str = "distilbert", max_length: int = 256):
        self.model_key = model_key
        self.max_length = max_length
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = None
        self._tokenizer = None

    def _load(self):
        local_path = MODELS_DIR / self.model_key
        source = str(local_path) if (
            local_path / "config.json").exists() else MODEL_NAMES[self.model_key]
        print(f"[inference] Loading {self.model_key} from: {source}")
        self._tokenizer = AutoTokenizer.from_pretrained(source)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            source,
            num_labels=4,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
            ignore_mismatched_sizes=True,
        )
        self._model.to(self.device)
        self._model.eval()
        print(f"[inference] Model ready on {self.device}")

    @property
    def model(self):
        if self._model is None:
            self._load()
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._load()
        return self._tokenizer

    def predict(self, text: str) -> dict:
        """
        Run inference on a single text.
        Returns label, confidence (0-1), per-class scores, and top token importance scores.
        """
        enc = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**enc)
            probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

        pred_id = int(np.argmax(probs))
        label = ID2LABEL[pred_id]
        confidence = float(probs[pred_id])
        scores = {ID2LABEL[i]: round(float(p), 4) for i, p in enumerate(probs)}
        tokens = self._token_importance(enc, pred_id)

        return {
            "label":      label,
            "confidence": round(confidence, 4),
            "scores":     scores,
            "tokens":     tokens,
        }

    def _token_importance(self, enc, pred_id: int, top_k: int = 8) -> list[dict]:
        """Gradient saliency — returns top-k tokens sorted by importance."""
        try:
            self.model.zero_grad()
            input_ids = enc["input_ids"]
            embeds = self.model.get_input_embeddings()(
                input_ids).detach().requires_grad_(True)
            outputs = self.model(inputs_embeds=embeds,
                                 attention_mask=enc.get("attention_mask"))
            outputs.logits[0, pred_id].backward()
            importance = embeds.grad[0].norm(dim=-1).cpu().numpy()
            tokens = self.tokenizer.convert_ids_to_tokens(
                input_ids[0].cpu().tolist())
            special = {"[CLS]", "[SEP]", "[PAD]", "<s>",
                       "</s>", "<pad>", "<cls>", "<sep>", "▁", "Ġ"}
            pairs = [
                (t.replace("##", "").replace("▁", "").replace("Ġ", ""), float(s))
                for t, s in zip(tokens, importance)
                if t not in special and len(t.strip()) > 1
            ]
            if pairs:
                max_s = max(s for _, s in pairs) or 1.0
                pairs = [(t, round(s / max_s, 4)) for t, s in pairs]
            pairs.sort(key=lambda x: x[1], reverse=True)
            return [{"token": t, "score": s} for t, s in pairs[:top_k]]
        except Exception:
            return []

    def attention_weights(self, text: str) -> list[dict]:
        """
        Gradient saliency mapped to original words in reading order.
        Merges subword tokens (BERT ## and RoBERTa Ġ) back into full words.
        """
        try:
            enc = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length,
                padding=False,
            ).to(self.device)

            input_ids = enc["input_ids"]
            self.model.zero_grad()
            embeds = self.model.get_input_embeddings()(
                input_ids).detach().requires_grad_(True)
            outputs = self.model(inputs_embeds=embeds,
                                 attention_mask=enc.get("attention_mask"))
            pred_id = int(torch.argmax(outputs.logits, dim=-1)[0])
            outputs.logits[0, pred_id].backward()
            importance = embeds.grad[0].norm(dim=-1).cpu().numpy()

            tokens = self.tokenizer.convert_ids_to_tokens(
                input_ids[0].cpu().tolist())
            SPECIAL = {"[CLS]", "[SEP]", "[PAD]", "<s>",
                       "</s>", "<pad>", "<cls>", "<sep>", "<unk>"}

            words = []
            current_word = ""
            current_score = 0.0
            for tok, score in zip(tokens, importance):
                if tok in SPECIAL:
                    if current_word:
                        words.append((current_word, current_score))
                        current_word = ""
                        current_score = 0.0
                    continue

                is_continuation = tok.startswith("##")
                is_new_word = tok.startswith("Ġ") or tok.startswith("▁")
                clean = tok.replace("##", "").replace("Ġ", "").replace("▁", "")

                if is_continuation:
                    current_word += clean
                    current_score = max(current_score, float(score))
                elif is_new_word:
                    if current_word:
                        words.append((current_word, current_score))
                    current_word = clean
                    current_score = float(score)
                else:
                    if current_word:
                        words.append((current_word, current_score))
                    current_word = clean
                    current_score = float(score)

            if current_word:
                words.append((current_word, current_score))

            if not words:
                return []

            max_s = max(s for _, s in words) or 1.0
            return [{"word": w, "attention": round(s / max_s, 4)} for w, s in words if w.strip()]

        except Exception as e:
            print(f"[attention_weights] failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def shap_explain(self, text: str) -> list[dict]:
        """
        Word-level SHAP explanation using RoBERTa for better context.
        Returns words sorted by absolute SHAP value, most influential first.
        """
        try:
            import shap

            clf = get_classifier("roberta")

            def predict_proba(texts):
                results = []
                for t in texts:
                    enc = clf.tokenizer(
                        t, return_tensors="pt", truncation=True,
                        max_length=clf.max_length, padding=True,
                    ).to(clf.device)
                    with torch.no_grad():
                        logits = clf.model(**enc).logits
                    probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
                    results.append(probs)
                return np.array(results)

            masker = shap.maskers.Text(r"\W+")
            explainer = shap.Explainer(
                predict_proba, masker, output_names=list(ID2LABEL.values()))
            shap_values = explainer([text], max_evals=200, batch_size=8)

            enc = clf.tokenizer(text, return_tensors="pt", truncation=True,
                                max_length=clf.max_length).to(clf.device)
            with torch.no_grad():
                pred_id = int(torch.argmax(clf.model(**enc).logits, dim=-1)[0])

            words = shap_values.data[0]
            values = shap_values.values[0, :, pred_id]

            max_abs = float(np.max(np.abs(values))) if len(values) else 1.0
            if max_abs == 0:
                max_abs = 1.0

            result = []
            for word, val in zip(words, values):
                w = word.strip()
                if not w:
                    continue
                result.append(
                    {"word": w, "shap_value": round(float(val) / max_abs, 4)})

            # Keep original sentence order so inline text rendering makes sense
            return result

        except Exception as e:
            print(f"[shap_explain] failed: {e}")
            import traceback
            traceback.print_exc()
            return []


_classifiers: dict[str, FakeNewsClassifier] = {}


def get_classifier(model_key: str = "distilbert") -> FakeNewsClassifier:
    """Get or create a cached classifier instance."""
    if model_key not in _classifiers:
        _classifiers[model_key] = FakeNewsClassifier(model_key)
    return _classifiers[model_key]


def predict(text: str, model_key: str = "distilbert") -> dict:
    """Convenience wrapper for single prediction."""
    return get_classifier(model_key).predict(text)


def generate_explanation_text(
    shap_tokens: list[dict],
    label: str,
    confidence: float,
    model_key: str,
) -> str:
    """
    Build a natural-language paragraph explaining the prediction from SHAP data.
    No LLM required — derived entirely from token scores and prediction metadata.
    """
    if not shap_tokens:
        return (
            f"The {model_key} model classified this article as {label} "
            f"with {round(confidence * 100)}% confidence, but no word-level "
            f"explanation data was available for this prediction."
        )

    positive = sorted(
        [t for t in shap_tokens if t["shap_value"] > 0.05],
        key=lambda x: x["shap_value"], reverse=True
    )[:5]
    negative = sorted(
        [t for t in shap_tokens if t["shap_value"] < -0.05],
        key=lambda x: x["shap_value"]
    )[:3]

    conf_pct = round(confidence * 100)
    model_display = {"distilbert": "DistilBERT", "roberta": "RoBERTa",
                     "xlnet": "XLNet"}.get(model_key, model_key)

    conf_phrase = (
        "with very high confidence" if conf_pct >= 90 else
        "with high confidence" if conf_pct >= 75 else
        "with moderate confidence" if conf_pct >= 55 else
        "with low confidence"
    )

    label_descriptions = {
        "True":   "factual and credible reporting",
        "Fake":   "fabricated or misleading content",
        "Satire": "satirical or parody content",
        "Bias":   "politically or ideologically biased reporting",
    }
    label_desc = label_descriptions.get(label, label)

    parts = [
        f"{model_display} classified this article as {label} ({label_desc}) "
        f"{conf_phrase} ({conf_pct}%)."
    ]

    if positive:
        word_list = ", ".join(f'"{t["word"]}"' for t in positive)
        parts.append(
            f"The words most strongly associated with this classification were {word_list}, "
            f"which the model weighted heavily toward a {label} prediction."
        )

    if negative:
        word_list = ", ".join(f'"{t["word"]}"' for t in negative)
        parts.append(
            f"On the other hand, terms like {word_list} pulled against this classification, "
            f"suggesting some linguistic signals that are inconsistent with {label} content."
        )
    elif not negative:
        parts.append(
            f"The model found little linguistic evidence contradicting this classification."
        )

    if conf_pct < 65:
        parts.append(
            "The relatively lower confidence suggests the article contains mixed signals "
            "and the prediction should be interpreted with caution."
        )

    return " ".join(parts)
