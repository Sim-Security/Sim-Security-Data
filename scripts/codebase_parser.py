from pathlib import Path
import re
import json
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextToJsonParser:
    def __init__(self):
        # File extensions and paths we want to include
        self.include_extensions = {
            '.sol',    # Solidity
            '.vy',     # Vyper
            '.py',     # Python
            '.js',     # JavaScript
            '.ts',     # TypeScript
            '.rs',     # Rust
            '.move'    # Move
        }
        
        # Paths that typically contain source code
        self.include_paths = [
            '/src/',
            '/contracts/',
            '/protocol/',
            '/lib/',
            '/sources/'
        ]
        
        # Files/directories to exclude
        self.exclude_patterns = {
            'test/',
            'mock',
            'example',
            '.t.sol',  # Test files
            '.s.sol',  # Script files
            '.json',
            '.md',
            '.yml',
            '.toml',
            '.txt',
            '.gitignore',
            '.git'
        }

    def is_relevant_file(self, filepath: str) -> bool:
        """Determine if a file should be included in the codebase JSON."""
        filepath_lower = filepath.lower().strip('/')
        
        # Check exclusions first
        if any(pattern in filepath_lower for pattern in self.exclude_patterns):
            return False
        
        # Check if it's in a relevant source directory
        in_source_dir = any(path in filepath_lower for path in self.include_paths)
        
        # Check if it has a relevant extension
        has_relevant_ext = any(filepath_lower.endswith(ext) for ext in self.include_extensions)
        
        return in_source_dir or has_relevant_ext

    def split_file_sections(self, content: str) -> List[Tuple[str, str]]:
        """Split the text file into sections based on the separator pattern."""
        sections = []
        
        try:
            # Skip to Files Content section if it exists
            if "Files Content:" in content:
                content = content.split("Files Content:", 1)[1]

            # Use regex to find all file sections
            # This pattern matches: File: <path> followed by separator line and content
            section_pattern = r"File:\s*([^\n]+)\n={48,}\n(.*?)(?=\nFile:|$)"
            matches = re.finditer(section_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    filepath = match.group(1).strip()
                    content = match.group(2).strip()
                    
                    if filepath and content:  # Only add if both path and content exist
                        sections.append((filepath, content))
                        logger.debug(f"Found file: {filepath}")
                except Exception as e:
                    logger.warning(f"Error processing section: {e}")
                    continue
                    
            logger.info(f"Successfully parsed {len(sections)} file sections")
            
        except Exception as e:
            logger.error(f"Error splitting file sections: {e}")
            
        return sections

    def create_codebase_json(self, input_text: str) -> Dict:
        """Convert the text file into the desired JSON structure."""
        logger.info("Starting to parse codebase text")
        
        # Split into file sections
        file_sections = self.split_file_sections(input_text)
        logger.info(f"Found {len(file_sections)} total file sections")
        
        # Filter and process relevant files
        relevant_files = []
        for filepath, content in file_sections:
            if self.is_relevant_file(filepath):
                clean_path = filepath.strip('/')
                relevant_files.append({
                    "path": f"/{clean_path}",
                    "content": content
                })
                logger.info(f"Including file: {clean_path}")
            else:
                logger.debug(f"Skipping file: {filepath}")

        logger.info(f"Included {len(relevant_files)} relevant files")

        # Create the JSON structure
        codebase_json = {
            "codebase": {
                "files": relevant_files
            }
        }
        
        return codebase_json

def process_file(input_path: Path, output_path: Path) -> None:
    """Process a single text file and save the resulting JSON."""
    logger.info(f"Processing file: {input_path}")
    
    try:
        # Read the input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            raise ValueError("Input file is empty")
            
        # Create parser and process content
        parser = TextToJsonParser()
        result = parser.create_codebase_json(content)
        
        if not result["codebase"]["files"]:
            logger.warning("No relevant files were found in the input")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            
        # Log summary
        file_count = len(result["codebase"]["files"])
        logger.info(f"Successfully processed {file_count} relevant files")
        logger.info(f"Output saved to: {output_path}")
        
        # Print preview of included files
        logger.info("\nIncluded files:")
        for file in result["codebase"]["files"]:
            logger.info(f"- {file['path']}")
            
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def main():
    input_file = Path("data/Manual-Process/Art-Gobblers/Repo.txt")
    output_file = Path("data/Manual-Process/Art-Gobblers/artgobblers_codebase.json")
    
    process_file(input_file, output_file)

if __name__ == "__main__":
    main()