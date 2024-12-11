# scripts/data_processing/utils/pdf_processing.py
import os
from pathlib import Path
from typing import List, Optional
import subprocess

class PDFProcessor:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_pdf_to_markdown(self, pdf_path: Path) -> Optional[Path]:
        """
        Convert a single PDF file to markdown using marker_single.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Path to the output directory containing the markdown file, or None if conversion failed
        """
        output_subdir = self.output_dir / pdf_path.stem
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"Converting {pdf_path} to markdown...")
            subprocess.run([
                "marker_single",
                str(pdf_path),
                "--output_dir", str(output_subdir),
                "--output_format", "markdown"
            ], check=True, capture_output=True, text=True)
            
            # marker_single creates a directory with the markdown file inside
            return output_subdir
        except subprocess.CalledProcessError as e:
            print(f"Error converting {pdf_path}:")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            print(f"Unexpected error converting {pdf_path}: {str(e)}")
            return None
    
    def process_pdfs(self) -> List[Path]:
        """
        Convert all PDFs in the input directory to markdown.
        
        Returns:
            List of paths to successfully converted markdown file directories
        """
        successful_conversions = []
        
        # Ensure input directory exists
        if not self.input_dir.exists():
            print(f"Input directory {self.input_dir} does not exist!")
            return successful_conversions
        
        # Process all PDFs in the directory
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {self.input_dir}")
            return successful_conversions
        
        print(f"Found {len(pdf_files)} PDF files to process")
        for pdf_file in pdf_files:
            output_dir = self.convert_pdf_to_markdown(pdf_file)
            if output_dir:
                successful_conversions.append(output_dir)
                print(f"Successfully converted {pdf_file} to markdown")
                print(f"Output saved in {output_dir}")
        
        return successful_conversions