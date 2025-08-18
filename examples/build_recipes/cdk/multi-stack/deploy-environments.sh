#!/bin/bash

# Deploy to different environments
environments=("dev" "staging" "prod")

for env in "${environments[@]}"; do
    echo "🚀 Deploying to $env environment..."

    cdk deploy PowertoolsStack-$env \
        --context environment=$env \
        --require-approval never

    echo "✅ $env deployment completed"
done
