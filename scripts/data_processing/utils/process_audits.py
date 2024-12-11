# scripts/process_audits.py
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv
from typing import Optional

def load_api_key() -> str:
    """Load API key from .env file or environment variables."""
    # Try to load from .env file first
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please add it to .env file or set it as an environment variable"
        )
    return api_key

class AuditFormatter:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=load_api_key())
        self.prompt_path = Path("prompts/audit_format_prompt.md")
        # ... rest of the class implementation stays the same ...

def main():
    # Set up paths
    input_dir = Path("data/audits/spearbit_portfolio/markdown")
    output_dir = Path("data/processed/reports")
    
    # Create formatter and process files
    formatter = AuditFormatter()
    formatter.process_directory(input_dir, output_dir)

if __name__ == "__main__":
    main()