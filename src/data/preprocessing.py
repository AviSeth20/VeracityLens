"""
Data preprocessing module for fake news detection
"""

import re
import html
from typing import List

def clean_text(text: str) -> str:
    """
    Clean and normalize text data
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Standardize quotes and dashes
    text = text.replace('"', '"').replace('"', '"').replace('–', '-')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_batch(texts: List[str]) -> List[str]:
    """
    Preprocess a batch of texts
    
    Args:
        texts: List of raw text strings
        
    Returns:
        List of cleaned text strings
    """
    return [clean_text(text) for text in texts]

if __name__ == "__main__":
    # Example usage
    sample_text = "Breaking News: &quot;Amazing Discovery&quot; – https://example.com"
    cleaned = clean_text(sample_text)
    print(f"Original: {sample_text}")
    print(f"Cleaned: {cleaned}")
