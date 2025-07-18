#!/usr/bin/env python3
"""
Version bumping script for mcp-local-context.

This script automatically increments the version number in all relevant files:
- pyproject.toml
- setup.py
- mcp_local_context/__init__.py

Usage:
    python bump_version.py [major|minor|patch]

Examples:
    python bump_version.py  # Defaults to patch increment
    python bump_version.py patch  # Increments patch version (0.1.2 -> 0.1.3)
    python bump_version.py minor  # Increments minor version (0.1.2 -> 0.2.0)
    python bump_version.py major  # Increments major version (0.1.2 -> 1.0.0)
"""

import re
import sys
import os
from pathlib import Path


def get_current_version():
    """Extract the current version from pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    
    return match.group(1)


def bump_version(current_version, bump_type="patch"):
    """Bump the version according to semantic versioning."""
    major, minor, patch = map(int, current_version.split("."))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_file(file_path, pattern, new_version):
    """Update version in a file."""
    with open(file_path, "r") as f:
        content = f.read()
    
    new_content = re.sub(pattern, lambda m: m.group(1) + new_version + m.group(3), content)
    
    with open(file_path, "w") as f:
        f.write(new_content)


def main():
    # Determine bump type
    bump_type = "patch"  # Default
    if len(sys.argv) > 1 and sys.argv[1] in ["major", "minor", "patch"]:
        bump_type = sys.argv[1]
    
    # Get current version
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    print(f"Bumping version: {current_version} -> {new_version} ({bump_type})")
    
    # Update pyproject.toml
    update_file(
        "pyproject.toml",
        r'(version\s*=\s*")([^"]+)(")',
        new_version
    )
    
    # Update setup.py
    update_file(
        "setup.py",
        r'(version=")([^"]+)(")',
        new_version
    )
    
    # Update __init__.py
    update_file(
        "mcp_local_context/__init__.py",
        r'(__version__\s*=\s*")([^"]+)(")',
        new_version
    )
    
    print(f"Version updated to {new_version} in all files.")
    print("You can now build and publish your package.")


if __name__ == "__main__":
    main()
