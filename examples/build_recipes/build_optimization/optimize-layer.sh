#!/bin/bash

# Create optimized layer structure
mkdir -p layer/python/

# Install only production dependencies
pip install aws-lambda-powertools[all] -t layer/python/ --no-deps
pip install pydantic -t layer/python/ --no-deps

# Remove unnecessary files from layer
find layer/ -name "*.pyc" -delete
find layer/ -name "__pycache__" -type d -exec rm -rf {} +
find layer/ -name "tests" -type d -exec rm -rf {} +

# Create layer zip
cd layer && zip -r ../optimized-layer.zip . && cd ..

echo "✅ Optimized layer created: optimized-layer.zip"
