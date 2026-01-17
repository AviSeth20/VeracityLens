"""
Tests for data preprocessing module
"""

import pytest
from src.data.preprocessing import clean_text, preprocess_batch

def test_clean_text_removes_urls():
    text = "Check this out: https://example.com"
    cleaned = clean_text(text)
    assert "https://" not in cleaned

def test_clean_text_decodes_html():
    text = "&quot;Hello&quot;"
    cleaned = clean_text(text)
    assert '"' in cleaned
    assert "&quot;" not in cleaned

def test_preprocess_batch():
    texts = [
        "Text with https://url.com",
        "&amp; special chars"
    ]
    cleaned = preprocess_batch(texts)
    assert len(cleaned) == 2
    assert "https://" not in cleaned[0]
