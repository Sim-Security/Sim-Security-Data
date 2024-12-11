# tests/test_pdf_processor.py
from scripts.data_processing.utils.pdf_processing import PDFProcessor
from pathlib import Path

def main():
    print("Testing PDF Processor...")
    
    # Define directories
    input_dir = Path("data/audits/spearbit_portfolio/pdfs")
    output_dir = Path("data/audits/spearbit_portfolio/markdown")
    
    # Create input directory if it doesn't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we have any PDFs to process
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"\nNo PDF files found in {input_dir}")
        print("Please add some PDF files to process")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files in {input_dir}:")
    for pdf in pdf_files:
        print(f"- {pdf.name}")
    
    # Process the PDFs
    processor = PDFProcessor(str(input_dir), str(output_dir))
    converted_dirs = processor.process_pdfs()
    
    # Report results
    if converted_dirs:
        print(f"\nSuccessfully converted {len(converted_dirs)} PDF files:")
        for dir_path in converted_dirs:
            print(f"\nOutput directory: {dir_path}")
            markdown_files = list(Path(dir_path).glob("*.md"))
            for md_file in markdown_files:
                print(f"- Generated: {md_file.name}")
                # Print first few lines of the markdown file
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        first_lines = ''.join(f.readline() for _ in range(5))
                    print("First few lines of content:")
                    print(first_lines)
                except Exception as e:
                    print(f"Could not read file: {e}")
    else:
        print("\nNo files were successfully converted")

if __name__ == "__main__":
    main()