#!/bin/bash

# Script to publish the package to PyPI with version bumping
set -e  # Exit on error

# Check if we're in a git repository and have a clean working directory
if [ -d ".git" ]; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "Warning: You have uncommitted changes in your git repository."
        echo "It's recommended to commit or stash your changes before publishing."
        read -p "Do you want to continue anyway? (y/n): " CONTINUE
        if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
            echo "Publishing cancelled."
            exit 1
        fi
    fi
fi

# Default to patch if no argument is provided
BUMP_TYPE=${1:-patch}

# Validate bump type
if [[ "$BUMP_TYPE" != "major" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "patch" ]]; then
    echo "Invalid bump type. Use 'major', 'minor', or 'patch'."
    exit 1
fi

# Get current version before bumping
CURRENT_VERSION=$(python -c "
import re
with open('pyproject.toml', 'r') as f:
    content = f.read()
match = re.search(r'version\s*=\s*\"([^\"]+)\"', content)
print(match.group(1) if match else 'unknown')
")

# Bump version
echo "Bumping version ($BUMP_TYPE)..."
python bump_version.py $BUMP_TYPE

# Get new version after bumping
NEW_VERSION=$(python -c "
import re
with open('pyproject.toml', 'r') as f:
    content = f.read()
match = re.search(r'version\s*=\s*\"([^\"]+)\"', content)
print(match.group(1) if match else 'unknown')
")

echo "Version bumped from $CURRENT_VERSION to $NEW_VERSION"

# Clean up previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "Building package..."
python -m pip install --upgrade build
python -m build

# Verify the package
echo "Verifying package with twine..."
python -m pip install --upgrade twine
python -m twine check dist/*

# Prompt for confirmation before publishing
echo ""
echo "Package is ready to be published to PyPI."
read -p "Do you want to publish now? (y/n): " CONFIRM

if [[ "$CONFIRM" == "y" || "$CONFIRM" == "Y" ]]; then
    echo "Publishing to PyPI..."
    python -m twine upload dist/*
    echo "Package published successfully!"

    # Commit version changes and create git tag
    echo ""
    echo "Creating git commit and tag..."
    git add pyproject.toml setup.py src/mcp_local_context/__init__.py
    git commit -m "Bump version to $NEW_VERSION"
    git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"

    echo "Git commit and tag created successfully!"
    echo "Don't forget to push your changes and tags:"
    echo "  git push origin main"
    echo "  git push origin v$NEW_VERSION"
else
    echo "Publishing cancelled. You can publish manually with:"
    echo "python -m twine upload dist/*"
    echo ""
    echo "Note: Version was already bumped to $NEW_VERSION"
    echo "You may want to commit these changes:"
    echo "  git add pyproject.toml setup.py src/mcp_local_context/__init__.py"
    echo "  git commit -m 'Bump version to $NEW_VERSION'"
fi
