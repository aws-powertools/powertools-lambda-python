#!/bin/bash

# Export requirements for Lambda
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create build directory
mkdir -p build/

# Install dependencies with Lambda-compatible wheels
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build/ \
    -r requirements.txt

# Copy application code
cp app_poetry.py build/

# Create deployment package
cd build && zip -r ../lambda-poetry.zip . && cd ..

# Cleanup
rm requirements.txt

echo "✅ Poetry deployment package created: lambda-poetry.zip"
