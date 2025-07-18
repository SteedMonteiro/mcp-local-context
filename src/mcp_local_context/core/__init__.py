"""
Core functionality for MCP Local Context Server.

This module contains the main server implementation and core business logic
separated into focused, modular components.
"""

from .server import MCPLocalContextServer
from .document_handler import DocumentHandler
from .document_classifier import DocumentClassifier, DocumentType
from .search_engine import SemanticSearchEngine, UnifiedSearchEngine, PathSearchEngine
from .index_manager import IndexManager
from .factory import create_full_server, create_simple_server, create_server_from_env

__all__ = [
    "MCPLocalContextServer",
    "DocumentHandler",
    "DocumentClassifier",
    "DocumentType",
    "SemanticSearchEngine",
    "UnifiedSearchEngine",
    "PathSearchEngine",
    "IndexManager",
    "create_full_server",
    "create_simple_server",
    "create_server_from_env"
]
