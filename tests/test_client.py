#!/usr/bin/env python3
"""
Test client for the Local Documentation MCP Server.

This script connects to the MCP server and tests the available tools.
"""

import asyncio
import json
from mcp.client import Client

async def main():
    """Test the MCP server."""
    print("Connecting to MCP server...")
    async with Client("http://127.0.0.1:8000/mcp") as client:
        # Test list_local_docs
        print("\n--- Testing list_local_docs ---")
        result = await client.call_tool("list_local_docs", {})
        print(f"Found documents: {result}")

        # Test list_docs_by_type for each type
        print("\n--- Testing list_docs_by_type (documentation) ---")
        result = await client.call_tool("list_docs_by_type", {"doc_type": "documentation"})
        print(f"Documentation files: {result}")

        print("\n--- Testing list_docs_by_type (guide) ---")
        result = await client.call_tool("list_docs_by_type", {"doc_type": "guide"})
        print(f"Guide files: {result}")

        print("\n--- Testing list_docs_by_type (convention) ---")
        result = await client.call_tool("list_docs_by_type", {"doc_type": "convention"})
        print(f"Convention files: {result}")

        # Test search_local_docs with doc_type
        print("\n--- Testing search_local_docs with doc_type ---")
        result = await client.call_tool("search_local_docs", {"query": "getting", "doc_type": "guide"})
        print(f"Search results for 'getting' in guides: {result}")

        # Test semantic_search with doc_type
        print("\n--- Testing semantic_search with doc_type ---")
        result = await client.call_tool("semantic_search", {"query": "How to get started", "max_results": 3, "doc_type": "guide"})
        print(f"Semantic search results: {result}")

        # Test get_local_doc
        print("\n--- Testing get_local_doc ---")
        result = await client.call_tool("get_local_doc", {"file_path": "guides/getting-started-guide.md"})
        print(f"Document result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
