#!/bin/bash

# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# Create build directory
mkdir -p build/

# Copy installed packages
cp -r .venv/lib/python*/site-packages/* build/

# Copy application code
cp app_uv.py build/

# Create deployment package
cd build && zip -r ../lambda-uv.zip . && cd ..

echo "✅ uv deployment package created: lambda-uv.zip"
