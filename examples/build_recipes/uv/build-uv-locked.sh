#!/bin/bash

# Generate lock file for reproducible builds
uv lock

# Install exact versions from lock file
uv sync --frozen

# Export to requirements.txt for Lambda
uv export --format requirements-txt --no-hashes > requirements.txt

# Create build directory
mkdir -p build/

# Install to build directory
uv pip install -r requirements.txt --target build/

# Copy application code
cp app_uv.py build/

# Create deployment package
cd build && zip -r ../lambda-uv-locked.zip . && cd ..

# Cleanup
rm requirements.txt

echo "✅ uv locked deployment package created: lambda-uv-locked.zip"
