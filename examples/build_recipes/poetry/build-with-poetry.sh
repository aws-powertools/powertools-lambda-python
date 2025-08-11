#!/bin/bash

# Install dependencies
poetry install --only=main --no-root

# Export requirements for Lambda
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create build directory
mkdir -p build/

# Install dependencies to build directory
pip install -r requirements.txt -t build/

# Copy application code
cp app_poetry.py build/

# Create deployment package
cd build && zip -r ../lambda-poetry.zip . && cd ..

# Cleanup
rm requirements.txt

echo "✅ Poetry deployment package created: lambda-poetry.zip"
