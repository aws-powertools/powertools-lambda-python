#!/bin/bash

# Remove unnecessary files to reduce package size
find build/ -name "*.pyc" -delete
find build/ -name "__pycache__" -type d -exec rm -rf {} +
find build/ -name "*.dist-info" -type d -exec rm -rf {} +
find build/ -name "tests" -type d -exec rm -rf {} +
find build/ -name "test_*" -delete

# Remove documentation and examples
find build/ -name "docs" -type d -exec rm -rf {} +
find build/ -name "examples" -type d -exec rm -rf {} +

echo "✅ Package optimized"
