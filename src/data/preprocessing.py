import re
import html
from typing import List


def clean_text(text: str) -> str:
    """Clean and normalize raw text — decodes HTML, strips URLs, normalizes whitespace."""
    text = html.unescape(text)
    text = re.sub(r'http\S+', '', text)
    text = text.replace('\u201c', '"').replace(
        '\u201d', '"').replace('\u2013', '-')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_batch(texts: List[str]) -> List[str]:
    """Apply clean_text to a list of strings."""
    return [clean_text(text) for text in texts]
