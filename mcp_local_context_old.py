#!/usr/bin/env python3
"""
MCP Local Context - Simple command to install and use the MCP server

This script provides a simple command to install and use the MCP server
for Cursor and Cline that can take a list of folders as sources.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Local Context - Simple command to install and use the MCP server"
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
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the MCP server in Claude Desktop"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run the server in development mode with the MCP Inspector"
    )
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()

    # Set default sources if none provided
    if not args.sources:
        args.sources = ["sources"]

    # Get the path to the docs_server.py script
    script_dir = Path(__file__).parent.absolute()
    docs_server_path = script_dir / "docs_server.py"

    # Check if the docs_server.py script exists
    if not docs_server_path.exists():
        print(f"Error: Could not find docs_server.py in {script_dir}")
        sys.exit(1)

    # Set environment variables for the sources
    os.environ["SOURCE_DIRS"] = ",".join(args.sources)
    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)
    os.environ["MCP_PATH"] = args.path

    # Build the command
    if args.install:
        # Install the server in Claude Desktop
        cmd = ["mcp", "install", str(docs_server_path)]
        cmd.extend(["--name", "Local Context MCP"])
        
        # Add environment variables
        for source in args.sources:
            cmd.extend(["-v", f"SOURCE_DIRS={','.join(args.sources)}"])
        
        cmd.extend(["-v", f"MCP_HOST={args.host}"])
        cmd.extend(["-v", f"MCP_PORT={args.port}"])
        cmd.extend(["-v", f"MCP_PATH={args.path}"])
    elif args.dev:
        # Run the server in development mode with the MCP Inspector
        cmd = ["mcp", "dev", str(docs_server_path)]
    else:
        # Run the server directly
        cmd = ["python", str(docs_server_path)]
        
        # Add sources
        cmd.append("--sources")
        cmd.extend(args.sources)
        
        # Add host, port, and path
        cmd.extend(["--host", args.host])
        cmd.extend(["--port", str(args.port)])
        cmd.extend(["--path", args.path])

    # Print the command
    print(f"Running: {' '.join(cmd)}")

    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
