#!/bin/bash

# Remove unnecessary files
find build/ -name "*.pyc" -delete
find build/ -name "__pycache__" -type d -exec rm -rf {} +
find build/ -name "*.dist-info" -type d -exec rm -rf {} +
find build/ -name "tests" -type d -exec rm -rf {} +
find build/ -name "test_*" -delete

# Remove debug symbols from compiled extensions
find build/ -name "*.so" -exec strip --strip-debug {} \; 2>/dev/null || true
find build/ -name "*.so.*" -exec strip --strip-debug {} \; 2>/dev/null || true

# Remove additional bloat from common packages
rm -rf build/*/site-packages/*/tests/
rm -rf build/*/site-packages/*/test/
rm -rf build/*/site-packages/*/.git/
rm -rf build/*/site-packages/*/docs/
rm -rf build/*/site-packages/*/examples/
rm -rf build/*/site-packages/*/*.md
rm -rf build/*/site-packages/*/*.rst
rm -rf build/*/site-packages/*/*.txt

# Calculate size reduction
echo "📊 Package optimization completed"
du -sh build/ 2>/dev/null || echo "✅ Advanced optimization applied"
