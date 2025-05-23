#!/bin/bash

# Script to publish the package to PyPI

# Clean up previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m pip install --upgrade build
python -m build

# Upload to PyPI
python -m pip install --upgrade twine
python -m twine upload dist/*
