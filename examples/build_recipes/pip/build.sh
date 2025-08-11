#!/bin/bash

# Create build directory
mkdir -p build/

# Install dependencies
pip install -r requirements.txt -t build/

# Copy application code
cp app_pip.py build/

# Create deployment package
cd build && zip -r ../lambda-deployment.zip . && cd ..

echo "✅ Deployment package created: lambda-deployment.zip"
