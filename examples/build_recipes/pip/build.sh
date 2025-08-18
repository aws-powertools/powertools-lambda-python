#!/bin/bash

# Create build directory
mkdir -p build/

# Install dependencies with Lambda-compatible wheels
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build/ \
    -r requirements.txt

# Copy application code
cp app_pip.py build/

# Create deployment package
cd build && zip -r ../lambda-deployment.zip . && cd ..

echo "✅ Deployment package created: lambda-deployment.zip"
