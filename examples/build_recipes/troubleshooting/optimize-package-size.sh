#!/bin/bash
# 1. Use Lambda Layers for heavy dependencies
pip install aws-lambda-powertools[all] -t layers/powertools/python/

# 2. Remove unnecessary files
find build/ -name "*.pyc" -delete
find build/ -name "__pycache__" -type d -exec rm -rf {} +
find build/ -name "tests" -type d -exec rm -rf {} +

# 3. Strip debug symbols from compiled libraries
find build/ -name "*.so" -exec strip --strip-debug {} \;

# 4. Use container images for very large packages
# Deploy as container image instead of ZIP
