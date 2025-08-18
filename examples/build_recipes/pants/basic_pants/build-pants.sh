#!/bin/bash

# Build the PEX binary
pants package :lambda_function

# The PEX file is created in dist/
# Rename it to a more descriptive name
mv dist/lambda_function.pex lambda-pants.pex

# For Lambda deployment, we need to extract the PEX
mkdir -p build/
cd build/

# Extract PEX contents
python ../lambda-pants.pex --pex-root . --pex-path . -c "import sys; sys.exit(0)"

# Create deployment zip
zip -r ../lambda-pants.zip .
cd ..

echo "✅ Pants deployment package created: lambda-pants.zip"
echo "✅ Pants PEX binary created: lambda-pants.pex"
