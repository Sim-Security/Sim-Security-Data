import pymupdf4llm
import pathlib

# Convert PDF to Markdown``
md_text = pymupdf4llm.to_markdown("data_git/audits/Art-Gobblers/ArtGobblers-Spearbit-Security-Review.pdf")
output_path = pathlib.Path("data_git/processed/Art-Gobblers-Review-pymupdf.md").write_bytes(md_text.encode())