#!/bin/bash

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
cp app_pip.py build-x86_64/
cp app_pip.py build-arm64/

# Create deployment packages
cd build-x86_64 && zip -r ../lambda-x86_64.zip . && cd ..
cd build-arm64 && zip -r ../lambda-arm64.zip . && cd ..

echo "✅ x86_64 package: lambda-x86_64.zip"
echo "✅ ARM64 package: lambda-arm64.zip"
