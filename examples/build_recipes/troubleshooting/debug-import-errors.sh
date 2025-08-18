#!/bin/bash
# 1. Verify dependencies are in the package
unzip -l lambda-package.zip | grep powertools

# 2. Check Python path in Lambda
python -c "import sys; print(sys.path)"

# 3. Ensure platform compatibility
pip install --platform manylinux2014_x86_64 --only-binary=:all: aws-lambda-powertools[all]

# 4. Test imports locally
cd build && python -c "from aws_lambda_powertools import Logger; print('OK')"
