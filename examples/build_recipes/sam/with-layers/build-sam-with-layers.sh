#!/bin/bash

echo "🏗️  Building SAM application with layers..."

# Build Dependencies layer (Powertools uses public layer ARN)
echo "Building Dependencies layer..."
mkdir -p layers/dependencies/python
pip install pydantic requests -t layers/dependencies/python/

# Optimize layers (remove unnecessary files)
echo "Optimizing layers..."
find layers/ -name "*.pyc" -delete
find layers/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find layers/ -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find layers/ -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Build and deploy
sam build --use-container
sam deploy --guided

echo "✅ SAM application with layers deployed successfully"

# Show layer sizes
echo ""
echo "📊 Layer sizes:"
echo "Powertools: Using public layer ARN (no local build needed)"
du -sh layers/dependencies/
