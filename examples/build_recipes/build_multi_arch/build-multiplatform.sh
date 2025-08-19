 #!/bin/bash

# Build using Lambda-compatible environment
docker build -f Dockerfile.lambda -t lambda-build .

# Extract built packages
docker create --name temp-container lambda-build
docker cp temp-container:/var/task ./build
docker rm temp-container

# Create deployment package
cd build && zip -r ../lambda-multiplatform.zip . && cd ..

echo "✅ Multi-platform compatible package created"
