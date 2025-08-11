#!/bin/bash

# Build Lambda Layer
mkdir -p layer/python/
pip install -r requirements-layer.txt -t layer/python/
cd layer && zip -r ../powertools-layer.zip . && cd ..

# Build application package (smaller without Powertools)
mkdir -p build/
pip install -r requirements-app.txt -t build/
cp app_pip.py build/
cd build && zip -r ../lambda-app.zip . && cd ..

echo "✅ Layer created: powertools-layer.zip"
echo "✅ App package created: lambda-app.zip"
