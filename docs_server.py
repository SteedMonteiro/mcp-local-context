#!/usr/bin/env python3
"""
Local Documentation MCP Server with RAG

This server provides access to local documents stored in source folders,
making it easy for AI assistants to access your library documents.
It uses RAG (Retrieval-Augmented Generation) for semantic search capabilities.
It supports three types of documents: documentations, guides, and conventions.
"""

import os
import glob
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Literal

from mcp.server.fastmcp import FastMCP, Context
from vlite import VLite

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

    parser = argparse.ArgumentParser(description="Local Documentation MCP Server with RAG")
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
    name="Local Development Context MCP",
    instructions="Retrieves development information with documentations, guides, and conventions",
)

# Initialize the vector database
SOURCE_DIRS = [Path(source) for source in args.sources]
vlite_db = VLite(collection="local_docs")

# Document types
DocumentType = Literal["documentation", "guide", "convention"]

# Document type
class DocumentResult:
    def __init__(self, file_path: str, content: str, doc_type: DocumentType, score: Optional[float] = None):
        self.file_path = file_path
        self.content = content
        self.doc_type = doc_type
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "file_path": self.file_path,
            "content": self.content,
            "doc_type": self.doc_type,
        }
        if self.score is not None:
            result["score"] = self.score
        return result

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

def determine_doc_type(file_path: str, content: Optional[str] = None) -> DocumentType:
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
    rel_path = get_relative_path(file_path)

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

@mcp.tool()
def build_docs_index(ctx: Context) -> str:
    """
    Builds or rebuilds the search index for local documents.

    This tool processes all document files and creates a search index for semantic search.
    Use this tool if you've added new document files or updated existing ones.

    The index is used by the 'semantic_search' tool to find relevant documents.
    Documents are categorized as documentation, guides, or conventions.
    """
    # Clear existing index
    vlite_db.clear()

    # Find all markdown and text files in all source directories
    all_files = []
    for source_dir in SOURCE_DIRS:
        markdown_files = glob.glob(f"{source_dir}/**/*.md", recursive=True)
        text_files = glob.glob(f"{source_dir}/**/*.txt", recursive=True)
        mdx_files = glob.glob(f"{source_dir}/**/*.mdx", recursive=True)
        all_files.extend(markdown_files + text_files + mdx_files)

    if not all_files:
        return "No document files found in any of the source directories."

    # Counters for document types
    doc_type_counts = {
        "documentation": 0,
        "guide": 0,
        "convention": 0
    }

    # Add each file to the index
    for file_path in all_files:
        try:
            content = get_file_content(file_path)
            relative_path = get_relative_path(file_path)

            # Determine document type
            doc_type = determine_doc_type(file_path, content)
            doc_type_counts[doc_type] += 1

            # Add to vlite with metadata including document type
            vlite_db.add(
                data=content,
                metadata={
                    "file_path": relative_path,
                    "doc_type": doc_type
                }
            )

            ctx.info(f"Indexed: {relative_path} (Type: {doc_type})")
        except Exception as e:
            ctx.error(f"Error indexing {file_path}: {str(e)}")

    # Create summary message
    summary = f"Successfully indexed {len(all_files)} files:\n"
    summary += f"- Documentation: {doc_type_counts['documentation']}\n"
    summary += f"- Guides: {doc_type_counts['guide']}\n"
    summary += f"- Conventions: {doc_type_counts['convention']}"

    return summary

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
def list_docs_by_type(doc_type: DocumentType) -> List[str]:
    """
    Lists all document files of a specific type.

    This tool provides a list of all document files of the specified type
    (documentation, guide, or convention) available in the configured source directories.

    Args:
        doc_type: The type of document to list ("documentation", "guide", or "convention")

    Returns:
        A list of file paths relative to their source directories.
    """
    # Get all files
    all_files = list_local_docs()

    # Filter files by type
    result_files = []
    for file_path in all_files:
        # Find the source directory for this file
        source_prefix = file_path.split('/')[0]
        source_dir = next((s for s in SOURCE_DIRS if s.name == source_prefix), None)

        if source_dir:
            # Get the path within the source directory
            relative_path = '/'.join(file_path.split('/')[1:])
            full_path = os.path.join(source_dir, relative_path)
            content = get_file_content(full_path)
            file_doc_type = determine_doc_type(full_path, content)

            if file_doc_type == doc_type:
                result_files.append(file_path)

    return result_files

@mcp.tool()
def search_local_docs(query: str, doc_type: Optional[DocumentType] = None) -> List[str]:
    """
    Searches for document files in the local sources directory that match a query.

    This tool helps you find specific document files based on a search query.
    The search is performed on file paths and matches any part of the path.
    You can optionally filter by document type.

    Args:
        query: Search query to find matching document files.
        doc_type: Optional document type to filter results ("documentation", "guide", or "convention").

    Returns:
        A list of file paths that match the query.
    """
    # Get all docs or filter by type first
    if doc_type:
        all_docs = list_docs_by_type(doc_type)
    else:
        all_docs = list_local_docs()

    # Filter by query
    matching_docs = [doc for doc in all_docs if query.lower() in doc.lower()]
    return matching_docs

@mcp.tool()
def semantic_search(query: str, max_results: int = 5, doc_type: Optional[DocumentType] = None) -> List[Dict[str, Any]]:
    """
    Performs semantic search on documentation content using RAG.

    This tool searches for documentation based on the meaning of your query, not just keyword matching.
    It uses vector embeddings to find the most semantically similar documents and returns excerpts from them.
    You can optionally filter by document type.

    Args:
        query: Search query to find semantically relevant documentation.
        max_results: Maximum number of results to return (default: 5).
        doc_type: Optional document type to filter results ("documentation", "guide", or "convention").

    Returns:
        A list of documents with their file paths, content excerpts, document type, and relevance scores.
    """
    try:
        # Retrieve similar documents from vlite
        results = vlite_db.retrieve(
            text=query,
            top_k=max_results * 3,  # Get more results if we need to filter
            return_scores=True
        )

        # Format the results
        formatted_results = []
        for _, text, metadata, score in results:
            # Get the file path and document type from metadata
            file_path = metadata.get("file_path", "unknown")
            doc_type_value = metadata.get("doc_type", "documentation")

            # Filter by document type if specified
            if doc_type and doc_type_value != doc_type:
                continue

            # Extract a snippet (first 200 characters)
            excerpt = text[:200] + "..." if len(text) > 200 else text

            # Create a document result
            doc = DocumentResult(file_path, excerpt, doc_type_value, score)
            formatted_results.append(doc.to_dict())

            # Limit results to max_results
            if len(formatted_results) >= max_results:
                break

        return formatted_results
    except Exception as e:
        return [{"error": f"Error performing semantic search: {str(e)}"}]

@mcp.tool()
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

    # Determine document type
    doc_type = determine_doc_type(full_path, content)

    return {
        "file_path": file_path,
        "content": content,
        "doc_type": doc_type
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
    print(f"Starting Local Documentation MCP Server...")
    print(f"Serving documents from: {', '.join(str(os.path.abspath(s)) for s in SOURCE_DIRS)}")
    print(f"Supporting document types: documentation, guides, and conventions")

    # Try to build the index if it doesn't exist
    if not vlite_db.count():
        print("Building document index...")
        try:
            # Find all markdown and text files in all source directories
            all_files = []
            for source_dir in SOURCE_DIRS:
                markdown_files = glob.glob(f"{source_dir}/**/*.md", recursive=True)
                text_files = glob.glob(f"{source_dir}/**/*.txt", recursive=True)
                mdx_files = glob.glob(f"{source_dir}/**/*.mdx", recursive=True)
                all_files.extend(markdown_files + text_files + mdx_files)

            # Counters for document types
            doc_type_counts = {
                "documentation": 0,
                "guide": 0,
                "convention": 0
            }

            # Add each file to the index
            for file_path in all_files:
                content = get_file_content(file_path)
                relative_path = get_relative_path(file_path)

                # Determine document type
                doc_type = determine_doc_type(file_path, content)
                doc_type_counts[doc_type] += 1

                # Add to vlite with metadata including document type
                vlite_db.add(
                    data=content,
                    metadata={
                        "file_path": relative_path,
                        "doc_type": doc_type
                    }
                )

                print(f"Indexed: {relative_path} (Type: {doc_type})")

            # Print summary
            print(f"Successfully indexed {len(all_files)} files:")
            print(f"- Documentation: {doc_type_counts['documentation']}")
            print(f"- Guides: {doc_type_counts['guide']}")
            print(f"- Conventions: {doc_type_counts['convention']}")

        except Exception as e:
            print(f"Error building index: {str(e)}")
            print("You can build the index manually using the 'build_docs_index' tool.")

    # Run the server with streamable-http transport
    mcp.run(transport="streamable-http", mount_path=args.path)

if __name__ == "__main__":
    main()
