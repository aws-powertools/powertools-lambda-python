#!/bin/bash

# Build for Lambda x86_64 (most common)
mkdir -p build-x86_64/
uv pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build-x86_64/ \
    -e .

# Build for Lambda ARM64 (Graviton2)
mkdir -p build-arm64/
uv pip install --platform manylinux2014_aarch64 --only-binary=:all: \
    --python-version 3.13 --target build-arm64/ \
    -e .

# Copy application code to both builds
cp app_uv.py build-x86_64/
cp app_uv.py build-arm64/

# Create deployment packages
cd build-x86_64 && zip -r ../lambda-uv-x86_64.zip . && cd ..
cd build-arm64 && zip -r ../lambda-uv-arm64.zip . && cd ..

echo "✅ x86_64 package: lambda-uv-x86_64.zip"
echo "✅ ARM64 package: lambda-uv-arm64.zip"
