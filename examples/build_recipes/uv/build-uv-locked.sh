#!/bin/bash

# Generate lock file for reproducible builds
uv lock

# Export to requirements.txt for Lambda
uv export --format requirements-txt --no-hashes > requirements.txt

# Create build directory
mkdir -p build/

# Install to build directory with Lambda-compatible wheels
uv pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build/ \
    -r requirements.txt

# Copy application code
cp app_uv.py build/

# Create deployment package
cd build && zip -r ../lambda-uv-locked.zip . && cd ..

# Cleanup
rm requirements.txt

echo "✅ uv locked deployment package created: lambda-uv-locked.zip"
