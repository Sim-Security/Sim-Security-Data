# scripts/process_to_jsonl.py
from pathlib import Path
import json
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CodeContext:
    file: str
    lines: str
    code: str
    commit: Optional[str] = None

@dataclass
class Finding:
    id: str
    title: str
    severity: str
    context: CodeContext
    description: str
    recommendation: str
    resolution: Optional[str] = None
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert finding to dictionary format for JSON."""
        return {
            "finding_id": self.id,
            "title": self.title,
            "severity": self.severity,
            "context": {
                "file": self.context.file,
                "lines": self.context.lines,
                "code": self.context.code,
                "commit": self.context.commit
            },
            "description": self.description,
            "recommendation": self.recommendation,
            "resolution": self.resolution,
            "tags": self.tags or []
        }

class AuditProcessor:
    def __init__(self):
        # Regular expressions for parsing audit reports
        self.finding_pattern = re.compile(r'###\s*(.*?)\n')
        self.severity_pattern = re.compile(r'\*\*Severity:\*\*\s*(.*?)\n')
        self.context_pattern = re.compile(r'\*\*Context:\*\*\s*(.*?)\n')
        self.description_pattern = re.compile(r'\*\*Description:\*\*\s*(.*?)(?=\*\*|$)', re.DOTALL)
        self.recommendation_pattern = re.compile(r'\*\*Recommendation:\*\*\s*(.*?)(?=\*\*|$)', re.DOTALL)
        self.resolution_pattern = re.compile(r'\*\*Resolution:\*\*\s*(.*?)(?=\*\*|$)', re.DOTALL)
        
    def extract_code_context(self, context_str: str) -> CodeContext:
        """Extract file name and line numbers from context string."""
        # Parse context string like "File: Contract.sol#L45-60"
        file_match = re.search(r'([^#]+)(?:#L(\d+(?:-\d+)?))?\s*$', context_str)
        if file_match:
            file = file_match.group(1).strip()
            lines = file_match.group(2) or "N/A"
            return CodeContext(file=file, lines=lines, code="")  # Code will be added later
        return CodeContext(file="unknown", lines="N/A", code="")

    def parse_finding(self, finding_text: str) -> Optional[Finding]:
        """Parse a single finding from markdown text."""
        try:
            # Extract basic info
            title_match = self.finding_pattern.search(finding_text)
            severity_match = self.severity_pattern.search(finding_text)
            context_match = self.context_pattern.search(finding_text)
            description_match = self.description_pattern.search(finding_text)
            recommendation_match = self.recommendation_pattern.search(finding_text)
            resolution_match = self.resolution_pattern.search(finding_text)
            
            if not all([title_match, severity_match, context_match, description_match]):
                logger.warning("Missing required fields in finding")
                return None
                
            # Create finding object
            finding = Finding(
                id=f"FINDING-{hash(title_match.group(1)) & 0xFFFFFFFF:08x}",
                title=title_match.group(1).strip(),
                severity=severity_match.group(1).strip(),
                context=self.extract_code_context(context_match.group(1)),
                description=description_match.group(1).strip(),
                recommendation=recommendation_match.group(1).strip() if recommendation_match else "",
                resolution=resolution_match.group(1).strip() if resolution_match else None,
                tags=self.extract_tags(finding_text)
            )
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing finding: {e}")
            return None
            
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from finding text."""
        tags = set()
        
        # Add common vulnerability tags
        vulnerability_keywords = [
            "reentrancy", "overflow", "underflow", "access control",
            "input validation", "authentication", "authorization",
            "gas optimization", "dos", "front-running"
        ]
        
        for keyword in vulnerability_keywords:
            if re.search(rf'\b{keyword}\b', text.lower()):
                tags.add(keyword)
                
        return list(tags)
        
    def process_file(self, input_path: Path, output_path: Path) -> None:
        """Process audit report and save as JSONL."""
        logger.info(f"Processing {input_path}")
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split into findings
        findings_text = re.split(r'(?=###\s+)', content)
        findings = []
        
        # Process each finding
        for finding_text in findings_text:
            if finding_text.strip() and '###' in finding_text:
                finding = self.parse_finding(finding_text)
                if finding:
                    findings.append(finding)
                    
        # Save as JSONL
        logger.info(f"Writing {len(findings)} findings to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            for finding in findings:
                json.dump(finding.to_dict(), f, ensure_ascii=False)
                f.write('\n')
                
def main():
    # Set up paths
    input_file = Path("outputs/formatted_report_opus1.md")
    output_file = Path("data/processed/reports/ArtGobblers/findings.jsonl")
    
    # Process file
    processor = AuditProcessor()
    try:
        processor.process_file(input_file, output_file)
        logger.info("Processing completed successfully")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()