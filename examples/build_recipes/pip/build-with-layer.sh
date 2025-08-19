#!/bin/bash

# Build Lambda Layer with compatible wheels
mkdir -p layer/python/
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target layer/python/ \
    -r requirements-layer.txt
cd layer && zip -r ../powertools-layer.zip . && cd ..

# Build application package (smaller without Powertools)
mkdir -p build/
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --python-version 3.13 --target build/ \
    -r requirements-app.txt
cp app_pip.py build/
cd build && zip -r ../lambda-app.zip . && cd ..

echo "✅ Layer created: powertools-layer.zip"
echo "✅ App package created: lambda-app.zip"
