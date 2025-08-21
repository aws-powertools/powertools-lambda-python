#!/bin/bash

# Build all Lambda functions
pants package ::

# Process each Lambda function
for pex_file in dist/*.pex; do
    base_name=$(basename "$pex_file" .pex)

    # Create build directory for this function
    mkdir -p "build/$base_name"
    cd "build/$base_name"

    # Extract PEX contents
    python "../../$pex_file" --pex-root . --pex-path . -c "import sys; sys.exit(0)"

    # Create deployment zip
    zip -r "../../$base_name.zip" .
    cd ../..

    echo "✅ Created: $base_name.zip"
done
