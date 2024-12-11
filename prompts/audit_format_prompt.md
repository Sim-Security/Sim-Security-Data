# Audit Report Formatting Instructions

You are tasked with reformatting smart contract security audit reports into a consistent, clean markdown format. Follow these formatting rules strictly:

## Document Structure
1. Title should be a level-1 header with project name and "Security Review"
2. Always include these main sections in order:
   - Auditors
   - About Spearbit
   - Introduction
   - Risk Classification
   - Executive Summary
   - Findings
   - Appendix (if present)

## Metadata Formatting
1. Auditor names should be in a clean list
2. Dates should be in format: Month DD, YYYY
3. Project metadata should be in a table with these exact headers:
   | Project Name | Repository | Commit | Type | Timeline | Methods |

## Risk Classification
Format the risk matrix as a clean table with:
- Clear severity levels (Critical, High, Medium, Low)
- Impact and Likelihood definitions
- Required actions for each level

## Findings Section
Each finding must be formatted consistently:

### [Finding Title] {#finding-id}

**Severity:** [Critical/High/Medium/Low/Gas/Informational]

**Context:** [File/Contract names and line numbers]

**Description:**  
[Clear description of the issue]

**Recommendation:**  
[Specific recommendations to address the issue]

**Resolution:**  
[Team's response and resolution status if provided]

## Formatting Rules
1. Code blocks must use triple backticks with language specified:
   ```solidity
   // code here
   ```
2. LaTeX equations must be properly fenced with double dollar signs:
   - Inline: $$equation$$
   - Block: 
     $$
     equation
     $$
3. Tables must be properly aligned with headers
4. Section numbers should be clean and properly nested
5. Remove any duplicate or redundant formatting
6. Ensure consistent spacing between sections

Follow these instructions exactly to reformat the audit report provided. Maintain all technical content exactly as is, only modifying the formatting and structure.