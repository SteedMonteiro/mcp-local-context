#!/usr/bin/env python3
"""
Test runner for the Local Documentation MCP Server.

This script runs all the tests for the MCP server.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test runner for the Local Documentation MCP Server"
    )
    parser.add_argument(
        "--test",
        choices=["all", "doc_types", "client", "mcp_sdk"],
        default="all",
        help="Which test to run (default: all)"
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start the server before running tests"
    )
    return parser.parse_args()

def start_server():
    """Start the MCP server in the background."""
    print("Starting MCP server...")

    # Use the new CLI to start the server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "mcp_local_context.cli"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parent / "src")}
    )

    # Wait a bit for the server to start
    import time
    time.sleep(3)

    return server_process

def run_test(test_name):
    """Run a specific test."""
    print(f"Running test: {test_name}")
    
    # Get the path to the test script
    script_dir = Path(__file__).parent.absolute()
    test_path = script_dir / "tests" / f"test_{test_name}.py"
    
    # Run the test
    try:
        subprocess.run(
            [sys.executable, str(test_path)],
            check=True,
        )
        print(f"Test {test_name} completed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"Test {test_name} failed")
        return False

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Start the server if requested
    server_process = None
    if args.server:
        server_process = start_server()
    
    # Run the tests
    if args.test == "all":
        tests = ["doc_types", "client", "mcp_sdk"]
    else:
        tests = [args.test]
    
    # Run each test
    results = {}
    for test in tests:
        results[test] = run_test(test)
    
    # Print summary
    print("\nTest Summary:")
    for test, result in results.items():
        print(f"  {test}: {'PASSED' if result else 'FAILED'}")
    
    # Stop the server if we started it
    if server_process:
        print("Stopping MCP server...")
        server_process.terminate()
    
    # Return success if all tests passed
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
