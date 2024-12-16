import os
from pathlib import Path
import anthropic
import json
import logging
import re
from typing import Dict, List, Optional, Iterator, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import jsonschema
from tqdm import tqdm
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ParsingProgress:
    """Track parsing progress for recovery."""
    markdown_path: str
    metadata_extracted: bool = False
    findings_split: bool = False
    total_findings: int = 0
    processed_findings: List[int] = None
    failed_findings: List[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ParsingProgress':
        return cls(**data)

class FindingValidator:
    """Validate parsed findings against schema."""
    
    # Schema for a single finding
    FINDING_SCHEMA = {
        "type": "object",
        "required": ["title", "severity", "vulnerabilityType", "code"],
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "severity": {
                "type": "string",
                "enum": ["Critical", "High", "Medium", "Low", "Gas", "Informational"]
            },
            "vulnerabilityType": {"type": "string", "minLength": 1},
            "exploitScenario": {"type": "string"},
            "remediation": {"type": "string"},
            "references": {"type": "array", "items": {"type": "string"}},
            "code": {
                "type": "object",
                "required": ["filePath", "vulnerableFunction", "vulnerableLines"],
                "properties": {
                    "filePath": {"type": "string"},
                    "snippet": {"type": "string"},
                    "vulnerableFunction": {"type": "string"},
                    "vulnerableLines": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    "controlFlow": {"type": "string"}
                }
            }
        }
    }
    
    @classmethod
    def validate_finding(cls, finding: Dict) -> tuple[bool, Optional[str]]:
        """Validate a finding against the schema."""
        try:
            jsonschema.validate(instance=finding, schema=cls.FINDING_SCHEMA)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, str(e)

class BatchedAuditParser:
    def __init__(self):
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.validator = FindingValidator()
        self.progress: Optional[ParsingProgress] = None

    def _save_progress(self, progress_dir: Path) -> None:
        """Save current parsing progress."""
        if self.progress:
            progress_file = progress_dir / f"{Path(self.progress.markdown_path).stem}_progress.json"
            progress_dir.mkdir(parents=True, exist_ok=True)
            with open(progress_file, 'w') as f:
                json.dump(self.progress.to_dict(), f)

    def _load_progress(self, markdown_path: Path, progress_dir: Path) -> Optional[ParsingProgress]:
        """Load previous parsing progress if it exists."""
        progress_file = progress_dir / f"{markdown_path.stem}_progress.json"
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return ParsingProgress.from_dict(json.load(f))
        return None

    def extract_metadata(self, content: str, progress_dir: Path) -> Dict:
        """Extract basic metadata from the start of the audit report."""
        if self.progress and self.progress.metadata_extracted:
            logger.info("Metadata already extracted, skipping...")
            return {}
            
        try:
            header_section = self._get_header_section(content)
            
            message = """Extract the following metadata as JSON:
            - auditTitle (string)
            - auditDate (YYYY-MM-DD format)
            - auditor (string)
            - projectName (string)

            Return only the JSON object, nothing else.

            Content:
            """
            message += header_section

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0,
                messages=[{"role": "user", "content": message}]
            )
            
            metadata = json.loads(response.content[0].text)
            
            # Update progress
            if self.progress:
                self.progress.metadata_extracted = True
                self._save_progress(progress_dir)
                
            logger.info("Successfully extracted metadata")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return self._get_default_metadata()

    def parse_single_finding(self, finding_content: str, finding_index: int) -> Optional[Dict]:
        """Parse a single finding using Claude and validate it."""
        try:
            message = """Convert this finding into a JSON object with this structure:
            {
                "title": "string",
                "severity": "Critical|High|Medium|Low|Gas|Informational",
                "vulnerabilityType": "string",
                "exploitScenario": "string",
                "remediation": "string",
                "references": [],
                "code": {
                    "filePath": "string",
                    "snippet": "string",
                    "vulnerableFunction": "string",
                    "vulnerableLines": [integers],
                    "controlFlow": "string"
                }
            }

            The severity MUST be one of the exact values listed.
            vulnerableLines must be integers.
            All other fields should be properly formatted strings.
            Return only the JSON object, nothing else.

            Finding content:
            """
            message += finding_content

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": message}]
            )
            
            finding = json.loads(response.content[0].text)
            
            # Validate finding
            is_valid, error = FindingValidator.validate_finding(finding)
            if not is_valid:
                logger.error(f"Finding {finding_index} failed validation: {error}")
                if self.progress:
                    self.progress.failed_findings.append(finding_index)
                return None
                
            logger.info(f"Successfully parsed and validated finding {finding_index}: {finding.get('title', 'Untitled')}")
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing finding {finding_index}: {e}")
            if self.progress:
                self.progress.failed_findings.append(finding_index)
            return None

    def parse_audit_markdown(
        self, 
        markdown_path: Path,
        progress_dir: Path,
        codebase_path: Optional[Path] = None
    ) -> Dict:
        """Parse audit markdown into complete JSON structure with progress tracking."""
        logger.info(f"Processing audit markdown: {markdown_path}")

        # Load or initialize progress
        self.progress = self._load_progress(markdown_path, progress_dir)
        if not self.progress:
            self.progress = ParsingProgress(
                markdown_path=str(markdown_path),
                processed_findings=[],
                failed_findings=[]
            )

        try:
            # Read markdown content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata if needed
            metadata = self.extract_metadata(content, progress_dir)

            # Split findings if needed
            if not self.progress.findings_split:
                findings = list(self.split_findings(content))
                self.progress.total_findings = len(findings)
                self.progress.findings_split = True
                self._save_progress(progress_dir)
            else:
                findings = list(self.split_findings(content))

            # Process findings with progress bar
            vulnerabilities = []
            remaining_findings = [
                i for i in range(len(findings)) 
                if i not in self.progress.processed_findings
            ]
            
            with tqdm(remaining_findings, desc="Processing findings") as pbar:
                for i in pbar:
                    if i in self.progress.processed_findings:
                        continue
                        
                    pbar.set_description(f"Processing finding {i+1}/{len(findings)}")
                    parsed_finding = self.parse_single_finding(findings[i], i)
                    
                    if parsed_finding:
                        vulnerabilities.append(parsed_finding)
                        self.progress.processed_findings.append(i)
                        self._save_progress(progress_dir)
                    pbar.update(1)

            # Load codebase if provided
            codebase = {}
            if codebase_path and codebase_path.exists():
                with open(codebase_path, 'r') as f:
                    codebase = json.load(f).get("codebase", {})

            # Create complete audit report
            audit_report = {
                "auditTitle": metadata.get("auditTitle", "Unknown Audit"),
                "auditDate": metadata.get("auditDate", datetime.now().strftime("%Y-%m-%d")),
                "auditor": metadata.get("auditor", "Unknown"),
                "project": {
                    "name": metadata.get("projectName", "Unknown Project"),
                    "repo": "",
                    "website": ""
                },
                "codebase": codebase,
                "vulnerabilities": vulnerabilities
            }

            # Report statistics
            total = len(findings)
            processed = len(self.progress.processed_findings)
            failed = len(self.progress.failed_findings)
            logger.info(f"\nProcessing complete:")
            logger.info(f"Total findings: {total}")
            logger.info(f"Successfully processed: {processed}")
            logger.info(f"Failed: {failed}")
            
            return audit_report

        except Exception as e:
            logger.error(f"Error processing audit markdown: {e}")
            raise

def process_audit_markdown(
    markdown_path: Path,
    output_path: Path,
    progress_dir: Path,
    codebase_path: Optional[Path] = None
) -> None:
    """Process a markdown audit report and save as JSON."""
    parser = BatchedAuditParser()
    
    # Parse and save report
    report = parser.parse_audit_markdown(markdown_path, progress_dir, codebase_path)
    
    # Save the report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Successfully saved audit report to {output_path}")

def main():
    # Example usage
    markdown_path = Path("data/audits/spearbit_portfolio/markdown/ArtGobblers/ArtGobblers/report.md")
    output_path = Path("data/final/art_gobblers_audit.json")
    progress_dir = Path("data/progress")
    codebase_path = Path("data/processed/art_gobblers_codebase.json")
    
    process_audit_markdown(markdown_path, output_path, progress_dir, codebase_path)

if __name__ == "__main__":
    main()