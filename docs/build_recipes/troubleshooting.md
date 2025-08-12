---
title: Troubleshooting
description: Common issues and solutions when building Lambda packages
---

<!-- markdownlint-disable MD043 -->

## Common issues and solutions

### Package size issues

???+ warning "Lambda deployment package too large (>50MB unzipped)"
    **Symptoms:**
    - `RequestEntityTooLargeException` during deployment
    - Slow cold starts
    - High memory usage

    **Solutions:**
    ```bash
    # 1. Use Lambda Layers for heavy dependencies
    pip install aws-lambda-powertools[all] -t layers/powertools/python/

    # 2. Remove unnecessary files
    find build/ -name "*.pyc" -delete
    find build/ -name "__pycache__" -type d -exec rm -rf {} +
    find build/ -name "tests" -type d -exec rm -rf {} +

    # 3. Strip debug symbols from compiled libraries
    find build/ -name "*.so" -exec strip --strip-debug {} \;

    # 4. Use container images for very large packages
    # Deploy as container image instead of ZIP
    ```

### Import and runtime errors

???+ error "ModuleNotFoundError or ImportError"
    **Symptoms:**
    - `ModuleNotFoundError: No module named 'aws_lambda_powertools'`
    - Function fails at runtime with import errors

    **Solutions:**
    ```bash
    # 1. Verify dependencies are in the package
    unzip -l lambda-package.zip | grep powertools

    # 2. Check Python path in Lambda
    python -c "import sys; print(sys.path)"

    # 3. Ensure platform compatibility
    pip install --platform linux_x86_64 --only-binary=:all: aws-lambda-powertools[all]

    # 4. Test imports locally
    cd build && python -c "from aws_lambda_powertools import Logger; print('OK')"
    ```

???+ error "Architecture mismatch errors"
    **Symptoms:**
    - `ImportError: /lib64/libc.so.6: version GLIBC_2.XX not found`
    - Compiled extensions fail to load

    **Solutions:**
    ```bash
    # Use Docker with Lambda base image
    docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.13 \
        pip install aws-lambda-powertools[all] -t /var/task/

    # Or force Linux-compatible wheels
    pip install --platform linux_x86_64 --implementation cp \
        --python-version 3.13 --only-binary=:all: aws-lambda-powertools[all]
    ```

### Performance issues

???+ warning "Slow cold starts"
    **Symptoms:**
    - High initialization duration in CloudWatch logs
    - Timeouts on first invocation

    **Solutions:**
    ```bash
    # 1. Optimize package size (see above)

    # 2. Use public Powertools for AWS layer
    # Layer ARN: arn:aws:lambda:region:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:1

    # 3. Enable provisioned concurrency for critical functions
    aws lambda put-provisioned-concurrency-config \
        --function-name my-function \
        --provisioned-concurrency-config ProvisionedConcurrencyCount=10

    # 4. Minimize imports in handler
    # Import only what you need, avoid heavy imports at module level
    ```

### Build and deployment issues

???+ error "Build inconsistencies across environments"
    **Symptoms:**
    - Works locally but fails in CI/CD
    - Different behavior between team members

    **Solutions:**
    ```bash
    # 1. Use lock files for reproducible builds
    # Poetry: poetry.lock
    # uv: uv.lock
    # pip: requirements.txt with pinned versions

    # 2. Use Docker for consistent build environment
    docker run --rm -v "$PWD":/app -w /app python:3.13-slim \
        bash -c "pip install -r requirements.txt -t build/"

    # 3. Pin all tool versions
    pip==24.0
    poetry==1.8.0
    uv==0.1.0

    # 4. Use same Python version everywhere
    python-version: '3.13'  # In CI/CD
    python = "^3.13"        # In pyproject.toml
    ```

???+ error "Layer compatibility issues"
    **Symptoms:**
    - Layer not found or incompatible runtime
    - Version conflicts between layer and function dependencies

    **Solutions:**
    ```bash
    # 1. Use correct layer ARN for your region and Python version
    # Check: https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer

    # 2. Verify layer compatibility
    aws lambda get-layer-version \
        --layer-name AWSLambdaPowertoolsPythonV3-python313-x86_64 \
        --version-number 1

    # 3. Avoid version conflicts
    # Don't include Powertools for AWS in deployment package if using layer
    pip install pydantic requests -t build/  # Exclude powertools
    ```
