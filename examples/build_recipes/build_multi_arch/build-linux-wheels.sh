#!/bin/bash

# Create build directory
mkdir -p build/

# Install Linux-compatible wheels
pip install \
    --platform linux_x86_64 \
    --target build/ \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --upgrade \
    -r requirements.txt

# Copy application code
cp -r src/* build/

# Create deployment package
cd build && zip -r ../lambda-linux.zip . && cd ..

echo "✅ Linux-compatible package created"
