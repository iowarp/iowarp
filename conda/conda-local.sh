#!/bin/bash

# Script to build and install the iowarp-core conda package locally

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RECIPE_DIR="$SCRIPT_DIR"

echo "Building iowarp-core conda package from: $RECIPE_DIR"

# Build the package with conda-forge channel
conda build "$RECIPE_DIR" -c conda-forge

# Get the output package path
PACKAGE_PATH=$(conda build "$RECIPE_DIR" --output)

echo ""
echo "Package built successfully: $PACKAGE_PATH"
echo ""
echo "To install the package locally, run:"
echo "  conda install --use-local iowarp-core"
echo ""
echo "Or install directly:"
echo "  conda install $PACKAGE_PATH"
