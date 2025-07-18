#!/usr/bin/env python3
"""
MCP Local Context Server

This module provides a unified MCP server for local documentation with optional RAG capabilities.
It consolidates all server implementations into a single, well-structured class using modular components.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any

from mcp.server.fastmcp import FastMCP, Context

from .document_handler import DocumentHandler
from .document_classifier import DocumentClassifier, DocumentType
from .search_engine import SemanticSearchEngine, UnifiedSearchEngine
from .index_manager import IndexManager

# Try to import vlite for RAG functionality
try:
    from vlite import VLite
    HAS_VLITE = True
except (ImportError, Exception) as e:
    HAS_VLITE = False


class MCPLocalContextServer:
    """
    Unified MCP Local Context Server for serving local documentation.

    This server provides access to local documents with optional RAG capabilities.
    It supports document type classification and semantic search when vlite is available.
    """

    def __init__(
        self,
        source_dirs: Optional[List[str]] = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        path: str = "/mcp",
        enable_rag: bool = True,
        server_name: str = "Local Context MCP",
        instructions: str = "Retrieves development information with documentations, guides, and conventions"
    ):
        """
        Initialize the MCP Local Context Server.

        Args:
            source_dirs: List of source directories to serve documents from
            host: Host to run the server on
            port: Port to run the server on
            path: Path for the MCP endpoint
            enable_rag: Whether to enable RAG functionality (requires vlite)
            server_name: Name of the MCP server
            instructions: Instructions for the MCP server
        """
        # Set default source directories if none provided
        if source_dirs is None:
            source_dirs = ["sources"]

        # Convert to Path objects
        source_paths = [Path(source) for source in source_dirs]

        # Store configuration
        self.host = host
        self.port = port
        self.path = path
        self.enable_rag = enable_rag and HAS_VLITE

        # Initialize core components
        self.document_handler = DocumentHandler(source_paths)
        self.document_classifier = DocumentClassifier()
        self.semantic_engine = SemanticSearchEngine("local_docs") if self.enable_rag else None
        self.search_engine = UnifiedSearchEngine("local_docs")
        self.index_manager = IndexManager(
            self.document_handler,
            self.document_classifier,
            self.semantic_engine
        ) if self.semantic_engine else None

        # Initialize the MCP server
        self.mcp = FastMCP(
            name=server_name,
            instructions=instructions,
        )

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register tools with the MCP server."""
        # Always available tools
        self._register_basic_tools()
        
        # RAG-dependent tools (only if vlite is available)
        if self.enable_rag:
            self._register_rag_tools()

    def _register_basic_tools(self):
        """Register basic tools that don't require RAG."""
        @self.mcp.tool()
        def list_local_docs() -> List[str]:
            """
            Lists all available document files in all source directories.

            This tool provides a comprehensive list of all document files available
            in the configured source directories. Use this to discover what documents
            are available locally before requesting specific files.

            Returns:
                A list of file paths relative to their source directories.
            """
            return self.document_handler.list_documents()

        @self.mcp.tool()
        def get_local_doc(file_path: str) -> Dict[str, Any]:
            """
            Fetches the content of a specific document file from the source directories.

            This tool retrieves the full content of a document file specified by its path.
            The path should be in the format 'source_dir_name/path/to/file.md'.

            Args:
                file_path: Path to the document file (e.g., 'sources/app-studio/README.md').

            Returns:
                The content of the document file along with its document type (if RAG is enabled).
            """
            result = self.document_handler.get_document_content(file_path)

            # Add document type if RAG is enabled and no error occurred
            if self.enable_rag and "error" not in result:
                full_path = result.get("full_path")
                content = result.get("content")
                if full_path and content:
                    doc_type = self.document_classifier.classify_document(full_path, content)
                    result["doc_type"] = doc_type

            # Remove full_path from result (internal use only)
            result.pop("full_path", None)
            return result

        @self.mcp.tool()
        def search_local_docs(query: str, doc_type: Optional[DocumentType] = None) -> List[str]:
            """
            Searches for document files in the local sources directory that match a query.

            This tool helps you find specific document files based on a search query.
            The search is performed on file paths and matches any part of the path.
            You can optionally filter by document type (requires RAG).

            Args:
                query: Search query to find matching document files.
                doc_type: Optional document type to filter results (only works with RAG enabled).

            Returns:
                A list of file paths that match the query.
            """
            all_docs = self.document_handler.list_documents()

            # If doc_type filter is requested and RAG is enabled, filter by type first
            if doc_type and self.enable_rag:
                filtered_docs = self.document_classifier.filter_by_type(
                    all_docs,
                    doc_type,
                    content_getter=lambda path: self.document_handler.get_document_content(path).get("content", "")
                )
                return self.document_handler.search_documents_by_path(query, filtered_docs)
            else:
                return self.document_handler.search_documents_by_path(query, all_docs)

    def _register_rag_tools(self):
        """Register RAG-dependent tools."""
        @self.mcp.tool()
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
            all_docs = self.document_handler.list_documents()
            return self.document_classifier.filter_by_type(
                all_docs,
                doc_type,
                content_getter=lambda path: self.document_handler.get_document_content(path).get("content", "")
            )

        @self.mcp.tool()
        def semantic_search(
            query: str,
            max_results: int = 5,
            doc_type: Optional[DocumentType] = None
        ) -> List[Dict[str, Any]]:
            """
            Performs semantic search on documentation content using RAG.

            This tool searches for documentation based on the meaning of your query,
            not just keyword matching. It uses vector embeddings to find the most
            semantically similar documents and returns excerpts from them.

            Args:
                query: Search query to find semantically relevant documentation.
                max_results: Maximum number of results to return (default: 5).
                doc_type: Optional document type to filter results.

            Returns:
                A list of documents with their file paths, content excerpts,
                document type, and relevance scores.
            """
            if not self.semantic_engine or not self.semantic_engine.is_available():
                return [{"error": "Semantic search is not available. RAG is disabled or vlite is not installed."}]

            results = self.semantic_engine.search(query, max_results, doc_type)
            return [result.to_dict() for result in results]

        @self.mcp.tool()
        def build_docs_index(ctx: Context) -> str:
            """
            Builds or rebuilds the search index for local documents.

            This tool processes all document files and creates a search index for semantic search.
            Use this tool if you've added new document files or updated existing ones.

            The index is used by the 'semantic_search' tool to find relevant documents.
            Documents are categorized as documentation, guides, or conventions.
            """
            if not self.index_manager or not self.index_manager.is_available():
                return "Indexing is not available. RAG is disabled or vlite is not installed."

            def progress_callback(message: str):
                ctx.info(message)

            return self.index_manager.build_index(progress_callback)

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about server capabilities.

        Returns:
            Dictionary containing server capabilities and configuration.
        """
        capabilities = {
            "rag_enabled": self.enable_rag,
            "vlite_available": HAS_VLITE,
            "tools": self._get_available_tools()
        }

        # Add document handler info
        capabilities.update(self.document_handler.get_source_info())

        # Add search engine capabilities
        if self.search_engine:
            capabilities.update(self.search_engine.get_capabilities())

        # Add document types if RAG is enabled
        if self.enable_rag:
            capabilities["document_types"] = ["documentation", "guide", "convention"]

        # Add index stats if available
        if self.index_manager:
            capabilities["index_stats"] = self.index_manager.get_index_stats()

        return capabilities

    def _get_available_tools(self) -> List[str]:
        """Get list of available tools based on current configuration."""
        basic_tools = ["list_local_docs", "get_local_doc", "search_local_docs"]
        rag_tools = ["list_docs_by_type", "semantic_search", "build_docs_index"]
        
        if self.enable_rag:
            return basic_tools + rag_tools
        return basic_tools

    def run(self):
        """Run the MCP server."""
        self._ensure_source_directories()
        self._print_startup_info()

        # Try to build the index if RAG is enabled and index doesn't exist
        if self.enable_rag and self.index_manager and self.semantic_engine:
            if self.semantic_engine.get_document_count() == 0:
                self._build_initial_index()

        # Run the server with streamable-http transport
        self.mcp.run(transport="streamable-http", mount_path=self.path)

    def _ensure_source_directories(self):
        """Ensure all source directories exist."""
        self.document_handler.ensure_source_directories()

    def _print_startup_info(self):
        """Print server startup information."""
        print(f"Starting {self.mcp.name}...")

        source_info = self.document_handler.get_source_info()
        print(f"Serving documents from: {', '.join(source_info['source_directories'])}")
        print(f"Total documents: {source_info['total_documents']}")

        if self.enable_rag:
            print("RAG capabilities: ENABLED (semantic search, document classification)")
        else:
            if not HAS_VLITE:
                print("RAG capabilities: DISABLED (vlite not available)")
            else:
                print("RAG capabilities: DISABLED (by configuration)")

        print(f"Available tools: {', '.join(self._get_available_tools())}")

    def _build_initial_index(self):
        """Build the initial document index if RAG is enabled."""
        print("Building document index...")
        try:
            if not self.index_manager:
                print("Index manager not available.")
                return

            def progress_callback(message: str):
                print(message)

            summary = self.index_manager.build_index(progress_callback)
            print(summary)

        except Exception as e:
            print(f"Error building index: {str(e)}")
            print("You can build the index manually using the 'build_docs_index' tool.")




