# scripts/data_processing/utils/markdown_cleaners.py

import os
import re

def clean_markdown_file(input_path, output_path):
    """
    Cleans a single markdown file to improve formatting.
    """
    with open(input_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Example cleanup: Remove excessive blank lines
    cleaned_content = re.sub(r'\n{3,}', '\n\n', content)

    # Example cleanup: Remove trailing whitespaces
    cleaned_content = re.sub(r'[ \t]+$', '', cleaned_content, flags=re.MULTILINE)

    # Additional cleaning rules can be added here

    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

def clean_markdown_directory(input_dir, output_dir):
    """
    Cleans all markdown files in the input directory and saves to output directory.
    """
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.md'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            print(f"Cleaning {input_path}...")
            clean_markdown_file(input_path, output_path)
            print(f"Cleaned {filename} saved to {output_path}")
