Below is a high-level pseudocode representation of the entire project, including directory structures, files, and the general logic within each file. This pseudocode aims to capture the structure, main functions, and workflow without tying to any specific programming language syntax. It serves as a blueprint or conceptual guide rather than ready-to-execute code.

---

### Project Directory Structure (Pseudocode)

```
project_root/
    scripts/
        data_processing/
            collect_data (script)
            utils/
                __init__ (empty file or namespace initializer)
                fetchers
                pdf_processing
                markdown_cleaners
                cleaners
                labelers
                splitters
    data/
        audits/
            spearbit_portfolio/
                pdfs/           (raw PDF files from cloned repo)
                markdown/       (PDF-to-markdown output)
        processed/
            reports/           (cleaned markdown files ready for further processing)
        raw/                   (if needed for raw data)
        logs/                  (if needed for logs)
```

---

### `fetchers` Pseudocode

**Location:** `scripts/data_processing/utils/fetchers`

**Purpose:**  
- Clone or update repositories containing audit reports.
- Potentially fetch web-based data sources (if needed).

**Pseudocode:**
```
function clone_or_update_repository(repo_url, destination):
    if destination does not exist:
        print "Cloning repository..."
        clone repo_url to destination
        print "Repository cloned."
    else:
        print "Repository exists, pulling latest changes..."
        open repository at destination
        pull latest changes
        print "Repository updated."

function fetch_audit_reports():
    spearbit_repo_url <- "https://github.com/spearbit/portfolio.git"
    spearbit_destination <- "data/audits/spearbit_portfolio"
    clone_or_update_repository(spearbit_repo_url, spearbit_destination)

    # Future: add more repos if needed
```

---

### `pdf_processing` Pseudocode

**Location:** `scripts/data_processing/utils/pdf_processing`

**Purpose:**  
- Convert PDFs to markdown using a tool (e.g., `marker_single`).
- Organize output into per-file subdirectories.

**Pseudocode:**
```
function convert_pdfs_to_markdown(input_dir, output_dir):
    ensure output_dir exists
    for each file in input_dir:
        if file is PDF:
            input_path <- input_dir + file
            output_subdir <- output_dir + basename(file_without_ext)
            ensure output_subdir exists
            run external command:
                "marker_single input_path --output_dir output_subdir --output_format markdown"
            print "Converted file to markdown in output_subdir"

function process_spearbit_pdfs():
    pdf_directory <- "data/audits/spearbit_portfolio/pdfs"
    output_directory <- "data/audits/spearbit_portfolio/markdown"
    convert_pdfs_to_markdown(pdf_directory, output_directory)
```

---

### `markdown_cleaners` Pseudocode

**Location:** `scripts/data_processing/utils/markdown_cleaners`

**Purpose:**  
- Clean and normalize the generated markdown files.
- Example: remove excessive whitespace, fix formatting issues.

**Pseudocode:**
```
function clean_markdown_file(input_path, output_path):
    content <- read input_path
    cleaned_content <- content
    cleaned_content <- remove excessive blank lines
    cleaned_content <- trim trailing whitespaces from each line
    write cleaned_content to output_path

function clean_markdown_directory(input_dir, output_dir):
    ensure output_dir exists
    for each file in input_dir:
        if file ends with ".md":
            input_path <- input_dir + file
            output_path <- output_dir + file
            print "Cleaning input_path..."
            clean_markdown_file(input_path, output_path)
            print "Cleaned file saved to output_path"
```

---

### `cleaners` Pseudocode (General Data Cleaning)

**Location:** `scripts/data_processing/utils/cleaners`

**Purpose:**  
- General text cleaning (e.g., for final dataset training).
- Remove extraneous whitespace, normalize formatting.

**Pseudocode:**
```
function clean_text(text):
    text <- trim leading/trailing whitespace
    text <- collapse multiple spaces into one
    return text

function clean_entries(entries):
    for each entry in entries:
        entry.title <- clean_text(entry.title)
        entry.content <- clean_text(entry.content)
    return entries
```

---

### `labelers` Pseudocode

**Location:** `scripts/data_processing/utils/labelers`

**Purpose:**  
- Tokenize data and apply vulnerability/platform labels based on keywords.
- Add remediation notes and store tokens.

**Pseudocode:**
```
VULNERABILITY_KEYWORDS <- {
    "reentrancy": {type: "Reentrancy", severity: "High"},
    "overflow": {type: "Integer Overflow", severity: "Medium"},
    "rug pull": {type: "Rug Pull", severity: "High"}
}

PLATFORM_KEYWORDS <- ["ethereum", "solana"]

function tokenize_text(text):
    return split text by whitespace

function annotate_entry(entry):
    content_lower <- lowercase(entry.content)
    tokens <- tokenize_text(content_lower)

    entry.vulnerability_type <- "Unknown"
    entry.severity <- "Unknown"
    entry.platform_label <- "Generic"

    for each (keyword, info) in VULNERABILITY_KEYWORDS:
        if keyword in content_lower:
            entry.vulnerability_type <- info.type
            entry.severity <- info.severity
            break

    for p in PLATFORM_KEYWORDS:
        if p in content_lower:
            entry.platform_label <- capitalize(p)
            break

    entry.remediation <- "Refer to standard secure coding guidelines."
    entry.tokens <- tokens
    return entry

function annotate_data(entries):
    for each entry in entries:
        entry <- annotate_entry(entry)
    return entries
```

---

### `splitters` Pseudocode

**Location:** `scripts/data_processing/utils/splitters`

**Purpose:**  
- Split annotated dataset into training, validation, and test sets.
- Shuffle entries and divide by given ratios.

**Pseudocode:**
```
function split_dataset(entries, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    check that train_ratio + val_ratio + test_ratio = 1.0
    shuffle entries
    total <- length(entries)
    train_end <- floor(total * train_ratio)
    val_end <- train_end + floor(total * val_ratio)

    train_set <- entries[0:train_end]
    val_set <- entries[train_end:val_end]
    test_set <- entries[val_end:total]

    return (train_set, val_set, test_set)
```

---

### `collect_data` Pseudocode

**Location:** `scripts/data_processing/collect_data`

**Purpose:**  
- Orchestrate full workflow: fetch data, process PDFs, clean markdown, (optionally) clean and label data, and split sets.

**Pseudocode:**
```
function main():
    # Step 1: Fetch audit reports (clone repositories)
    fetch_audit_reports()

    # Step 2: Convert PDFs to markdown
    process_spearbit_pdfs()

    # Step 3: Clean markdown files
    markdown_input_dir <- "data/audits/spearbit_portfolio/markdown"
    markdown_output_dir <- "data/processed/reports"
    clean_markdown_directory(markdown_input_dir, markdown_output_dir)

    # Optionally, load processed data, clean, label, and split
    # raw_entries <- load json/csv from markdown_output_dir or other sources
    # cleaned_entries <- clean_entries(raw_entries)
    # annotated_entries <- annotate_data(cleaned_entries)
    # (train, val, test) <- split_dataset(annotated_entries)

    # Save (train, val, test) sets as needed in JSON or other formats

    print "Data ingestion and preprocessing completed."

if run as main:
    main()
```

---

### Summary

This pseudocode representation shows how each component interacts within the project. It provides a conceptual framework for data ingestion (cloning repos, fetching PDFs), file conversion (PDF to markdown), data cleaning, labeling, and dataset splitting for training a model. You can adapt the pseudocode back into actual code as needed, using the appropriate language constructs and libraries.