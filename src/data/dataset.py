"""
Dataset loader — reads Dataset_Clean.csv and returns tokenized HuggingFace DatasetDict splits.
"""

import pandas as pd
from pathlib import Path
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer
from sklearn.model_selection import train_test_split
from src.data.preprocessing import clean_text

LABEL2ID = {"True": 0, "Fake": 1, "Satire": 2, "Bias": 3}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}

DEFAULT_CSV = Path(__file__).parents[2] / \
    "data" / "processed" / "Dataset_Clean.csv"
MAX_LENGTH = 256
VAL_SPLIT = 0.10
TEST_SPLIT = 0.10
RANDOM_SEED = 42


def load_dataframe(csv_path: str | Path = DEFAULT_CSV) -> pd.DataFrame:
    """Load and clean Dataset_Clean.csv. Returns a DataFrame with columns: text, label (int)."""
    df = pd.read_csv(csv_path, low_memory=False)
    df["label_text"] = df["label_text"].astype(
        str).str.strip().str.capitalize()
    df = df[df["label_text"].isin(LABEL2ID)].copy()

    df["content"] = df["content"].fillna("").astype(str)
    df["title"] = df["title"].fillna("").astype(str)
    df["text"] = df.apply(lambda r: r["content"] if len(
        r["content"]) > 30 else r["title"], axis=1)
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() > 10].copy()
    df["label"] = df["label_text"].map(LABEL2ID).astype(int)

    print(f"[dataset] Loaded {len(df):,} rows")
    print(
        f"[dataset] Label distribution:\n{df['label_text'].value_counts().to_string()}\n")
    return df[["text", "label"]].reset_index(drop=True)


def make_splits(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified train / val / test split."""
    train_df, temp_df = train_test_split(
        df, test_size=VAL_SPLIT + TEST_SPLIT, stratify=df["label"], random_state=RANDOM_SEED
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=TEST_SPLIT / (VAL_SPLIT + TEST_SPLIT),
        stratify=temp_df["label"], random_state=RANDOM_SEED
    )
    print(
        f"[dataset] Train: {len(train_df):,}  Val: {len(val_df):,}  Test: {len(test_df):,}")
    return train_df, val_df, test_df


def tokenize_dataset(dataset_dict: DatasetDict, tokenizer_name: str, max_length: int = MAX_LENGTH) -> DatasetDict:
    """Tokenize all splits."""
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def _tokenize(batch):
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=max_length)

    tokenized = dataset_dict.map(_tokenize, batched=True, batch_size=512, remove_columns=[
                                 "text"], desc="Tokenizing")
    tokenized.set_format("torch")
    return tokenized


def build_dataset(
    csv_path: str | Path = DEFAULT_CSV,
    tokenizer_name: str = "distilbert-base-uncased",
    max_length: int = MAX_LENGTH,
) -> DatasetDict:
    """Full pipeline: CSV → cleaned DataFrame → HuggingFace DatasetDict → tokenized splits."""
    df = load_dataframe(csv_path)
    train_df, val_df, test_df = make_splits(df)

    raw = DatasetDict({
        "train":      Dataset.from_pandas(train_df, preserve_index=False),
        "validation": Dataset.from_pandas(val_df,   preserve_index=False),
        "test":       Dataset.from_pandas(test_df,  preserve_index=False),
    })
    return tokenize_dataset(raw, tokenizer_name, max_length)


if __name__ == "__main__":
    ds = build_dataset()
    print(ds)
    print("Sample:", ds["train"][0])
