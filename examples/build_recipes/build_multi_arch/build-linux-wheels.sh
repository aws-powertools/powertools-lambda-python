#!/bin/bash

# Create build directory
mkdir -p build/

# Install Linux-compatible wheels
pip install \
    --platform manylinux2014_x86_64 \
    --target build/ \
    --implementation cp \
    --python-version 3.14 \
    --only-binary=:all: \
    --upgrade \
    --abi cp313 \
    -r requirements.txt

# Copy application code
cp -r src/* build/

# Create deployment package
cd build && zip -r ../lambda-linux.zip . && cd ..

echo "✅ Linux-compatible package created"
