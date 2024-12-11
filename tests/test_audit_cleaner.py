# tests/test_audit_cleaner.py
from pathlib import Path
from scripts.data_processing.utils.audit_markdown_cleaner import AuditMarkdownCleaner
import sys

def main():
    print("Testing Audit Markdown Cleaner...")
    
    # Define directories
    input_dir = Path("data/audits/spearbit_portfolio/markdown")
    output_dir = Path("data/processed/reports")
    
    # Create cleaner instance
    cleaner = AuditMarkdownCleaner()
    
    # Find markdown files
    md_files = list(input_dir.glob("**/*.md"))
    if not md_files:
        print(f"\nNo markdown files found in {input_dir}")
        print(f"Current working directory: {Path.cwd()}")
        print("\nSearching subdirectories:")
        for path in input_dir.glob("**/*"):
            print(f"  Found: {path}")
        return
    
    print(f"\nFound {len(md_files)} markdown files:")
    for md in md_files:
        print(f"- {md}")
        
        try:
            # Get relative path from input directory
            rel_path = md.relative_to(input_dir)
            print(f"  Relative path: {rel_path}")
            
            # Create output path maintaining structure
            output_path = output_dir / rel_path
            print(f"  Output path: {output_path}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process file
            processed_path = cleaner.process_file(md, output_path)
            print(f"  Processed: {processed_path}")
            
            # Print first few lines of cleaned content
            try:
                with open(processed_path, 'r', encoding='utf-8') as f:
                    first_lines = ''.join(f.readline() for _ in range(10))
                print("\nFirst few lines of cleaned content:")
                print("-" * 80)
                print(first_lines)
                print("-" * 80)
            except Exception as e:
                print(f"Error reading processed file: {e}")
                
        except Exception as e:
            print(f"Error processing {md}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()