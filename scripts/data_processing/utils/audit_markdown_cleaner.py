# scripts/data_processing/utils/audit_markdown_cleaner.py

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Finding:
    id: str
    title: str
    severity: str
    context: str
    description: str
    recommendation: str
    response: Optional[str] = None

class AuditMarkdownCleaner:
    def __init__(self):
        # Regex patterns for parsing
        self.section_pattern = re.compile(r'^#+\s*(?:\d+\.)*\d+\s+(.+)$')
        self.finding_pattern = re.compile(r'^#+\s*(?:\d+\.)*\d+\.\d+\s+(.+)$')
        self.severity_pattern = re.compile(r'^\*?(Severity|Risk):\s*\*?([^*\n]+)\*?$', re.IGNORECASE)
        self.context_pattern = re.compile(r'^\*?(Context|Location|File):\s*\*?([^*\n]+)\*?$', re.IGNORECASE)
        
    def clean_content(self, content: str) -> str:
        """Clean and format audit report markdown content."""
        sections = self._split_into_sections(content)
        cleaned_sections = []
        
        for section in sections:
            if section.startswith('# **'):  # Main header
                cleaned_sections.append(self._clean_header(section))
            elif '| --- |' in section:  # Table
                cleaned_sections.append(self._clean_table(section))
            elif 'Severity:' in section or 'Risk:' in section:  # Finding
                cleaned_sections.append(self._clean_finding(section))
            else:
                cleaned_sections.append(self._clean_text_section(section))
        
        return '\n\n'.join(cleaned_sections)
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections based on headers."""
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.startswith('#') and current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = [line]
            else:
                current_section.append(line)
                
        if current_section:
            sections.append('\n'.join(current_section).strip())
            
        return sections
    
    def _clean_header(self, section: str) -> str:
        """Clean and format section headers."""
        # Remove extra asterisks and spaces
        section = re.sub(r'\*\*([^*]+)\*\*', r'\1', section)
        # Ensure proper header formatting
        section = re.sub(r'^(#+)\s+', r'\1 ', section)
        return section.strip()
    
    def _clean_table(self, section: str) -> str:
        """Clean and format markdown tables."""
        lines = section.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if not line.strip():
                continue
            # Clean up excessive separators
            if '---' in line:
                cells = [cell.strip() for cell in line.split('|')]
                cleaned_lines.append('| ' + ' | '.join(['---' for cell in cells if cell]) + ' |')
            else:
                cells = [cell.strip() for cell in line.split('|')]
                cleaned_lines.append('| ' + ' | '.join([cell for cell in cells if cell]) + ' |')
        
        return '\n'.join(cleaned_lines)
    
    def _clean_finding(self, section: str) -> str:
        """Clean and format a finding section."""
        lines = section.split('\n')
        finding = Finding(
            id="",
            title="",
            severity="",
            context="",
            description="",
            recommendation="",
            response=None
        )
        
        # Parse finding content
        current_section = ""
        section_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Extract title and ID from header
                header_match = self.finding_pattern.match(line)
                if header_match:
                    finding.title = header_match.group(1).strip()
            elif severity_match := self.severity_pattern.match(line):
                finding.severity = severity_match.group(2).strip()
            elif context_match := self.context_pattern.match(line):
                finding.context = context_match.group(2).strip()
            elif line.strip().lower().startswith('recommendation'):
                if section_content:
                    finding.description = '\n'.join(section_content).strip()
                current_section = "recommendation"
                section_content = []
            elif line.strip().lower().startswith(('art gobblers:', 'spearbit:', 'overlay:')):
                if current_section == "recommendation":
                    finding.recommendation = '\n'.join(section_content).strip()
                current_section = "response"
                section_content = [line]
            else:
                section_content.append(line)
        
        # Format finding as markdown
        formatted = [
            f"### {finding.title}",
            "",
            f"**Severity:** {finding.severity}",
            "",
            f"**Context:** {finding.context}",
            "",
            "**Description:**",
            finding.description,
            "",
            "**Recommendation:**",
            finding.recommendation
        ]
        
        if finding.response:
            formatted.extend([
                "",
                "**Response:**",
                finding.response
            ])
        
        return '\n'.join(formatted)
    
    def _clean_text_section(self, section: str) -> str:
        """Clean and format regular text sections."""
        lines = section.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean excessive whitespace
            line = ' '.join(line.split())
            # Fix bold formatting
            line = re.sub(r'\*\*\s*([^*]+)\s*\*\*', r'**\1**', line)
            # Fix italic formatting
            line = re.sub(r'_\s*([^_]+)\s*_', r'_\1_', line)
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _format_latex(self, text: str) -> str:
        """Format LaTeX equations consistently."""
        # Handle inline equations
        text = re.sub(r'\$([^$]+)\$', r'$$\1$$', text)
        # Handle block equations
        text = re.sub(r'\$\$([^$]+)\$\$', lambda m: '\n$$\n' + m.group(1).strip() + '\n$$\n', text)
        return text
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Process a single markdown file."""
        if output_path is None:
            output_path = input_path.parent / f"cleaned_{input_path.name}"
            
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        cleaned_content = self.clean_content(content)
        cleaned_content = self._format_latex(cleaned_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            
        return output_path
    
    def process_directory(self, input_dir: Path, output_dir: Path) -> List[Path]:
        """Process all markdown files in a directory."""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        for md_file in input_dir.glob("**/*.md"):
            relative_path = md_file.relative_to(input_dir)
            output_path = output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            processed_path = self.process_file(md_file, output_path)
            processed_files.append(processed_path)
            
        return processed_files