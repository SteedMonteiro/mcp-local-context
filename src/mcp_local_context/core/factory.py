"""
Factory functions for creating MCP Local Context Server instances.

This module provides convenient factory functions for creating server instances
with different configurations (full-featured, simple, etc.).
"""

from typing import List, Optional
from .server import MCPLocalContextServer


def create_full_server(
    source_dirs: Optional[List[str]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp"
) -> MCPLocalContextServer:
    """
    Create a full-featured MCP server with RAG capabilities.
    
    This server includes all available tools including semantic search,
    document type classification, and index building.
    
    Args:
        source_dirs: List of source directories to serve documents from
        host: Host to run the server on
        port: Port to run the server on
        path: Path for the MCP endpoint
        
    Returns:
        Configured MCPLocalContextServer instance
    """
    return MCPLocalContextServer(
        source_dirs=source_dirs,
        host=host,
        port=port,
        path=path,
        enable_rag=True,
        server_name="Local Documentation MCP Server",
        instructions="Retrieves development information with documentations, guides, and conventions"
    )


def create_simple_server(
    source_dirs: Optional[List[str]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp"
) -> MCPLocalContextServer:
    """
    Create a simple MCP server without RAG capabilities.
    
    This server provides basic document listing and retrieval functionality
    without requiring vlite or other external dependencies.
    
    Args:
        source_dirs: List of source directories to serve documents from
        host: Host to run the server on
        port: Port to run the server on
        path: Path for the MCP endpoint
        
    Returns:
        Configured MCPLocalContextServer instance
    """
    return MCPLocalContextServer(
        source_dirs=source_dirs,
        host=host,
        port=port,
        path=path,
        enable_rag=False,
        server_name="Simple Local Documentation MCP Server",
        instructions="Provides basic access to local documentation files"
    )


def create_server_from_env() -> MCPLocalContextServer:
    """
    Create a server instance using environment variables for configuration.
    
    Environment variables:
    - SOURCE_DIRS: Comma-separated list of source directories
    - MCP_HOST: Host to run the server on
    - MCP_PORT: Port to run the server on
    - MCP_PATH: Path for the MCP endpoint
    - ENABLE_RAG: Whether to enable RAG functionality (true/false)
    
    Returns:
        Configured MCPLocalContextServer instance
    """
    import os
    
    # Parse source directories
    source_dirs_str = os.environ.get("SOURCE_DIRS", "sources")
    if "," in source_dirs_str:
        source_dirs = [d.strip() for d in source_dirs_str.split(",")]
    else:
        source_dirs = [source_dirs_str]
    
    # Parse other configuration
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    path = os.environ.get("MCP_PATH", "/mcp")
    enable_rag = os.environ.get("ENABLE_RAG", "true").lower() in ("true", "1", "yes", "on")
    
    return MCPLocalContextServer(
        source_dirs=source_dirs,
        host=host,
        port=port,
        path=path,
        enable_rag=enable_rag,
        server_name="Local Context MCP Server",
        instructions="Retrieves development information with documentations, guides, and conventions"
    )
