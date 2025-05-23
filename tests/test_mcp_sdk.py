#!/usr/bin/env python3
"""
Test client for the Local Documentation MCP Server using the MCP Python SDK.

This script connects to the MCP server and tests the available tools.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the docs_server module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP client
from mcp.client import Client

async def main():
    """Test the MCP server using the MCP Python SDK."""
    print("Connecting to MCP server...")
    
    # Connect to the MCP server
    async with Client("http://127.0.0.1:8000/mcp") as client:
        print("Connected to MCP server")
        
        # Get server info
        server_info = await client.get_server_info()
        print(f"\nServer info: {json.dumps(server_info, indent=2)}")
        
        # List available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test list_local_docs
        print("\n--- Testing list_local_docs ---")
        result = await client.call_tool("list_local_docs")
        print(f"Found {len(result.content)} documents")
        
        # Test list_docs_by_type for each type
        for doc_type in ["documentation", "guide", "convention"]:
            print(f"\n--- Testing list_docs_by_type ({doc_type}) ---")
            result = await client.call_tool("list_docs_by_type", {"doc_type": doc_type})
            print(f"{doc_type.capitalize()} files: {len(result.content)}")
        
        # Test search_local_docs
        print("\n--- Testing search_local_docs ---")
        result = await client.call_tool("search_local_docs", {"query": "api"})
        print(f"Search results for 'api': {len(result.content)}")
        
        # Test semantic_search
        print("\n--- Testing semantic_search ---")
        result = await client.call_tool(
            "semantic_search", 
            {"query": "How to handle errors", "max_results": 3}
        )
        print(f"Semantic search results: {len(result.content)}")
        for i, doc in enumerate(result.content):
            print(f"  {i+1}. {doc.get('file_path')} ({doc.get('doc_type')})")
            print(f"     Score: {doc.get('score')}")
            print(f"     Excerpt: {doc.get('content')[:100]}...")
        
        # Test build_docs_index
        print("\n--- Testing build_docs_index ---")
        try:
            result = await client.call_tool("build_docs_index")
            print(f"Index build result: {result.content}")
        except Exception as e:
            print(f"Error building index: {e}")

if __name__ == "__main__":
    asyncio.run(main())
