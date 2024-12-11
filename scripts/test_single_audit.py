# scripts/test_single_audit.py
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_key() -> str:
    """Load API key from .env file or environment variables."""
    logger.info("Loading environment variables...")
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please add it to .env file or set it as an environment variable"
        )
    logger.info("API key loaded successfully")
    return api_key

def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate the cost of the API call"""
    if model == "claude-3-opus-20240229":
        input_cost_per_1k = 0.015
        output_cost_per_1k = 0.075
    elif model == "claude-3-sonnet-20240229":
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
    
    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k
    return input_cost + output_cost

def format_single_audit(input_file: Path, output_file: Path) -> None:
    """Process a single audit file through Claude."""
    logger.info(f"Starting to process audit file: {input_file}")
    
    # Load formatting instructions
    logger.info("Loading formatting prompt...")
    prompt_path = Path("prompts/audit_format_prompt.md")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            format_instructions = f.read()
        logger.info("Format prompt loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load format prompt: {e}")
        raise
    
    # Load audit content
    logger.info("Loading audit content...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            audit_content = f.read()
        logger.info(f"Loaded {len(audit_content)} characters from audit file")
    except Exception as e:
        logger.error(f"Failed to load audit file: {e}")
        raise
    
    # Create Claude client
    logger.info("Initializing Claude client...")
    client = anthropic.Anthropic(api_key=load_api_key())
    
    # Prepare message
    logger.info("Preparing message for Claude...")
    message = f"{format_instructions}\n\nPlease format this audit report:\n\n{audit_content}"
    logger.info(f"Total message length: {len(message)} characters")
    
    # Model settings
    model = "claude-3-sonnet-20240229"
    max_tokens = 4096  # Increased token limit
    
    # Send to Claude
    logger.info(f"Sending request to Claude ({model})...")
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        logger.info("Received response from Claude")
        
        # Calculate and log cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = calculate_cost(input_tokens, output_tokens, model)
        logger.info(f"Input tokens: {input_tokens}")
        logger.info(f"Output tokens: {output_tokens}")
        logger.info(f"Estimated cost: ${cost:.3f}")
        
    except Exception as e:
        logger.error(f"Failed to get response from Claude: {e}")
        raise
    
    # Get formatted content
    formatted_content = response.content[0].text
    logger.info(f"Received {len(formatted_content)} characters of formatted content")
    
    # Compare input and output sizes
    input_size = len(audit_content)
    output_size = len(formatted_content)
    logger.info(f"Input size: {input_size} characters")
    logger.info(f"Output size: {output_size} characters")
    if output_size < input_size:
        logger.warning(f"Output is smaller than input by {input_size - output_size} characters")
    
    # Save formatted content
    logger.info(f"Saving formatted content to {output_file}")
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        logger.info("Successfully saved formatted content")
    except Exception as e:
        logger.error(f"Failed to save formatted content: {e}")
        raise
    
    logger.info("Processing completed successfully")

def main():
    # Set up paths for Art Gobblers audit
    input_file = Path("data/audits/spearbit_portfolio/markdown/ArtGobblers-Spearbit-Security-Review/ArtGobblers-Spearbit-Security-Review/ArtGobblers-Spearbit-Security-Review.md")
    output_file = Path("data/processed/reports/ArtGobblers/formatted_report.md")
    
    logger.info("Starting audit formatting process...")
    try:
        format_single_audit(input_file, output_file)
        logger.info("Process completed successfully!")
        
        # Print sample of formatted content
        logger.info("\nFirst few lines of formatted content:")
        with open(output_file, 'r', encoding='utf-8') as f:
            print("\n" + "-" * 80)
            print(f.read(1000))  # First 1000 characters
            print("-" * 80)
            
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise

if __name__ == "__main__":
    main()