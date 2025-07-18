#!/usr/bin/env python3
"""
Simple MCP Server for local documentation.

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

# Document types
DocumentType = Literal["documentation", "guide", "convention"]

class SimpleMCPServer:
    """Simple MCP Server for serving local documentation."""

    def __init__(self, source_dirs=None, host="127.0.0.1", port=8000, path="/mcp"):
        """Initialize the Simple MCP Server.

        Args:
            source_dirs: List of source directories to serve documents from
            host: Host to run the server on
            port: Port to run the server on
            path: Path for the MCP endpoint
        """
        # Set default source directories if none provided
        if source_dirs is None:
            source_dirs = ["sources"]

        # Convert to Path objects
        self.source_dirs = [Path(source) for source in source_dirs]
        self.host = host
        self.port = port
        self.path = path

        # Initialize the MCP server
        self.mcp = FastMCP(
            name="Local Context MCP",
            instructions="Retrieves development information with documentations, guides, and conventions",
        )

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register tools with the MCP server."""
        # Register the list_local_docs tool
        @self.mcp.tool()
        def list_local_docs() -> List[str]:
            """
            Lists all available document files in all source directories.

            This tool provides a comprehensive list of all document files available in the configured source directories.
            Use this to discover what documents are available locally before requesting specific files.

            Returns:
                A list of file paths relative to their source directories.
            """
            return self._list_local_docs()

        # Register the get_local_doc tool
        @self.mcp.tool()
        def get_local_doc(file_path: str) -> Dict[str, Any]:
            """
            Fetches the content of a specific document file from the source directories.

            This tool retrieves the full content of a document file specified by its path.
            The path should be in the format 'source_dir_name/path/to/file.md'.

            Args:
                file_path: Path to the document file (e.g., 'sources/app-studio/README.md').

            Returns:
                The content of the document file along with its document type.
            """
            return self._get_local_doc(file_path)

    def _list_local_docs(self) -> List[str]:
        """List all available document files in all source directories."""
        all_files = []
        for source_dir in self.source_dirs:
            markdown_files = glob.glob(f"{source_dir}/**/*.md", recursive=True)
            text_files = glob.glob(f"{source_dir}/**/*.txt", recursive=True)
            mdx_files = glob.glob(f"{source_dir}/**/*.mdx", recursive=True)
            all_files.extend(markdown_files + text_files + mdx_files)

        # Convert to relative paths
        relative_paths = [self._get_relative_path(file_path) for file_path in all_files]

        # Sort for better readability
        relative_paths.sort()

        return relative_paths

    def _get_local_doc(self, file_path: str) -> Dict[str, Any]:
        """Get the content of a specific document file."""
        # Parse the source directory and relative path
        parts = file_path.split('/', 1)
        if len(parts) < 2:
            return {"error": f"Invalid file path format. Expected 'source_dir/path/to/file', got: {file_path}"}

        source_name, relative_path = parts

        # Find the matching source directory
        source_dir = next((s for s in self.source_dirs if s.name == source_name), None)
        if not source_dir:
            return {"error": f"Source directory '{source_name}' not found"}

        # Build the full path
        full_path = os.path.join(source_dir, relative_path)

        # Check if the file exists
        if not os.path.isfile(full_path):
            return {"error": f"File not found: {file_path}"}

        # Read the file content
        content = self._get_file_content(full_path)

        # Determine document type
        doc_type = self._determine_doc_type(full_path, content)

        return {
            "file_path": file_path,
            "content": content,
            "doc_type": doc_type
        }

    def _get_file_content(self, file_path: str) -> str:
        """Read the content of a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _get_relative_path(self, file_path: str) -> str:
        """Get the path relative to the source directories."""
        abs_path = os.path.abspath(file_path)

        # Check each source directory
        for source_dir in self.source_dirs:
            abs_docs = os.path.abspath(source_dir)
            if abs_path.startswith(abs_docs):
                return f"{source_dir.name}/{os.path.relpath(abs_path, abs_docs)}"

        return file_path

    def _determine_doc_type(self, file_path: str, content: Optional[str] = None) -> DocumentType:
        """
        Determine the document type based on file path and/or content.

        Rules:
        - Files with "guide" in the path or title are guides
        - Files with "convention" in the path or title are conventions
        - All other files are considered documentation

        Args:
            file_path: Path to the file
            content: Optional content of the file to analyze

        Returns:
            Document type: "documentation", "guide", or "convention"
        """
        rel_path = self._get_relative_path(file_path)

        # Check path for guide or convention indicators
        if "guide" in rel_path.lower():
            return "guide"
        elif "convention" in rel_path.lower():
            return "convention"

        # If content is provided, check for indicators in the first few lines
        if content:
            first_lines = content.split('\n')[:10]
            first_text = '\n'.join(first_lines).lower()

            if "guide" in first_text or "how to" in first_text:
                return "guide"
            elif "convention" in first_text or "standard" in first_text or "rule" in first_text:
                return "convention"

        # Default to documentation
        return "documentation"

    def run(self):
        """Run the MCP server."""
        # Check if the source directories exist
        for source_dir in self.source_dirs:
            if not os.path.isdir(source_dir):
                print(f"Warning: Source directory '{source_dir}' not found. Creating it...")
                os.makedirs(source_dir, exist_ok=True)

        # Run the server
        print(f"Starting Simple MCP Server...")
        print(f"Serving documents from: {', '.join(str(os.path.abspath(s)) for s in self.source_dirs)}")

        # Run the server with streamable-http transport
        self.mcp.run(transport="streamable-http", mount_path=self.path)


def main():
    """Main entry point for the Simple MCP Server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Simple MCP Server")
    parser.add_argument(
        "sources",
        nargs="*",
        help="List of source folders to index (default: sources)"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host to run the server on (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--path",
        default=os.environ.get("MCP_PATH", "/mcp"),
        help="Path for the MCP endpoint (default: /mcp)"
    )
    args = parser.parse_args()

    # Set default sources if none provided
    if not args.sources:
        args.sources = ["sources"]

    # Create and run the server
    server = SimpleMCPServer(
        source_dirs=args.sources,
        host=args.host,
        port=args.port,
        path=args.path
    )
    server.run()


if __name__ == "__main__":
    main()
