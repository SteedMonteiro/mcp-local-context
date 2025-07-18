#!/usr/bin/env python3
"""
MCP Local Context Server - Main Entry Point

This module provides the main entry point for the MCP Local Context Server.
It maintains backward compatibility with the old server interface while using
the new unified server implementation.
"""

import os
import sys
import argparse
from typing import List, Optional

from .core.factory import create_server_from_env, create_full_server


def parse_args():
    """Parse command-line arguments."""
    # Get default values from environment variables if available
    default_sources = os.environ.get("SOURCE_DIRS", "sources")
    if "," in default_sources:
        default_sources = default_sources.split(",")
    else:
        default_sources = [default_sources]

    default_host = os.environ.get("MCP_HOST", "127.0.0.1")
    default_port = int(os.environ.get("MCP_PORT", "8000"))
    default_path = os.environ.get("MCP_PATH", "/mcp")

    parser = argparse.ArgumentParser(description="MCP Local Context Server")
    parser.add_argument(
        "sources",
        nargs="*",
        help=f"List of source folders to index (default: {default_sources})"
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Host to run the server on (default: {default_host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to run the server on (default: {default_port})"
    )
    parser.add_argument(
        "--path",
        default=default_path,
        help=f"Path for the MCP endpoint (default: {default_path})"
    )
    return parser.parse_args()


def main():
    """Main entry point for the MCP Local Context Server."""
    # Check if we should use environment-based configuration
    if os.environ.get("USE_ENV_CONFIG", "").lower() in ("true", "1", "yes"):
        server = create_server_from_env()
    else:
        # Parse command-line arguments
        args = parse_args()

        # Set default sources if none provided
        if not args.sources:
            args.sources = ["sources"]

        # Create server with parsed arguments
        server = create_full_server(
            source_dirs=args.sources,
            host=args.host,
            port=args.port,
            path=args.path
        )

    # Run the server
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
