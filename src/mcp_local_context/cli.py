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
from typing import Optional

from .core.factory import create_full_server, create_simple_server, create_server_from_env


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Local Context - Simple command to install and use the MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default 'sources' directory
  %(prog)s docs api-docs specs      # Run with multiple source directories
  %(prog)s --host 0.0.0.0 --port 9000  # Run with custom host and port
  %(prog)s --dev                    # Run in development mode with MCP Inspector
  %(prog)s --install                # Install the server in Claude Desktop
  %(prog)s --simple                 # Run without RAG capabilities
        """
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
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Run without RAG capabilities (no vlite dependency)"
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Use environment variables for configuration"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show server capabilities and configuration"
    )
    return parser.parse_args()


def find_mcp_command() -> Optional[str]:
    """Find the mcp command."""
    # Try to find the mcp command in the PATH
    try:
        mcp_path = subprocess.check_output(["which", "mcp"], stderr=subprocess.DEVNULL).decode().strip()
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


def show_server_info(server):
    """Show server capabilities and configuration."""
    capabilities = server.get_capabilities()
    
    print("MCP Local Context Server Information")
    print("=" * 40)
    print(f"RAG Enabled: {'Yes' if capabilities['rag_enabled'] else 'No'}")
    print(f"VLite Available: {'Yes' if capabilities['vlite_available'] else 'No'}")
    print(f"Source Directories: {', '.join(capabilities['source_directories'])}")
    print(f"Supported File Types: {', '.join(capabilities['supported_file_types'])}")
    
    if capabilities['document_types']:
        print(f"Document Types: {', '.join(capabilities['document_types'])}")
    
    print(f"Available Tools: {', '.join(capabilities['tools'])}")
    print()


def run_with_mcp_command(args, server_module: str):
    """Run the server using the mcp command."""
    # Find the mcp command
    mcp_cmd = find_mcp_command()
    if not mcp_cmd:
        print("Error: Could not find the mcp command. Please install the MCP Python SDK.")
        print("You can install it with: pip install 'mcp[cli]'")
        sys.exit(1)
    
    if args.install:
        # Install the server in Claude Desktop
        cmd = [mcp_cmd, "install", "-m", server_module, "--name", "Local Context MCP"]
        
        # Add environment variables
        cmd.extend(["-v", f"SOURCE_DIRS={','.join(args.sources)}"])
        cmd.extend(["-v", f"MCP_HOST={args.host}"])
        cmd.extend(["-v", f"MCP_PORT={args.port}"])
        cmd.extend(["-v", f"MCP_PATH={args.path}"])
        
        if args.simple:
            cmd.extend(["-v", "ENABLE_RAG=false"])
    else:
        # Run the server in development mode with the MCP Inspector
        cmd = [mcp_cmd, "dev", "-m", server_module]
    
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
    
    if args.simple:
        os.environ["ENABLE_RAG"] = "false"

    # Handle special modes that require the mcp command
    if args.install or args.dev:
        server_module = "mcp_local_context.core.server"
        run_with_mcp_command(args, server_module)
        return

    # Create server instance based on configuration
    if args.env:
        server = create_server_from_env()
    elif args.simple:
        server = create_simple_server(
            source_dirs=args.sources,
            host=args.host,
            port=args.port,
            path=args.path
        )
    else:
        server = create_full_server(
            source_dirs=args.sources,
            host=args.host,
            port=args.port,
            path=args.path
        )

    # Show server info if requested
    if args.info:
        show_server_info(server)
        return

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
