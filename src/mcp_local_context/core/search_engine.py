"""
Search Engine Module

This module handles both path-based and semantic search functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from .document_classifier import DocumentType

# Try to import vlite for semantic search
try:
    from vlite import VLite
    HAS_VLITE = True
except (ImportError, Exception):
    HAS_VLITE = False


class SearchResult:
    """Represents a search result with metadata."""
    
    def __init__(self, file_path: str, content: str, doc_type: DocumentType, 
                 score: Optional[float] = None, excerpt_start: int = 0):
        self.file_path = file_path
        self.content = content
        self.doc_type = doc_type
        self.score = score
        self.excerpt_start = excerpt_start

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "file_path": self.file_path,
            "content": self.content,
            "doc_type": self.doc_type,
            "excerpt_start": self.excerpt_start
        }
        if self.score is not None:
            result["score"] = self.score
        return result


class PathSearchEngine:
    """
    Handles path-based document searching.
    
    This engine provides simple text-based searching within file paths
    and supports filtering by document type.
    """

    def __init__(self):
        """Initialize the path search engine."""
        pass

    def search(self, query: str, documents: List[str], 
               case_sensitive: bool = False) -> List[str]:
        """
        Search for documents by path/filename.
        
        Args:
            query: Search query to match against file paths
            documents: List of document paths to search within
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of matching document paths
        """
        if not case_sensitive:
            query = query.lower()
            matching_docs = [doc for doc in documents 
                           if query in doc.lower()]
        else:
            matching_docs = [doc for doc in documents 
                           if query in doc]
        
        return matching_docs

    def search_with_ranking(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Search with simple ranking based on match position and frequency.
        
        Args:
            query: Search query
            documents: List of document paths to search within
            
        Returns:
            List of tuples (document_path, score) sorted by relevance
        """
        results = []
        query_lower = query.lower()
        
        for doc in documents:
            doc_lower = doc.lower()
            if query_lower in doc_lower:
                # Calculate simple score based on:
                # 1. Position of match (earlier is better)
                # 2. Number of matches
                # 3. Length of document path (shorter is better)
                
                first_match_pos = doc_lower.find(query_lower)
                match_count = doc_lower.count(query_lower)
                doc_length = len(doc)
                
                # Score calculation (higher is better)
                position_score = 1.0 / (first_match_pos + 1)
                frequency_score = match_count
                length_score = 1.0 / (doc_length + 1)
                
                total_score = position_score + frequency_score + length_score
                results.append((doc, total_score))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results


class SemanticSearchEngine:
    """
    Handles semantic search using vector embeddings.
    
    This engine provides RAG-based semantic search capabilities
    when vlite is available.
    """

    def __init__(self, collection_name: str = "local_docs"):
        """
        Initialize the semantic search engine.
        
        Args:
            collection_name: Name of the vector database collection
        """
        self.collection_name = collection_name
        self.vlite_db = None
        self.enabled = HAS_VLITE
        
        if self.enabled:
            self.vlite_db = VLite(collection=collection_name)

    def is_available(self) -> bool:
        """Check if semantic search is available."""
        return self.enabled and self.vlite_db is not None

    def add_document(self, content: str, metadata: Dict[str, Any]):
        """
        Add a document to the search index.
        
        Args:
            content: Document content
            metadata: Document metadata (file_path, doc_type, etc.)
        """
        if not self.is_available():
            raise RuntimeError("Semantic search is not available")
        
        self.vlite_db.add(data=content, metadata=metadata)

    def search(self, query: str, max_results: int = 5, 
               doc_type: Optional[DocumentType] = None) -> List[SearchResult]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            doc_type: Optional document type filter
            
        Returns:
            List of SearchResult objects
        """
        if not self.is_available():
            return []

        try:
            # Retrieve similar documents from vlite
            results = self.vlite_db.retrieve(
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

                # Create a search result
                result = SearchResult(
                    file_path=file_path,
                    content=excerpt,
                    doc_type=doc_type_value,
                    score=score
                )
                formatted_results.append(result)

                # Limit results to max_results
                if len(formatted_results) >= max_results:
                    break

            return formatted_results
        except Exception as e:
            # Return error as a special result
            error_result = SearchResult(
                file_path="error",
                content=f"Error performing semantic search: {str(e)}",
                doc_type="documentation"
            )
            return [error_result]

    def clear_index(self):
        """Clear the search index."""
        if self.is_available():
            self.vlite_db.clear()

    def get_document_count(self) -> int:
        """Get the number of documents in the index."""
        if self.is_available():
            return self.vlite_db.count()
        return 0

    def rebuild_index(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Rebuild the entire search index.
        
        Args:
            documents: List of documents with 'content', 'file_path', and 'doc_type'
            
        Returns:
            Statistics about the rebuild process
        """
        if not self.is_available():
            return {"error": "Semantic search is not available"}

        # Clear existing index
        self.clear_index()

        # Counters for document types
        doc_type_counts = {"documentation": 0, "guide": 0, "convention": 0}
        processed_count = 0
        error_count = 0

        # Add each document to the index
        for doc in documents:
            try:
                content = doc["content"]
                file_path = doc["file_path"]
                doc_type = doc["doc_type"]
                
                doc_type_counts[doc_type] += 1
                
                # Add to vlite with metadata
                self.add_document(content, {
                    "file_path": file_path,
                    "doc_type": doc_type
                })
                
                processed_count += 1
            except Exception:
                error_count += 1

        return {
            "processed": processed_count,
            "errors": error_count,
            "doc_type_counts": doc_type_counts
        }


class UnifiedSearchEngine:
    """
    Unified search engine that combines path-based and semantic search.
    
    This engine provides a single interface for both types of search
    and automatically falls back to path search when semantic search
    is not available.
    """

    def __init__(self, collection_name: str = "local_docs"):
        """Initialize the unified search engine."""
        self.path_engine = PathSearchEngine()
        self.semantic_engine = SemanticSearchEngine(collection_name)

    def search(self, query: str, documents: List[str], 
               max_results: int = 5, doc_type: Optional[DocumentType] = None,
               search_type: str = "auto") -> List[Dict[str, Any]]:
        """
        Perform unified search.
        
        Args:
            query: Search query
            documents: List of document paths for path search
            max_results: Maximum number of results
            doc_type: Optional document type filter
            search_type: "path", "semantic", or "auto"
            
        Returns:
            List of search results as dictionaries
        """
        if search_type == "semantic" or (search_type == "auto" and self.semantic_engine.is_available()):
            # Use semantic search
            results = self.semantic_engine.search(query, max_results, doc_type)
            return [result.to_dict() for result in results]
        else:
            # Use path search
            matching_docs = self.path_engine.search(query, documents)
            
            # Convert to unified format
            results = []
            for doc_path in matching_docs[:max_results]:
                results.append({
                    "file_path": doc_path,
                    "content": f"Path match for query: {query}",
                    "doc_type": "documentation",  # Default type for path search
                    "search_type": "path"
                })
            
            return results

    def is_semantic_available(self) -> bool:
        """Check if semantic search is available."""
        return self.semantic_engine.is_available()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get search engine capabilities."""
        return {
            "path_search": True,
            "semantic_search": self.semantic_engine.is_available(),
            "vlite_available": HAS_VLITE,
            "document_count": self.semantic_engine.get_document_count()
        }
