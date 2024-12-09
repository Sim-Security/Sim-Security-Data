# scripts/data_processing/utils/cleaners.py
# This module provides functions to clean and normalize text data.

import re
from typing import Dict, List

def clean_text(text: str) -> str:
    """
    Clean and normalize a text string by:
    - Stripping leading/trailing whitespace
    - Collapsing multiple spaces into a single space
    """
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def clean_entries(entries: List[Dict]) -> List[Dict]:
    """
    Apply the clean_text function to each entry's 'title' and 'content'.
    """
    cleaned = []
    for e in entries:
        e["title"] = clean_text(e.get("title", ""))
        e["content"] = clean_text(e.get("content", ""))
        cleaned.append(e)
    return cleaned
