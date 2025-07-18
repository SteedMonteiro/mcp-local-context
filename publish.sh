#!/bin/bash

# Script to publish the package to PyPI with version bumping
set -e  # Exit on error

# Default to patch if no argument is provided
BUMP_TYPE=${1:-patch}

# Validate bump type
if [[ "$BUMP_TYPE" != "major" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "patch" ]]; then
    echo "Invalid bump type. Use 'major', 'minor', or 'patch'."
    exit 1
fi

# Bump version
echo "Bumping version ($BUMP_TYPE)..."
python bump_version.py $BUMP_TYPE

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
else
    echo "Publishing cancelled. You can publish manually with:"
    echo "python -m twine upload dist/*"
fi
