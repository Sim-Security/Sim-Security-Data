# scripts/data_processing/utils/markdown_cleaners.py
import re
from pathlib import Path
from typing import List, Optional

class MarkdownCleaner:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_content(self, content: str) -> str:
        """
        Clean markdown content by removing excessive whitespace and normalizing formatting.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Cleaned markdown content
        """
        # Remove excessive blank lines (more than 2 consecutive)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Clean individual lines
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at start and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def clean_file(self, input_path: Path) -> Optional[Path]:
        """
        Clean a single markdown file.
        
        Args:
            input_path: Path to the input markdown file
            
        Returns:
            Path to the cleaned file, or None if cleaning failed
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_content = self.clean_content(content)
            output_path = self.output_dir / input_path.name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            return output_path
        except Exception as e:
            print(f"Error cleaning {input_path}: {str(e)}")
            return None
    
    def clean_directory(self) -> List[Path]:
        """
        Clean all markdown files in the input directory.
        
        Returns:
            List of paths to successfully cleaned files
        """
        successful_cleanings = []
        
        for md_file in self.input_dir.glob("*.md"):
            print(f"Cleaning {md_file}...")
            output_path = self.clean_file(md_file)
            if output_path:
                successful_cleanings.append(output_path)
                print(f"Successfully cleaned {md_file}")
        
        return successful_cleanings