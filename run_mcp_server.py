#!/usr/bin/env python3
"""
Simple script to run the MCP server directly.
"""

import os
import sys
import argparse
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the MCP server directly"
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help="List of source folders to index (default: sources)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run the server on (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="Path for the MCP endpoint (default: /mcp)"
    )
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()

    # Set default sources if none provided
    if not args.sources:
        args.sources = ["sources"]

    # Set environment variables for the sources
    os.environ["SOURCE_DIRS"] = ",".join(args.sources)
    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)
    os.environ["MCP_PATH"] = args.path

    # Import the docs_server module
    import docs_server

    # Run the server
    docs_server.main()

if __name__ == "__main__":
    main()
