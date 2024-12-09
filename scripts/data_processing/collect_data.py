# scripts/data_processing/collect_data.py

import os
from utils.fetchers import fetch_audit_reports
from utils.pdf_processing import process_spearbit_pdfs
from utils.markdown_cleaners import clean_markdown_directory

def main():
    # Step 1: Fetch audit reports (e.g., clone the Spearbit repository)
    fetch_audit_reports()

    # Step 2: Convert PDFs to markdown
    process_spearbit_pdfs()

    # Step 3: Clean the markdown files
    markdown_input_dir = 'data/audits/spearbit_portfolio/markdown'
    markdown_output_dir = 'data/processed/reports'
    clean_markdown_directory(markdown_input_dir, markdown_output_dir)

    print("Data ingestion and preprocessing completed successfully.")

if __name__ == "__main__":
    main()
