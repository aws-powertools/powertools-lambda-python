#!/bin/bash

# Create build directory
mkdir -p build/

# Install dependencies directly to build directory using Poetry
# Note: This method may not handle cross-platform compatibility as well
poetry install --only=main --no-root

# Copy installed packages from virtual environment
VENV_PATH=$(poetry env info --path)
cp -r "$VENV_PATH/lib/python*/site-packages"/* build/

# Copy application code
cp app_poetry.py build/

# Create deployment package
cd build && zip -r ../lambda-poetry-native.zip . && cd ..

echo "✅ Poetry native deployment package created: lambda-poetry-native.zip"
echo "⚠️  Warning: This method may have cross-platform compatibility issues"
