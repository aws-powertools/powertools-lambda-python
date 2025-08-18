#!/bin/bash

echo "🏗️  Building CDK application..."

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
# cdk bootstrap

# Deploy stack
cdk deploy --require-approval never

echo "✅ CDK application deployed successfully"
