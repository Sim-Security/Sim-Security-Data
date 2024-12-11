# scripts/batch_process_audits.py
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv
import logging
import re
import time
from typing import List, Iterator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuditBatchProcessor:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompt_path = Path("prompts/audit_format_prompt.md")
        
    def split_into_sections(self, content: str) -> List[str]:
        """Split content into sections based on main headers."""
        sections = []
        current_section = []
        header_pattern = re.compile(r'^#\s+[\w\s-]+$', re.MULTILINE)
        
        for line in content.split('\n'):
            if header_pattern.match(line) and current_section:
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
                
        if current_section:
            sections.append('\n'.join(current_section))
            
        return sections
    
    def chunk_sections(self, sections: List[str], max_chunk_tokens: int = 3000) -> Iterator[str]:
        """Yield chunks of sections that fit within token limits."""
        current_chunk = []
        current_size = 0
        
        for section in sections:
            # Rough estimate of tokens (characters / 4)
            section_tokens = len(section) // 4
            
            if current_size + section_tokens > max_chunk_tokens and current_chunk:
                yield '\n\n'.join(current_chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(section)
            current_size += section_tokens
        
        if current_chunk:
            yield '\n\n'.join(current_chunk)
    
    def format_chunk(self, chunk: str, is_first_chunk: bool = False) -> str:
        """Format a single chunk through Claude."""
        # Load formatting instructions if it's the first chunk
        if is_first_chunk:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                format_instructions = f.read()
            message = f"{format_instructions}\n\nPlease format this first part of the audit report:\n\n{chunk}"
        else:
            message = f"Continue formatting the audit report. Format this next section maintaining consistent style:\n\n{chunk}"
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )
            
            # Log token usage and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens)
            logger.info(f"Chunk processed - Input tokens: {input_tokens}, Output tokens: {output_tokens}")
            logger.info(f"Chunk cost: ${cost:.3f}")
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            raise
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Sonnet."""
        input_cost = (input_tokens / 1000) * 0.003
        output_cost = (output_tokens / 1000) * 0.015
        return input_cost + output_cost
    
    def process_file(self, input_path: Path, output_path: Path) -> None:
        """Process a file in batches."""
        logger.info(f"Starting to process: {input_path}")
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into sections
        logger.info("Splitting content into sections...")
        sections = self.split_into_sections(content)
        logger.info(f"Split into {len(sections)} sections")
        
        # Process chunks
        formatted_chunks = []
        total_cost = 0
        
        for i, chunk in enumerate(self.chunk_sections(sections)):
            logger.info(f"Processing chunk {i+1}")
            try:
                formatted_chunk = self.format_chunk(chunk, is_first_chunk=(i==0))
                formatted_chunks.append(formatted_chunk)
                
                # Rate limiting - stay within 8000 tokens per minute for Sonnet
                if i < len(sections) - 1:  # Don't sleep after last chunk
                    time.sleep(10)  # 10 second delay between chunks
                    
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                raise
        
        # Combine and save results
        logger.info("Combining formatted chunks...")
        formatted_content = '\n\n'.join(formatted_chunks)
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        logger.info(f"Successfully saved formatted content to {output_path}")
        logger.info(f"Total cost: ${total_cost:.3f}")

def main():
    # Load environment
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
    # Set up paths
    input_file = Path("data/audits/spearbit_portfolio/markdown/ArtGobblers-Spearbit-Security-Review/ArtGobblers-Spearbit-Security-Review/ArtGobblers-Spearbit-Security-Review.md")
    output_file = Path("data/processed/reports/ArtGobblers/formatted_report.md")
    
    # Process file
    processor = AuditBatchProcessor(api_key)
    try:
        processor.process_file(input_file, output_file)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()