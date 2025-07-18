"""
Document Classifier Module

This module handles document type classification based on file paths and content.
"""

import re
from typing import Optional, Literal, Dict, List
from pathlib import Path

# Document types
DocumentType = Literal["documentation", "guide", "convention"]


class DocumentClassifier:
    """
    Classifies documents into types based on file paths and content analysis.
    
    This class implements rules for determining whether a document is
    documentation, a guide, or a convention based on various indicators.
    """

    def __init__(self):
        """Initialize the document classifier with default rules."""
        # Path-based classification rules
        self.path_rules = {
            "guide": ["guide", "tutorial", "how-to", "howto", "getting-started", "quickstart"],
            "convention": ["convention", "standard", "rule", "policy", "guideline", "best-practice"]
        }
        
        # Content-based classification rules
        self.content_rules = {
            "guide": [
                "how to", "step by step", "tutorial", "getting started", "quick start",
                "walkthrough", "guide", "instructions", "follow these steps"
            ],
            "convention": [
                "convention", "standard", "rule", "policy", "guideline", "best practice",
                "coding standard", "style guide", "must", "should", "shall", "requirement"
            ]
        }

    def classify_by_path(self, file_path: str) -> Optional[DocumentType]:
        """
        Classify a document based on its file path.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document type if classification is confident, None otherwise
        """
        path_lower = file_path.lower()
        
        # Check for guide indicators
        for indicator in self.path_rules["guide"]:
            if indicator in path_lower:
                return "guide"
        
        # Check for convention indicators
        for indicator in self.path_rules["convention"]:
            if indicator in path_lower:
                return "convention"
        
        return None

    def classify_by_content(self, content: str, max_lines: int = 20) -> Optional[DocumentType]:
        """
        Classify a document based on its content.
        
        Args:
            content: Document content to analyze
            max_lines: Maximum number of lines to analyze from the beginning
            
        Returns:
            Document type if classification is confident, None otherwise
        """
        if not content:
            return None
        
        # Analyze the first few lines for classification hints
        lines = content.split('\n')[:max_lines]
        text_to_analyze = '\n'.join(lines).lower()
        
        # Count indicators for each type
        guide_score = 0
        convention_score = 0
        
        for indicator in self.content_rules["guide"]:
            guide_score += text_to_analyze.count(indicator)
        
        for indicator in self.content_rules["convention"]:
            convention_score += text_to_analyze.count(indicator)
        
        # Determine classification based on scores
        if guide_score > convention_score and guide_score > 0:
            return "guide"
        elif convention_score > guide_score and convention_score > 0:
            return "convention"
        
        return None

    def classify_document(self, file_path: str, content: Optional[str] = None) -> DocumentType:
        """
        Classify a document using both path and content analysis.
        
        Args:
            file_path: Path to the document file
            content: Optional content of the file to analyze
            
        Returns:
            Document type: "documentation", "guide", or "convention"
        """
        # First try path-based classification
        path_classification = self.classify_by_path(file_path)
        if path_classification:
            return path_classification
        
        # If path classification is inconclusive, try content-based classification
        if content:
            content_classification = self.classify_by_content(content)
            if content_classification:
                return content_classification
        
        # Default to documentation if no other classification is found
        return "documentation"

    def classify_documents_batch(self, documents: List[Dict[str, str]]) -> Dict[str, DocumentType]:
        """
        Classify multiple documents in batch.
        
        Args:
            documents: List of dictionaries with 'file_path' and optional 'content' keys
            
        Returns:
            Dictionary mapping file paths to document types
        """
        classifications = {}
        for doc in documents:
            file_path = doc["file_path"]
            content = doc.get("content")
            classifications[file_path] = self.classify_document(file_path, content)
        
        return classifications

    def get_classification_stats(self, classifications: Dict[str, DocumentType]) -> Dict[str, int]:
        """
        Get statistics about document classifications.
        
        Args:
            classifications: Dictionary mapping file paths to document types
            
        Returns:
            Dictionary with counts for each document type
        """
        stats = {"documentation": 0, "guide": 0, "convention": 0}
        for doc_type in classifications.values():
            stats[doc_type] += 1
        return stats

    def filter_by_type(self, documents: List[str], doc_type: DocumentType, 
                      content_getter: Optional[callable] = None) -> List[str]:
        """
        Filter documents by type.
        
        Args:
            documents: List of document file paths
            doc_type: Document type to filter for
            content_getter: Optional function to get content for a file path
            
        Returns:
            List of documents matching the specified type
        """
        filtered_docs = []
        
        for doc_path in documents:
            content = None
            if content_getter:
                try:
                    content = content_getter(doc_path)
                except Exception:
                    pass  # Continue without content if getter fails
            
            if self.classify_document(doc_path, content) == doc_type:
                filtered_docs.append(doc_path)
        
        return filtered_docs

    def add_path_rule(self, doc_type: DocumentType, indicators: List[str]):
        """
        Add custom path-based classification rules.
        
        Args:
            doc_type: Document type to add rules for
            indicators: List of path indicators for this type
        """
        if doc_type in self.path_rules:
            self.path_rules[doc_type].extend(indicators)
        else:
            self.path_rules[doc_type] = indicators

    def add_content_rule(self, doc_type: DocumentType, indicators: List[str]):
        """
        Add custom content-based classification rules.
        
        Args:
            doc_type: Document type to add rules for
            indicators: List of content indicators for this type
        """
        if doc_type in self.content_rules:
            self.content_rules[doc_type].extend(indicators)
        else:
            self.content_rules[doc_type] = indicators

    def get_rules_info(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get information about current classification rules.
        
        Returns:
            Dictionary containing path and content rules for each document type
        """
        return {
            "path_rules": self.path_rules.copy(),
            "content_rules": self.content_rules.copy()
        }
