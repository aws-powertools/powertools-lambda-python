#!/bin/bash
# 1. Optimize package size (see above)

# 2. Use public Powertools for AWS layer
# Layer ARN: arn:aws:lambda:region:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:1

# 3. Enable provisioned concurrency for critical functions
aws lambda put-provisioned-concurrency-config \
    --function-name my-function \
    --provisioned-concurrency-config ProvisionedConcurrencyCount=10

# 4. Minimize imports in handler
# Import only what you need, avoid heavy imports at module level
