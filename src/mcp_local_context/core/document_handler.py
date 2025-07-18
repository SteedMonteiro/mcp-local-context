"""
Document Handler Module

This module handles document file operations, content reading, and path management.
"""

import os
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any


class DocumentHandler:
    """
    Handles document file operations and content management.
    
    This class provides methods for discovering, reading, and managing
    document files across multiple source directories.
    """

    def __init__(self, source_dirs: List[Path]):
        """
        Initialize the document handler.
        
        Args:
            source_dirs: List of source directories to manage
        """
        self.source_dirs = source_dirs
        self.supported_extensions = [".md", ".txt", ".mdx"]

    def get_all_document_files(self) -> List[str]:
        """
        Get all document files from all source directories.
        
        Returns:
            List of absolute file paths for all supported document files
        """
        all_files = []
        for source_dir in self.source_dirs:
            for ext in self.supported_extensions:
                pattern = f"{source_dir}/**/*{ext}"
                files = glob.glob(pattern, recursive=True)
                all_files.extend(files)
        return all_files

    def get_file_content(self, file_path: str) -> str:
        """
        Read the content of a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string, or error message if reading fails
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def get_relative_path(self, file_path: str) -> str:
        """
        Get the path relative to the source directories.
        
        Args:
            file_path: Absolute path to the file
            
        Returns:
            Relative path in format 'source_dir_name/path/to/file'
        """
        abs_path = os.path.abspath(file_path)

        # Check each source directory
        for source_dir in self.source_dirs:
            abs_docs = os.path.abspath(source_dir)
            if abs_path.startswith(abs_docs):
                return f"{source_dir.name}/{os.path.relpath(abs_path, abs_docs)}"

        return file_path

    def list_documents(self) -> List[str]:
        """
        List all available document files with relative paths.
        
        Returns:
            Sorted list of relative file paths
        """
        all_files = self.get_all_document_files()
        relative_paths = [self.get_relative_path(file_path) for file_path in all_files]
        relative_paths.sort()
        return relative_paths

    def get_document_content(self, file_path: str) -> Dict[str, Any]:
        """
        Get the content of a specific document file.
        
        Args:
            file_path: Relative path in format 'source_dir/path/to/file'
            
        Returns:
            Dictionary containing file content and metadata, or error information
        """
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
        content = self.get_file_content(full_path)

        return {
            "file_path": file_path,
            "content": content,
            "full_path": full_path
        }

    def search_documents_by_path(self, query: str, documents: Optional[List[str]] = None) -> List[str]:
        """
        Search for documents by path/filename.
        
        Args:
            query: Search query to match against file paths
            documents: Optional list of documents to search within (defaults to all documents)
            
        Returns:
            List of matching document paths
        """
        if documents is None:
            documents = self.list_documents()
        
        # Filter by query (case-insensitive)
        matching_docs = [doc for doc in documents if query.lower() in doc.lower()]
        return matching_docs

    def ensure_source_directories(self):
        """
        Ensure all source directories exist, creating them if necessary.
        """
        for source_dir in self.source_dirs:
            if not os.path.isdir(source_dir):
                print(f"Warning: Source directory '{source_dir}' not found. Creating it...")
                os.makedirs(source_dir, exist_ok=True)

    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about the configured source directories.
        
        Returns:
            Dictionary containing source directory information
        """
        info = {
            "source_directories": [str(d) for d in self.source_dirs],
            "supported_extensions": self.supported_extensions,
            "total_documents": len(self.get_all_document_files())
        }
        
        # Add per-directory statistics
        dir_stats = {}
        for source_dir in self.source_dirs:
            files = []
            for ext in self.supported_extensions:
                pattern = f"{source_dir}/**/*{ext}"
                files.extend(glob.glob(pattern, recursive=True))
            dir_stats[str(source_dir)] = len(files)
        
        info["documents_per_directory"] = dir_stats
        return info
