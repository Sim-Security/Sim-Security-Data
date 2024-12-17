import os
from pathlib import Path
import anthropic
import logging
from typing import List, Optional
import math
from tqdm import tqdm
from dotenv import load_dotenv
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarkdownCleaner:
    def __init__(self):
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.max_chunk_size = 12000  # Characters per chunk
        
    def split_content(self, content: str) -> List[str]:
        """Split content into processable chunks."""
        logger.info("Starting content splitting...")
        
        # Calculate target chunk size
        total_chars = len(content)
        target_size = self.max_chunk_size
        
        # Split on double newlines first
        sections = content.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        logger.info(f"Processing {len(sections)} sections...")
        
        for section in sections:
            section_size = len(section)
            
            # If adding this section would exceed target size and we have content
            if current_size + section_size > target_size and current_chunk:
                # Join and add current chunk
                chunks.append('\n\n'.join(current_chunk))
                # Start new chunk
                current_chunk = [section]
                current_size = section_size
            else:
                # Add to current chunk
                current_chunk.append(section)
                current_size += section_size
        
        # Add final chunk if exists
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        logger.info(f"Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1} size: {len(chunk)} characters")
        
        return chunks

    def standardize_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> Optional[str]:
        """Standardize a chunk of the audit report."""
        message = """You are processing chunk {chunk_index + 1} of {total_chunks} from a security audit report.
        
        For each finding in the chunk, format it precisely as follows to ensure all information is preserved:
        
        ### [Title of the Finding] {#finding-id}
        
        **Severity:** [Critical/High/Medium/Low/Gas/Informational]
        
        **Context:** [ContractName.sol#LX-Y]
        
        **Vulnerability Type:** [Category/type of vulnerability - extract from description if not explicitly stated]
        
        **Description:**
        [Detailed description of the issue]
        
        **Exploit Scenario:** (if present)
        [Description of how the vulnerability could be exploited]
        
        **Code Snippet:**
        ```solidity
        [Any relevant code snippets]
        ```
        
        **Vulnerable Function:** [Extract from context/description]
        
        **Control Flow:** (if described)
        [Description of the vulnerable control flow]
        
        **Recommendation:**
        [Recommendations for fixing the issue]
        
        **References:** (if any)
        [List of relevant references]
        
        **Resolution:** (if present)
        [How the issue was resolved]

        Important:
        1. Maintain all technical details and examples from the original
        2. Keep all code blocks and proofs of concept
        3. If any section is not present in the original, omit it - do not create content
        4. Format all code blocks with appropriate language tags
        5. Standardize line number references as ContractName.sol#L123-L456
        6. Ensure severity matches exactly one of: Critical, High, Medium, Low, Gas, Informational
        
        Return only the standardized markdown, preserving all original technical content.

        Important Notes:
        - If the chunk starts with "**Context:** Continued from previous chunk", 
        this is a continuation of a previous finding. Format it maintaining the original finding's title.
        - For continued chunks, preserve all content but ensure it follows the standardized format.
        - Do not duplicate sections that were in the previous chunk.
        - Maintain all technical details and formatting.

        Content:"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": message + "\n\n" + chunk}]
            )
            
            cleaned = response.content[0].text.strip()
            if "###" in cleaned:  # Only return chunks that contain findings
                return cleaned
            return None
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_index}: {e}")
            return None

    def clean_audit_report(self, content: str) -> str:
        """Process entire audit report in chunks."""
        try:
            # Split content into manageable chunks
            chunks = self.split_content(content)
            
            # Process each chunk
            cleaned_chunks = []
            with tqdm(total=len(chunks), desc="Processing chunks") as pbar:
                for i, chunk in enumerate(chunks):
                    cleaned_chunk = self.standardize_chunk(chunk, i, len(chunks))
                    if cleaned_chunk:
                        cleaned_chunks.append(cleaned_chunk)
                    pbar.update(1)
            
            # Combine cleaned chunks
            cleaned_content = "\n\n".join([chunk for chunk in cleaned_chunks if chunk])
            
            # Add header if findings were found
            if cleaned_content:
                cleaned_content = "# Findings\n\n" + cleaned_content
                
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Error cleaning audit report: {e}")
            return content

def process_file(input_path: Path, output_path: Path) -> None:
    """Process a markdown file and save the cleaned version."""
    try:
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Read {len(content)} characters from {input_path}")
        
        # Clean content
        cleaner = MarkdownCleaner()
        cleaned_content = cleaner.clean_audit_report(content)
        
        # Save cleaned content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            
        logger.info(f"Cleaned content saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def main():
    # Update paths as needed
    input_path = Path("data_git/processed/Art-Gobblers-Review-pymupdf.md")
    output_path = Path("data/processed/Art-Gobblers-Review-Cleaned-pymupdf.md")
    
    process_file(input_path, output_path)

if __name__ == "__main__":
    main()