#!/bin/bash
# 1. Use correct layer ARN for your region and Python version
# Check: https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer

# 2. Verify layer compatibility
aws lambda get-layer-version \
    --layer-name AWSLambdaPowertoolsPythonV3-python313-x86_64 \
    --version-number 22 \
    --region-name {REGION}

# 3. Avoid version conflicts
# Don't include Powertools for AWS in deployment package if using layer
pip install pydantic requests -t build/  # Exclude powertools
