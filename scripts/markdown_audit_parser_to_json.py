import os
from pathlib import Path
import anthropic
import json
import logging
import re
from typing import Dict, List, Optional, Iterator
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
    
    def __post_init__(self):
        if self.processed_findings is None:
            self.processed_findings = []
        if self.failed_findings is None:
            self.failed_findings = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ParsingProgress':
        return cls(**data)

class FindingValidator:
    """Validate parsed findings against schema."""
    
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
        try:
            jsonschema.validate(instance=finding, schema=cls.FINDING_SCHEMA)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, str(e)

class AuditParser:
    def __init__(self):
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.validator = FindingValidator()
        self.progress: Optional[ParsingProgress] = None

    def parse_finding(self, finding_content: str, finding_index: int) -> Optional[Dict]:
        """Parse a single finding into JSON format."""
        try:
            message = """Convert this finding into a JSON object with exactly these fields:
            {
                "title": <extract from ### heading>,
                "severity": <must be one of: Critical, High, Medium, Low, Gas, Informational>,
                "vulnerabilityType": <determine from description>,
                "exploitScenario": <extract from description or synthesize>,
                "remediation": <extract from Recommendation section>,
                "code": {
                    "filePath": <extract contract name from Context>,
                    "vulnerableFunction": <extract function name from context/description>,
                    "vulnerableLines": <extract line numbers as integer array, use [] if none>,
                    "snippet": <extract code blocks if any>,
                    "controlFlow": <describe the vulnerable flow>
                }
            }

            Important:
            - vulnerableLines must be integers in an array, use [] if none found
            - severity must be exactly one of the allowed values
            - extract exact file paths and line numbers from Context section
            - include all code blocks in snippet field

            Return ONLY the JSON object, no other text."""

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                    "role": "user", 
                    "content": message + "\n\nFinding Content:\n" + finding_content
                }]
            )

            # Extract and clean JSON
            response_text = response.content[0].text.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            # Parse and validate
            finding = json.loads(response_text)
            is_valid, error = FindingValidator.validate_finding(finding)
            
            if not is_valid:
                logger.error(f"Finding {finding_index} failed validation: {error}")
                return None
                
            logger.info(f"Successfully parsed finding {finding_index}")
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing finding {finding_index}: {e}")
            return None

    def split_findings(self, content: str) -> Iterator[str]:
        """Split markdown content into individual findings."""
        try:
            findings_section = content.split("## Findings", 1)[1].split("## Appendix")[0]
            
            # Match finding headers and capture content until next finding
            finding_pattern = r"### \[.*?\].*?(?=### \[|$)"
            findings = re.finditer(finding_pattern, findings_section, re.DOTALL)
            
            for finding in findings:
                yield finding.group(0).strip()
                
        except Exception as e:
            logger.error(f"Error splitting findings: {e}")
            return []

    def parse_audit_report(self, markdown_path: Path, output_path: Path) -> None:
        """Parse entire audit report and save to JSON."""
        try:
            # Read content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract metadata
            metadata = self.extract_metadata(content)
            
            # Process findings
            findings = []
            for i, finding in enumerate(self.split_findings(content)):
                parsed = self.parse_finding(finding, i)
                if parsed:
                    findings.append(parsed)
                    
            # Create report
            report = {
                "auditTitle": metadata.get("title", "Unknown"),
                "auditDate": metadata.get("date", datetime.now().strftime("%Y-%m-%d")),
                "auditor": metadata.get("auditor", "Unknown"),
                "project": {
                    "name": metadata.get("projectName", "Unknown"),
                    "repository": metadata.get("repository", ""),
                    "commit": metadata.get("commit", ""),
                },
                "findings": findings
            }
            
            # Save report
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Successfully saved parsed report to {output_path}")
            
        except Exception as e:
            logger.error(f"Error parsing audit report: {e}")
            raise

def main():
    input_path = Path("data/processed/Art-Gobblers-Review-Cleaned.md") 
    output_path = Path("data/final/art_gobblers_audit2.json")
    
    parser = AuditParser()
    parser.parse_audit_report(input_path, output_path)

if __name__ == "__main__":
    main()