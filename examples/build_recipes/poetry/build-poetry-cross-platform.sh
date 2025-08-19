#!/bin/bash

# Export requirements for Lambda
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Build for Lambda x86_64 (most common)
mkdir -p build-x86_64/
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build-x86_64/ \
    -r requirements.txt

# Build for Lambda ARM64 (Graviton2)
mkdir -p build-arm64/
pip install --platform manylinux2014_aarch64 --only-binary=:all: \
    --python-version 3.13 --target build-arm64/ \
    -r requirements.txt

# Copy application code to both builds
cp app_poetry.py build-x86_64/
cp app_poetry.py build-arm64/

# Create deployment packages
cd build-x86_64 && zip -r ../lambda-poetry-x86_64.zip . && cd ..
cd build-arm64 && zip -r ../lambda-poetry-arm64.zip . && cd ..

# Cleanup
rm requirements.txt

echo "✅ x86_64 package: lambda-poetry-x86_64.zip"
echo "✅ ARM64 package: lambda-poetry-arm64.zip"
