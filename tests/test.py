#!/usr/bin/env python3
"""
Test client for the Local Documentation MCP Server.

This script connects to the MCP server and tests the available tools.
"""

import asyncio
import json
from mcp.client import Client

async def main():
    # Connect to the MCP server
    async with Client("http://127.0.0.1:8000/mcp") as client:
        print("Connected to MCP server")

        # List available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools: {json.dumps(tools, indent=2)}")

        # Test list_local_docs
        print("\n--- Testing list_local_docs ---")
        result = await client.call_tool("list_local_docs")
        print(f"Available docs: {json.dumps(result.content, indent=2)}")

        # Test search_local_docs
        print("\n--- Testing search_local_docs ---")
        result = await client.call_tool("search_local_docs", {"query": "api"})
        print(f"Search results: {json.dumps(result.content, indent=2)}")

        # Test semantic_search
        print("\n--- Testing semantic_search ---")
        result = await client.call_tool("semantic_search", {"query": "How to handle errors", "max_results": 3})
        print(f"Semantic search results: {json.dumps(result.content, indent=2)}")

        # Test get_local_doc
        print("\n--- Testing get_local_doc ---")
        result = await client.call_tool("get_local_doc", {"file_path": "getting-started.md"})
        print(f"Document content (truncated): {result.content.get('content', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())