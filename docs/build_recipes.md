---
title: Build Recipes
description: Lambda function packaging recipes with Powertools for AWS
---

<!-- markdownlint-disable MD043 MD013 -->

This guide provides practical recipes for packaging Lambda functions with Powertools for AWS Lambda (Python) using different build tools and dependency managers.

## Key benefits

* **Optimized packaging** - Reduce deployment package size and cold start times
* **Dependency management** - Handle complex dependency trees efficiently
* **Build reproducibility** - Consistent builds across environments
* **Layer optimization** - Leverage Lambda Layers for better performance
* **Multi-tool support** - Choose the right tool for your workflow

## Terminology

Understanding these key terms will help you navigate the build recipes more effectively:

| Term | Definition |
|------|------------|
| **Deployment Package** | A ZIP archive or container image containing your Lambda function code and all its dependencies, ready for deployment to AWS Lambda |
| **Lambda Layer** | A ZIP archive containing libraries, custom runtimes, or other function dependencies that can be shared across multiple Lambda functions |
| **Build Tool** | Software that automates the process of compiling, packaging, and preparing your code for deployment (e.g., pip, poetry, uv, pants) |
| **Dependency Manager** | Tool responsible for resolving, downloading, and managing external libraries your project depends on |
| **Lock File** | A file that records the exact versions of all dependencies used in your project, ensuring reproducible builds (e.g., poetry.lock, uv.lock) |
| **Cold Start** | The initialization time when AWS Lambda creates a new execution environment for your function, including loading your deployment package |
| **SAM (Serverless Application Model)** | AWS framework for building serverless applications, providing templates and CLI tools for deploying Lambda functions and related resources |
| **CDK (Cloud Development Kit)** | AWS framework for defining cloud infrastructure using familiar programming languages, enabling infrastructure as code for Lambda deployments |

## Cross-Platform build considerations

Many modern Python packages include compiled extensions written in Rust or C/C++ for performance reasons. These compiled components are platform-specific and can cause deployment issues when building on different architectures.

???+ warning "Architecture Mismatch Issues"
    Building Lambda packages on macOS (ARM64/Intel) for deployment on AWS Lambda (Linux x86_64 or ARM64) will result in incompatible binary dependencies that cause import errors at runtime.

### Common compiled libraries

Taking into consideration Powertools for AWS dependencies and common Python packages, these libraries include compiled Rust/C components that require architecture-specific builds:

| Library | Language | Components | Impact | Used in Powertools for AWS|
|---------|----------|------------|--------|-------------------|
| **pydantic** | Rust | Core validation engine | High - Core functionality affected | ✅ Core dependency |
| **aws-encryption-sdk** | C | Encryption/decryption | High - Data masking fails | ✅ Optional (datamasking extra) |
| **protobuf** | C++ | Protocol buffer serialization | High - Message parsing fails | ✅ Optional (kafka-consumer-protobuf) |
| **redis** | C | Redis client with hiredis | Medium - Falls back to pure Python | ✅ Optional (redis extra) |
| **valkey-glide** | Rust | High-performance Redis client | High - Client completely broken | ✅ Optional (valkey extra) |
| **orjson** | Rust | JSON serialization | Medium - Performance degradation | ❌ Not used (but common) |
| **uvloop** | C | Event loop implementation | Medium - Falls back to asyncio | ❌ Not used (but common) |
| **lxml** | C | XML/HTML processing | High - XML parsing fails | ❌ Not used (but common) |

### Extras dependencies and architecture

Different Powertools for AWS extras dependencies have varying levels of architecture dependency:

=== "Safe extras (pure python)"

    ```txt title="requirements.txt - Safe for any platform"
    # These extras have minimal or no compiled dependencies
    aws-lambda-powertools[tracer]==3.18.0      # aws-xray-sdk (mostly pure Python)
    aws-lambda-powertools[aws-sdk]==3.18.0    # boto3 (pure Python)
    ```

=== "Architecture-dependent extras"

    ```txt title="requirements.txt - Requires Linux builds"
    # These extras include compiled dependencies
    aws-lambda-powertools[parser]==3.18.0           # pydantic (Rust)
    aws-lambda-powertools[validation]==3.18.0       # fastjsonschema (C)
    aws-lambda-powertools[datamasking]==3.18.0      # aws-encryption-sdk (C)
    aws-lambda-powertools[redis]==3.18.0            # redis with hiredis (C)
    aws-lambda-powertools[valkey]==3.18.0           # valkey-glide (Rust)
    aws-lambda-powertools[kafka-consumer-avro]==3.18.0      # avro (C)
    aws-lambda-powertools[kafka-consumer-protobuf]==3.18.0  # protobuf (C++)
    ```

=== "All extras (mixed dependencies)"

    ```txt title="requirements.txt - Requires careful platform handling"
    # The 'all' extra includes both safe and architecture-dependent packages
    aws-lambda-powertools[all]==3.18.0

    # This is equivalent to:
    # pydantic, pydantic-settings, aws-xray-sdk, fastjsonschema,
    # aws-encryption-sdk, jsonpath-ng
    ```

???+ tip "Powertools for AWS build strategy"
    1. **Use `[all]` extra with Docker builds** for maximum compatibility
    2. **Use specific extras** if you want to avoid certain compiled dependencies
    3. **Test imports** after building to catch architecture mismatches early

### Multi-platform build strategies

=== "Docker-based Builds (Recommended)"

    Use AWS Lambda base images to ensure Linux x86_64 or ARM64 compatibility:

    === "Dockerfile"

        ```dockerfile
        --8<-- "examples/build_recipes/build_multi_arch/Dockerfile.lambda"
        ```

    === "Build Script"

        ```bash
        --8<-- "examples/build_recipes/build_multi_arch/build-multiplatform.sh"
        ```

=== "Platform-specific pip install"

    Force installation of Linux-compatible wheels:

    === "Build Script"

        ```bash
        --8<-- "examples/build_recipes/build_multi_arch/build-linux-wheels.sh"
        ```

=== "GitHub Actions multi-arch"

    Use GitHub Actions with Linux runners for consistent builds:

    === "Workflow"

        ```yaml
        --8<-- "examples/build_recipes/build_multi_arch/lambda-build.yml"
        ```

### Best practices for cross-platform builds

???+ tip "Development Workflow"
    Develop locally on your preferred platform, but always build deployment packages in a Linux environment or Docker container to ensure compatibility.

1. **Always build on Linux** for Lambda deployments, or use Docker with Lambda base images
2. **Use `--platform` flags** when installing with pip to force Linux-compatible wheels
3. **Test imports** in your build environment before deployment
4. **Pin dependency versions** to ensure reproducible builds across platforms
5. **Use CI/CD with Linux runners** to avoid local architecture issues
6. **Consider Lambda container images** for complex dependency scenarios

## Getting started

???+ tip
    All examples in this guide are available in the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples/build_recipes){target="_blank"}.

### Prerequisites

Before using any of these recipes, ensure you have:

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){target="_blank"} configured
* Python 3.10+ installed
* Your preferred build tool installed (see individual recipes)

### Choosing the right tool

Each build tool has its strengths and is optimized for different use cases. Consider your project complexity, team preferences, and deployment requirements when selecting the best approach.

| Tool                  | Best for                          | Considerations                              |
| --------------------- | --------------------------------- | ------------------------------------------- |
| **[pip](#pip)**       | Simple projects, CI/CD            | Lightweight, universal                      |
| **[poetry](#poetry)** | Modern Python projects            | Excellent dependency management, lock files |
| **[uv](#uv)**         | Fast builds, performance-critical | Extremely fast, Rust-based                  |
| **[pants](#pants)**   | Monorepos, complex projects       | Advanced build system, incremental builds   |
| **[SAM](#sam)**       | AWS-native deployments            | Integrated with AWS, local testing          |
| **[CDK](#cdk)**       | Infrastructure as code            | Programmatic infrastructure, type safety    |

## Build recipes

### Pip

**pip** is Python's standard package installer - simple, reliable, and available everywhere. Perfect for straightforward Lambda functions where you need basic dependency management without complex workflows.

#### Basic setup

=== "requirements.txt"

    ```bash
    --8<-- "examples/build_recipes/pip/requirements.txt"
    ```

=== "app_pip.py"

    ```python
    --8<-- "examples/build_recipes/pip/app_pip.py"
    ```

=== "build.sh"

    ```bash
    --8<-- "examples/build_recipes/pip/build.sh"
    ```

#### Advanced pip with Lambda Layers

Optimize your deployment by using Lambda Layers for Powertools for AWS:

=== "requirements-layer.txt"

    ```bash
    --8<-- "examples/build_recipes/pip/requirements-layer.txt"
    ```

=== "requirements-app.txt"

    ```bash
    --8<-- "examples/build_recipes/pip/requirements-app.txt"
    ```

=== "app_pip.py"

    ```python
    --8<-- "examples/build_recipes/pip/app_pip.py"
    ```

=== "build-with-layer.sh"

    ```bash
    --8<-- "examples/build_recipes/pip/build-with-layer.sh"
    ```

### Poetry

**Poetry** is a modern Python dependency manager that handles packaging, dependency resolution, and virtual environments. It uses lock files to ensure reproducible builds and provides excellent developer experience with semantic versioning.

#### Setup Poetry

???+ info "Prerequisites"
    - **Poetry 2.0+** required for optimal performance and latest features
    - Initialize a new project with `poetry new my-lambda-project` or `poetry init` in existing directory
    - Project name in `pyproject.toml` can be customized to match your preferences
    - See [Poetry documentation](https://python-poetry.org/docs/basic-usage/){target="_blank"} for detailed project setup guide

=== "pyproject.toml"

    ```toml
    --8<-- "examples/build_recipes/poetry/pyproject.toml"
    ```

=== "app.py"

    ```python
    --8<-- "examples/build_recipes/poetry/app_poetry.py"
    ```

=== "build-with-poetry.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-with-poetry.sh"
    ```

#### Poetry with Docker for consistent builds

Use Docker to ensure consistent builds across different development environments and avoid platform-specific dependency issues.

=== "Dockerfile"

    ```dockerfile title="Dockerfile.poetry"
    --8<-- "examples/build_recipes/poetry/Dockerfile.poetry"
    ```

=== "build-with-poetry-docker.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-with-poetry-docker.sh"
    ```

### uv

**uv** is an extremely fast Python package manager written in Rust, designed as a drop-in replacement for pip and pip-tools. It offers 10-100x faster dependency resolution and installation, making it ideal for CI/CD pipelines and performance-critical builds. Learn more at [docs.astral.sh/uv/](https://docs.astral.sh/uv/){target="_blank"}.

#### Setup uv

=== "pyproject.toml"

    ```toml
    --8<-- "examples/build_recipes/uv/pyproject.toml"
    ```

=== "app_uv.py"

    ```python
    --8<-- "examples/build_recipes/uv/app_uv.py"
    ```

=== "build-uv.sh"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv.sh"
    ```

#### uv with lock file for reproducible builds

Generate and use lock files to ensure exact dependency versions across all environments and team members.

=== "build-uv-locked.sh"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv-locked.sh"
    ```

### SAM

**AWS SAM (Serverless Application Model)** is AWS's framework for building serverless applications using CloudFormation templates. It provides local testing capabilities, built-in best practices, and seamless integration with AWS services, making it the go-to choice for AWS-native serverless development.

SAM automatically resolves multi-architecture compatibility issues by building functions inside Lambda-compatible containers (`--use-container` flag), ensuring dependencies are installed with the correct architecture and glibc versions for the Lambda runtime environment. This eliminates the common problem of architecture mismatches when building on macOS/Windows for Linux-based Lambda execution.

Learn more at [AWS SAM documentation](https://docs.aws.amazon.com/serverless-application-model/){target="_blank"}.

#### SAM without Layers (All-in-one package)

Simple approach where all dependencies are packaged with the function code:

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/no-layers/template.yaml"
    ```

=== "requirements.txt"

    ```txt
    --8<-- "examples/build_recipes/sam/no-layers/requirements.txt"
    ```

=== "src/app_sam_no_layer.py"

    ```python
    --8<-- "examples/build_recipes/sam/no-layers/src/app_sam_no_layer.py"
    ```

=== "build-sam-no-layers.sh"

    ```bash
    --8<-- "examples/build_recipes/sam/no-layers/build-sam-no-layers.sh"
    ```

#### SAM with Layers (Optimized approach)

Optimized approach using Lambda Layers to separate dependencies from application code. This example demonstrates:

* **Public Powertools for AWS Lambda layer** - Uses AWS-managed layer ARN for better performance and maintenance
* **Custom dependencies layer** - Separates application-specific dependencies

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/with-layers/template.yaml"
    ```

=== "layers/dependencies/requirements.txt"

    ```txt
    --8<-- "examples/build_recipes/sam/with-layers/layers/dependencies/requirements.txt"
    ```

=== "src/app/app_sam_layer.py"

    ```python
    --8<-- "examples/build_recipes/sam/with-layers/src/app/app_sam_layer.py"
    ```

=== "src/worker/worker_sam_layer.py"

    ```python
    --8<-- "examples/build_recipes/sam/with-layers/src/worker/worker_sam_layer.py"
    ```

=== "samconfig.toml"

    ```toml
    --8<-- "examples/build_recipes/sam/with-layers/samconfig.toml"
    ```

=== "build-sam-with-layers.sh"

    ```bash
    --8<-- "examples/build_recipes/sam/with-layers/build-sam-with-layers.sh"
    ```

#### Comparison: with vs without Layers

| Aspect | Without Layers | With Layers |
|--------|----------------|-------------|
| **Deployment Speed** | Slower (uploads all deps each time) | Faster (layers cached, only app code changes) |
| **Package Size** | Larger function packages | Smaller function packages |
| **Cold Start** | Slightly faster (everything in one place) | Slightly slower (layer loading overhead) |
| **Reusability** | No sharing between functions | Layers shared across functions |
| **Complexity** | Simple, single package | More complex, multiple components |
| **Best For** | Single function, simple apps | Multiple functions, shared dependencies |

#### Advanced SAM with multiple environments

Configure different environments (dev, staging, prod) with environment-specific settings and layer references. This example demonstrates how to use parameters, mappings, and conditions to create flexible, multi-environment deployments.

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/multi-env/template.yaml"
    ```

### CDK

**AWS CDK (Cloud Development Kit)** allows you to define cloud infrastructure using familiar programming languages like Python, TypeScript, or Java. It provides type safety, IDE support, and the ability to create reusable constructs, making it perfect for complex infrastructure requirements and teams that prefer code over YAML.

Learn more at [AWS CDK documentation](https://docs.aws.amazon.com/cdk/){target="_blank"}.

#### Basic CDK setup with Python

=== "app.py"

    ```python
    --8<-- "examples/build_recipes/cdk/basic/app.py"
    ```

=== "cdk.json"

    ```json
    --8<-- "examples/build_recipes/cdk/basic/cdk.json"
    ```

=== "requirements.txt"

    ```txt
    --8<-- "examples/build_recipes/cdk/basic/requirements.txt"
    ```

=== "src/lambda_function.py"

    ```python
    --8<-- "examples/build_recipes/cdk/basic/src/lambda_function.py"
    ```

=== "build-cdk.sh"

    ```bash
    --8<-- "examples/build_recipes/cdk/basic/build-cdk.sh"
    ```

#### Advanced CDK with multiple stacks

Multi-environment CDK setup with separate stacks, DynamoDB integration, and SQS message processing using BatchProcessor.

=== "stacks/powertools_cdk_stack.py"

    ```python
    --8<-- "examples/build_recipes/cdk/multi-stack/stacks/powertools_cdk_stack.py"
    ```

=== "cdk.json"

    ```json
    --8<-- "examples/build_recipes/cdk/multi-stack/cdk.json"
    ```

=== "app_multi_stack.py"

    ```python
    --8<-- "examples/build_recipes/cdk/multi-stack/app_multi_stack.py"
    ```

=== "src/app/api.py"

    ```python
    --8<-- "examples/build_recipes/cdk/multi-stack/src/app/api.py"
    ```

=== "src/worker/worker.py"

    ```python
    --8<-- "examples/build_recipes/cdk/multi-stack/src/worker/worker.py"
    ```

=== "deploy-environments.sh"

    ```bash
    --8<-- "examples/build_recipes/cdk/multi-stack/deploy-environments.sh"
    ```

### Pants

**Pants** is a powerful build system designed for large codebases and monorepos. It provides incremental builds, dependency inference, and advanced caching mechanisms. Ideal for organizations with complex Python projects that need fine-grained build control and optimization.

#### Setup

=== "pants.toml"

    ```toml
    --8<-- "examples/build_recipes/pants/basic_pants/pants.toml"
    ```

=== "BUILD"

    ```python
    --8<-- "examples/build_recipes/pants/basic_pants/BUILD"
    ```

=== "app.py"

    ```python
    --8<-- "examples/build_recipes/pants/basic_pants/app_pants.py"
    ```

=== "build-pants.sh"

    ```bash
    --8<-- "examples/build_recipes/pants/basic_pants/build-pants.sh"
    ```

#### Advanced Pants with multiple targets

Pants excels at managing complex projects with multiple Lambda functions that share dependencies. This approach provides significant benefits for monorepo architectures and microservices.

=== "BUILD"

    ```python
    --8<-- "examples/build_recipes/pants/multi-target/BUILD"
    ```

=== "app/handler.py"

    ```python
    --8<-- "examples/build_recipes/pants/multi-target/app/handler.py"
    ```

=== "worker/worker_pants.py"

    ```python
    --8<-- "examples/build_recipes/pants/multi-target/worker/worker_pants.py"
    ```

=== "build-pants-multi.sh"

    ```bash
    --8<-- "examples/build_recipes/pants/multi-target/build-pants-multi.sh"
    ```

## Performance optimization tips

Optimize your Lambda functions for better performance, reduced cold start times, and lower costs. These techniques help minimize package size, improve startup speed, and reduce memory usage.

### Reduce cold start times

1. **Minimize package size** by excluding unnecessary files
2. **Use compiled dependencies** when possible
3. **Leverage Lambda SnapStart** or **Provisioned concurrency** when possible

### Build optimization

=== "Exclude unnecessary files"

    ```bash
    --8<-- "examples/build_recipes/build_optimization/optimize-package.sh"
    ```

=== "Layer optimization"

    ```bash
    --8<-- "examples/build_recipes/build_optimization/optimize-layer.sh"
    ```

=== "Advanced optimization with debug symbol removal"

    ```bash
    --8<-- "examples/build_recipes/build_optimization/optimize-advanced.sh"
    ```

## CI/CD integration

Automate your Lambda function builds and deployments using popular CI/CD platforms. These examples show how to build and deploy Lambda functions with Powertools for AWS with proper cross-platform compatibility and deploy them reliably.

### GitHub Actions

**GitHub Actions** provides a powerful, integrated CI/CD platform that runs directly in your GitHub repository. It offers excellent integration with AWS services, supports matrix builds for testing multiple configurations, and provides a rich ecosystem of pre-built actions.

=== "Modern AWS Lambda deploy action"

    ```yaml
    --8<-- "examples/build_recipes/cicd/github-actions/deploy-modern.yml"
    ```

=== "Multi-environment deployment"

    ```yaml
    --8<-- "examples/build_recipes/cicd/github-actions/deploy-multi-env.yml"
    ```

=== "Simple source code deployment"

    ```yaml
    --8<-- "examples/build_recipes/cicd/github-actions/deploy-simple.yml"
    ```

=== "S3 deployment method"

    ```yaml
    --8<-- "examples/build_recipes/cicd/github-actions/deploy-s3.yml"
    ```

=== "Build tool integration"

    ```yaml
    --8<-- "examples/build_recipes/cicd/github-actions/deploy-build-tools.yml"
    ```

### AWS CodeBuild

**AWS CodeBuild** is a fully managed build service that compiles source code, runs tests, and produces deployment packages. It integrates seamlessly with other AWS services and provides consistent build environments with automatic scaling.

=== "Basic CodeBuild Configuration"

    ```yaml
    --8<-- "examples/build_recipes/cicd/codebuild/buildspec.yml"
    ```

### Best Practices for CI/CD

1. **Use Linux runners** (ubuntu-latest) to ensure Lambda compatibility
2. **Cache dependencies** to speed up builds (uv, poetry cache, pip cache)
3. **Run tests first** before building deployment packages
4. **Use matrix builds** to test multiple Python versions or configurations
5. **Implement proper secrets management** with GitHub Secrets or AWS Parameter Store
6. **Add deployment gates** for production environments
7. **Monitor deployment success** with CloudWatch metrics and alarms

???+ tip "Performance Optimization"
    - Use **uv** for fastest dependency installation in CI/CD
    - **Cache virtual environments** between builds when possible
    - **Parallelize builds** for multiple environments
    - **Use container images** for complex dependencies or large packages

## Troubleshooting

### Common issues and solutions

#### Package size issues

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

#### Import and runtime errors

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

#### Performance issues

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

#### Build and deployment issues

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
