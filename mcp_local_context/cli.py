#!/usr/bin/env python3
"""
MCP Local Context CLI

This module provides a command-line interface for the MCP Local Context Server.
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
        help="Install the server in Claude Desktop"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run the server in development mode with the MCP Inspector"
    )
    return parser.parse_args()

def find_mcp_command():
    """Find the mcp command."""
    # Try to find the mcp command in the PATH
    try:
        mcp_path = subprocess.check_output(["which", "mcp"]).decode().strip()
        return mcp_path
    except subprocess.CalledProcessError:
        # Try to find the mcp command in common locations
        common_locations = [
            os.path.expanduser("~/.local/bin/mcp"),
            "/usr/local/bin/mcp",
            "/usr/bin/mcp",
        ]
        for location in common_locations:
            if os.path.isfile(location):
                return location
        
        # If we can't find the mcp command, return None
        return None

def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Set default sources if none provided
    if not args.sources:
        args.sources = ["sources"]

    # Set environment variables for the sources
    os.environ["SOURCE_DIRS"] = ",".join(args.sources)
    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)
    os.environ["MCP_PATH"] = args.path

    if args.install or args.dev:
        # Find the mcp command
        mcp_cmd = find_mcp_command()
        if not mcp_cmd:
            print("Error: Could not find the mcp command. Please install the MCP Python SDK.")
            print("You can install it with: pip install 'mcp[cli]'")
            sys.exit(1)
        
        # Get the path to the server module
        server_module = "mcp_local_context.server"
        
        if args.install:
            # Install the server in Claude Desktop
            cmd = [mcp_cmd, "install", "-m", server_module, "--name", "Local Context MCP"]
            
            # Add environment variables
            cmd.extend(["-v", f"SOURCE_DIRS={','.join(args.sources)}"])
            cmd.extend(["-v", f"MCP_HOST={args.host}"])
            cmd.extend(["-v", f"MCP_PORT={args.port}"])
            cmd.extend(["-v", f"MCP_PATH={args.path}"])
        else:
            # Run the server in development mode with the MCP Inspector
            cmd = [mcp_cmd, "dev", "-m", server_module]
    else:
        # Import the server module and run it directly
        from mcp_local_context.server import main as server_main
        
        # Run the server
        return server_main()
    
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
