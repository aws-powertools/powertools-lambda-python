#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Synthesize CloudFormation template
cdk synth

# Deploy stack
cdk deploy

# Deploy specific stack
cdk deploy MyLambdaStack

# Destroy stack
cdk destroy

# List all stacks
cdk list

# Compare deployed stack with current state
cdk diff
