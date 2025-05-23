#!/usr/bin/env python3
"""
Simple MCP Server for testing.

This is a minimal MCP server that doesn't depend on vlite.
"""

import os
import glob
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Literal

from mcp.server.fastmcp import FastMCP, Context

# Parse command-line arguments
def parse_args():
    # Get default values from environment variables if available
    default_sources = os.environ.get("SOURCE_DIRS", "sources")
    if "," in default_sources:
        default_sources = default_sources.split(",")
    else:
        default_sources = [default_sources]

    default_host = os.environ.get("MCP_HOST", "127.0.0.1")
    default_port = int(os.environ.get("MCP_PORT", "8000"))
    default_path = os.environ.get("MCP_PATH", "/mcp")

    parser = argparse.ArgumentParser(description="Simple MCP Server for testing")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=default_sources,
        help=f"List of source folders to index (default: {default_sources})"
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Host to run the server on (default: {default_host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to run the server on (default: {default_port})"
    )
    parser.add_argument(
        "--path",
        default=default_path,
        help=f"Path for the MCP endpoint (default: {default_path})"
    )
    return parser.parse_args()

# Get command-line arguments
args = parse_args()

# Initialize the MCP server
mcp = FastMCP(
    name="Simple MCP Server",
    instructions="A simple MCP server for testing",
)

# Initialize the source directories
SOURCE_DIRS = [Path(source) for source in args.sources]

# Document types
DocumentType = Literal["documentation", "guide", "convention"]

def get_file_content(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def get_relative_path(file_path: str) -> str:
    """Get the path relative to the source directories."""
    abs_path = os.path.abspath(file_path)

    # Check each source directory
    for source_dir in SOURCE_DIRS:
        abs_docs = os.path.abspath(source_dir)
        if abs_path.startswith(abs_docs):
            return f"{source_dir.name}/{os.path.relpath(abs_path, abs_docs)}"

    return file_path

@mcp.tool()
def list_local_docs() -> List[str]:
    """
    Lists all available document files in all source directories.

    This tool provides a comprehensive list of all document files available in the configured source directories.
    Use this to discover what documents are available locally before requesting specific files.

    Returns:
        A list of file paths relative to their source directories.
    """
    all_files = []
    for source_dir in SOURCE_DIRS:
        markdown_files = glob.glob(f"{source_dir}/**/*.md", recursive=True)
        text_files = glob.glob(f"{source_dir}/**/*.txt", recursive=True)
        mdx_files = glob.glob(f"{source_dir}/**/*.mdx", recursive=True)
        all_files.extend(markdown_files + text_files + mdx_files)

    # Convert to relative paths
    relative_paths = [get_relative_path(file_path) for file_path in all_files]

    # Sort for better readability
    relative_paths.sort()

    return relative_paths

@mcp.tool()
def get_local_doc(file_path: str) -> Dict[str, Any]:
    """
    Fetches the content of a specific document file from the source directories.

    This tool retrieves the full content of a document file specified by its path.
    The path should be in the format 'source_dir_name/path/to/file.md'.

    Args:
        file_path: Path to the document file (e.g., 'sources/app-studio/README.md').

    Returns:
        The content of the document file.
    """
    # Parse the source directory and relative path
    parts = file_path.split('/', 1)
    if len(parts) < 2:
        return {"error": f"Invalid file path format. Expected 'source_dir/path/to/file', got: {file_path}"}

    source_name, relative_path = parts

    # Find the matching source directory
    source_dir = next((s for s in SOURCE_DIRS if s.name == source_name), None)
    if not source_dir:
        return {"error": f"Source directory '{source_name}' not found"}

    # Build the full path
    full_path = os.path.join(source_dir, relative_path)

    # Check if the file exists
    if not os.path.isfile(full_path):
        return {"error": f"File not found: {file_path}"}

    # Read the file content
    content = get_file_content(full_path)

    return {
        "file_path": file_path,
        "content": content
    }

def main():
    """Main entry point for the MCP server."""
    global SOURCE_DIRS

    # Check if the source directories exist
    for source_dir in SOURCE_DIRS:
        if not os.path.isdir(source_dir):
            print(f"Warning: Source directory '{source_dir}' not found. Creating it...")
            os.makedirs(source_dir, exist_ok=True)

    # Run the server
    print(f"Starting Simple MCP Server...")
    print(f"Serving documents from: {', '.join(str(os.path.abspath(s)) for s in SOURCE_DIRS)}")

    # Run the server with streamable-http transport
    mcp.run(transport="streamable-http", mount_path=args.path)

if __name__ == "__main__":
    main()
