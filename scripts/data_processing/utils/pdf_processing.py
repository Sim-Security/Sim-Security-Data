# scripts/data_processing/utils/pdf_processing.py

import os
import subprocess

def convert_pdfs_to_markdown(input_dir, output_dir):
    """
    Converts all PDF files in the input directory to markdown using `marker_single`.
    """
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_subdir = os.path.join(output_dir, os.path.splitext(filename)[0])
            os.makedirs(output_subdir, exist_ok=True)

            command = [
                'marker_single',
                input_path,
                '--output_dir',
                output_subdir,
                '--output_format',
                'markdown'
            ]

            print(f"Converting {input_path} to markdown...")
            subprocess.run(command, check=True)
            print(f"Converted {filename} to markdown in {output_subdir}")

def process_spearbit_pdfs():
    """
    Converts PDFs from the Spearbit portfolio repository to markdown.
    """
    pdf_directory = 'data/audits/spearbit_portfolio/pdfs'
    output_directory = 'data/audits/spearbit_portfolio/markdown'
    convert_pdfs_to_markdown(pdf_directory, output_directory)
