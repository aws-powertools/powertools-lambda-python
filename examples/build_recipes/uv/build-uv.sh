#!/bin/bash

# Create build directory
mkdir -p build/

# Install dependencies with Lambda-compatible wheels
uv pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build/ \
    -e .

# Copy application code
cp app_uv.py build/

# Create deployment package
cd build && zip -r ../lambda-uv.zip . && cd ..

echo "✅ uv deployment package created: lambda-uv.zip"
