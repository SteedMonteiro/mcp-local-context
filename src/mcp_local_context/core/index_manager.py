"""
Index Manager Module

This module manages the document indexing process for semantic search.
"""

from typing import Dict, Any, List, Optional, Callable
from .document_handler import DocumentHandler
from .document_classifier import DocumentClassifier, DocumentType
from .search_engine import SemanticSearchEngine


class IndexingProgress:
    """Tracks indexing progress and provides callbacks."""
    
    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.error_files = 0
        self.doc_type_counts = {"documentation": 0, "guide": 0, "convention": 0}
        self.callbacks = []

    def add_callback(self, callback: Callable[[str], None]):
        """Add a progress callback function."""
        self.callbacks.append(callback)

    def update(self, file_path: str, doc_type: DocumentType, success: bool = True):
        """Update progress with a processed file."""
        if success:
            self.processed_files += 1
            self.doc_type_counts[doc_type] += 1
        else:
            self.error_files += 1
        
        # Call progress callbacks
        for callback in self.callbacks:
            try:
                callback(f"Processed: {file_path} (Type: {doc_type})")
            except Exception:
                pass  # Don't let callback errors stop indexing

    def get_summary(self) -> str:
        """Get a summary of the indexing progress."""
        summary = f"Successfully indexed {self.processed_files} files"
        if self.error_files > 0:
            summary += f" ({self.error_files} errors)"
        summary += ":\n"
        
        for doc_type, count in self.doc_type_counts.items():
            summary += f"- {doc_type.title()}: {count}\n"
        
        return summary.rstrip()


class IndexManager:
    """
    Manages document indexing for semantic search.
    
    This class coordinates between document handling, classification,
    and search engine indexing to build and maintain the search index.
    """

    def __init__(self, document_handler: DocumentHandler, 
                 document_classifier: DocumentClassifier,
                 search_engine: SemanticSearchEngine):
        """
        Initialize the index manager.
        
        Args:
            document_handler: Document handler instance
            document_classifier: Document classifier instance
            search_engine: Semantic search engine instance
        """
        self.document_handler = document_handler
        self.document_classifier = document_classifier
        self.search_engine = search_engine

    def is_available(self) -> bool:
        """Check if indexing is available (requires semantic search)."""
        return self.search_engine.is_available()

    def build_index(self, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Build the complete document index.
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Summary string of the indexing process
        """
        if not self.is_available():
            return "Indexing is not available. Semantic search is disabled or vlite is not installed."

        # Initialize progress tracking
        progress = IndexingProgress()
        if progress_callback:
            progress.add_callback(progress_callback)

        # Clear existing index
        self.search_engine.clear_index()

        # Get all document files
        all_files = self.document_handler.get_all_document_files()
        if not all_files:
            return "No document files found in any of the source directories."

        progress.total_files = len(all_files)

        # Process each file
        for file_path in all_files:
            try:
                # Read file content
                content = self.document_handler.get_file_content(file_path)
                relative_path = self.document_handler.get_relative_path(file_path)

                # Classify document
                doc_type = self.document_classifier.classify_document(file_path, content)

                # Add to search index
                self.search_engine.add_document(content, {
                    "file_path": relative_path,
                    "doc_type": doc_type
                })

                # Update progress
                progress.update(relative_path, doc_type, success=True)

            except Exception as e:
                # Update progress with error
                progress.update(file_path, "documentation", success=False)
                if progress_callback:
                    progress_callback(f"Error indexing {file_path}: {str(e)}")

        return progress.get_summary()

    def rebuild_index(self, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Rebuild the entire document index.
        
        This is an alias for build_index() for backward compatibility.
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Summary string of the indexing process
        """
        return self.build_index(progress_callback)

    def add_document_to_index(self, file_path: str) -> bool:
        """
        Add a single document to the index.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            # Read file content
            content = self.document_handler.get_file_content(file_path)
            relative_path = self.document_handler.get_relative_path(file_path)

            # Classify document
            doc_type = self.document_classifier.classify_document(file_path, content)

            # Add to search index
            self.search_engine.add_document(content, {
                "file_path": relative_path,
                "doc_type": doc_type
            })

            return True
        except Exception:
            return False

    def remove_document_from_index(self, file_path: str) -> bool:
        """
        Remove a document from the index.
        
        Note: This is a placeholder as vlite doesn't support individual document removal.
        A full rebuild would be needed to actually remove documents.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            False (not implemented in vlite)
        """
        # vlite doesn't support removing individual documents
        # Would need to rebuild the entire index
        return False

    def update_document_in_index(self, file_path: str) -> bool:
        """
        Update a document in the index.
        
        This removes the old version and adds the new version.
        Since vlite doesn't support individual removal, this just adds the document again.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        # For now, just add the document (vlite will handle duplicates)
        return self.add_document_to_index(file_path)

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current index.
        
        Returns:
            Dictionary containing index statistics
        """
        stats = {
            "available": self.is_available(),
            "document_count": 0,
            "source_info": self.document_handler.get_source_info()
        }

        if self.is_available():
            stats["document_count"] = self.search_engine.get_document_count()

        return stats

    def validate_index(self) -> Dict[str, Any]:
        """
        Validate the current index against the file system.
        
        Returns:
            Dictionary containing validation results
        """
        validation = {
            "index_available": self.is_available(),
            "files_on_disk": len(self.document_handler.get_all_document_files()),
            "documents_in_index": 0,
            "needs_rebuild": False
        }

        if self.is_available():
            validation["documents_in_index"] = self.search_engine.get_document_count()
            
            # Simple check: if file count doesn't match, suggest rebuild
            if validation["files_on_disk"] != validation["documents_in_index"]:
                validation["needs_rebuild"] = True

        return validation

    def get_classification_preview(self, max_files: int = 10) -> List[Dict[str, str]]:
        """
        Get a preview of how documents would be classified.
        
        Args:
            max_files: Maximum number of files to preview
            
        Returns:
            List of dictionaries with file_path and predicted doc_type
        """
        all_files = self.document_handler.get_all_document_files()[:max_files]
        preview = []

        for file_path in all_files:
            relative_path = self.document_handler.get_relative_path(file_path)
            
            # Try classification without content first (faster)
            doc_type = self.document_classifier.classify_by_path(file_path)
            if not doc_type:
                # If path classification fails, try with content
                content = self.document_handler.get_file_content(file_path)
                doc_type = self.document_classifier.classify_document(file_path, content)

            preview.append({
                "file_path": relative_path,
                "doc_type": doc_type
            })

        return preview
