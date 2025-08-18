#!/bin/bash
# Install AWS CDK CLI
npm install -g aws-cdk

# Verify installation
cdk --version

# Bootstrap CDK in your AWS account (one-time setup)
cdk bootstrap aws://ACCOUNT-ID/REGION
