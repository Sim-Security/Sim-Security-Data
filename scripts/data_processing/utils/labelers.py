# scripts/data_processing/utils/labelers.py
# This module tokenizes content and assigns vulnerability and platform labels.

from typing import Dict, List

VULNERABILITY_KEYWORDS = {
    "reentrancy": {"type": "Reentrancy", "severity": "High"},
    "overflow": {"type": "Integer Overflow", "severity": "Medium"},
    "rug pull": {"type": "Rug Pull", "severity": "High"}
}

PLATFORM_KEYWORDS = ["ethereum", "solana"]

def tokenize_text(text: str) -> List[str]:
    """
    Simple tokenization by splitting on whitespace.
    For more complex use cases, consider NLP libraries.
    """
    return text.split()

def annotate_entry(entry: Dict) -> Dict:
    """
    Annotate an entry with vulnerability_type, severity, platform_label, and tokens.
    """
    content_lower = entry.get("content", "").lower()
    tokens = tokenize_text(content_lower)

    # Default annotations
    entry["vulnerability_type"] = "Unknown"
    entry["severity"] = "Unknown"
    entry["platform_label"] = "Generic"

    # Check for vulnerabilities
    for keyword, info in VULNERABILITY_KEYWORDS.items():
        if keyword in content_lower:
            entry["vulnerability_type"] = info["type"]
            entry["severity"] = info["severity"]
            break

    # Check for platform
    for p in PLATFORM_KEYWORDS:
        if p in content_lower:
            entry["platform_label"] = p.capitalize()
            break

    # Assign remediation note
    entry["remediation"] = "Refer to standard secure coding guidelines and best practices."
    entry["tokens"] = tokens

    return entry

def annotate_data(entries: List[Dict]) -> List[Dict]:
    """
    Apply annotation to a list of entries.
    """
    return [annotate_entry(e) for e in entries]
