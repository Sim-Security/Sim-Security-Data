# scripts/data_processing/collect_data.py
from pathlib import Path
from utils.fetchers import GitFetcher
from utils.pdf_processing import PDFProcessor
from utils.markdown_cleaners import MarkdownCleaner

def main():
    # Step 1: Fetch audit reports
    fetcher = GitFetcher()
    fetcher.fetch_audit_reports()
    
    # Step 2: Convert PDFs to markdown
    pdf_dir = Path("data/audits/spearbit_portfolio/pdfs")
    markdown_dir = Path("data/audits/spearbit_portfolio/markdown")
    
    processor = PDFProcessor(pdf_dir, markdown_dir)
    converted_files = processor.process_pdfs()
    
    # Step 3: Clean markdown files
    output_dir = Path("data/processed/reports")
    cleaner = MarkdownCleaner(markdown_dir, output_dir)
    cleaned_files = cleaner.clean_directory()
    
    print("\nData ingestion and preprocessing completed.")
    print(f"Converted {len(converted_files)} PDF files to markdown")
    print(f"Cleaned {len(cleaned_files)} markdown files")

if __name__ == "__main__":
    main()