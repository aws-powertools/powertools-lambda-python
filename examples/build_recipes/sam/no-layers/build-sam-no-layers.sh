#!/bin/bash

echo "🏗️  Building SAM application without layers..."

# Build and deploy (SAM will handle dependency installation)
sam build --use-container
sam deploy --guided

echo "✅ SAM application deployed successfully (no layers)"
