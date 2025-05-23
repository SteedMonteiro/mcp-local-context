#!/usr/bin/env python3
"""
Test script for document type classification.
"""

import os
import glob
from pathlib import Path

# Import the document type determination function
from docs_server import determine_doc_type, get_file_content

# Directory containing the sources
SOURCES_DIR = Path("sources")

def main():
    """Test document type classification."""
    print("Testing document type classification...")

    # Find all markdown and text files in the sources directory
    markdown_files = glob.glob(f"{SOURCES_DIR}/**/*.md", recursive=True)
    text_files = glob.glob(f"{SOURCES_DIR}/**/*.txt", recursive=True)
    mdx_files = glob.glob(f"{SOURCES_DIR}/**/*.mdx", recursive=True)
    all_files = markdown_files + text_files + mdx_files

    # Counters for document types
    doc_type_counts = {
        "documentation": 0,
        "guide": 0,
        "convention": 0
    }

    # Process each file
    for file_path in all_files:
        content = get_file_content(file_path)
        doc_type = determine_doc_type(file_path, content)
        doc_type_counts[doc_type] += 1

        # Print the file path and its determined type
        print(f"File: {file_path}")
        print(f"Type: {doc_type}")
        print("-" * 50)

    # Print summary
    print("\nSummary:")
    print(f"Total files: {len(all_files)}")
    print(f"Documentation: {doc_type_counts['documentation']}")
    print(f"Guides: {doc_type_counts['guide']}")
    print(f"Conventions: {doc_type_counts['convention']}")

if __name__ == "__main__":
    main()
