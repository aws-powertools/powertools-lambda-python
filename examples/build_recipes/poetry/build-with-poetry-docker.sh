#!/bin/bash

# Build Docker image
docker build -t lambda-powertools-app -f Dockerfile.poetry .

# Create container and extract files
docker create --name temp-container lambda-powertools-app
docker cp temp-container:/var/task ./build
docker rm temp-container

# Create deployment package
cd build && zip -r ../lambda-docker.zip . && cd ..

echo "✅ Docker-based deployment package created: lambda-docker.zip"
