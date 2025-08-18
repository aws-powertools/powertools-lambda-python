---
title: Build Tools
description: Package Lambda functions using different build tools and dependency managers
---

<!-- markdownlint-disable MD043 MD013 -->

This guide covers different build tools and dependency managers for packaging Lambda functions with Powertools for AWS Lambda (Python). Each tool has its strengths and is optimized for different use cases.

???+ info "Requirements file security"
    For simplicity, examples in this guide use `requirements.txt` files with pinned versions. In production environments, you should use hash-checking for enhanced security by including `--hash` flags. Learn more about [secure package installation](https://pip.pypa.io/en/stable/topics/secure-installs/){target="_blank"} in the pip documentation.

## pip

**pip** is Python's standard package installer - simple, reliable, and available everywhere. Perfect for straightforward Lambda functions where you need basic dependency management without complex workflows.

???+ warning "Cross-platform compatibility"
    Always use `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags when building on non-Linux systems to ensure Lambda compatibility. This forces pip to download Linux-compatible wheels instead of compiling from source.

### Basic setup

=== "requirements.txt"

    ```bash
    aws-lambda-powertools[all]==3.18.0
    pydantic==2.10.4
    requests>=2.32.4
    ```

=== "app_pip.py"

    ```python
    --8<-- "examples/build_recipes/pip/app_pip.py"
    ```

=== "build.sh"

    ```bash
    --8<-- "examples/build_recipes/pip/build.sh"
    ```

### Advanced pip with Lambda Layers

Optimize your deployment by using Lambda layers for Powertools for AWS:

=== "requirements-layer.txt"

    ```bash
    aws-lambda-powertools[all]==3.18.0
    ```

=== "requirements-app.txt"

    ```bash
    pydantic==2.10.4
    requests>=2.32.4
    ```

=== "app_pip.py"

    ```python
    --8<-- "examples/build_recipes/pip/app_pip.py"
    ```

=== "build-with-layer.sh"

    ```bash
    --8<-- "examples/build_recipes/pip/build-with-layer.sh"
    ```

### Cross-platform builds

Build packages for different Lambda architectures using platform-specific wheels:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/pip/build-cross-platform.sh"
    ```

#### Platform compatibility

| Platform Flag | Lambda Architecture | Use Case |
|---------------|-------------------|----------|
| `manylinux2014_x86_64` | x86_64 | Standard Lambda functions |
| `manylinux2014_aarch64` | arm64 | Graviton-based functions (lower cost) |

???+ tip "Architecture selection"
    - **x86_64**: Broader package compatibility, more mature ecosystem
    - **arm64**: Up to 20% better price-performance, newer architecture

## uv

**uv** is an extremely fast Python package manager written in Rust, designed as a drop-in replacement for pip and pip-tools. It offers 10-100x faster dependency resolution and installation, making it ideal for CI/CD pipelines and performance-critical builds. Learn more at [docs.astral.sh/uv/](https://docs.astral.sh/uv/){target="_blank"}.

???+ warning "Cross-platform compatibility"
    Use `uv pip install` with `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags when building on non-Linux systems. This ensures Lambda-compatible wheels are downloaded instead of compiling from source.

### Setup uv

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

### uv with lock file for reproducible builds

Generate and use lock files to ensure exact dependency versions across all environments and team members.

=== "build-uv-locked.sh"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv-locked.sh"
    ```

### Cross-platform builds with uv

Build packages for different Lambda architectures using uv's platform-specific installation:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv-cross-platform.sh"
    ```

#### uv performance advantages

| Feature | uv | pip | Benefit |
|---------|----|----|---------|
| **Dependency resolution** | Rust-based solver | Python-based | 10-100x faster |
| **Parallel downloads** | Built-in | Limited | Faster package installation |
| **Lock file generation** | `uv lock` | Requires pip-tools | Reproducible builds |
| **Virtual environments** | `uv venv` | Separate venv tool | Integrated workflow |

???+ tip "uv best practices for Lambda"
    - Use `uv lock` for reproducible builds across environments
    - Leverage `uv export` to generate requirements.txt for deployment
    - Use `--frozen` flag in CI/CD to ensure exact dependency versions

## Poetry

**Poetry** is a modern Python dependency manager that handles packaging, dependency resolution, and virtual environments. It uses lock files to ensure reproducible builds and provides excellent developer experience with semantic versioning.

???+ warning "Cross-platform compatibility"
    When building on non-Linux systems, use `pip install` with `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags after exporting requirements from Poetry. This ensures Lambda-compatible wheels are installed.

### Setup Poetry

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

#### Alternative: Poetry-only build (not recommended for production)

For development or when cross-platform compatibility is not a concern:

=== "build-poetry-native.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-poetry-native.sh"
    ```

### Cross-platform builds with Poetry

Build packages for different Lambda architectures by combining Poetry's dependency management with pip's platform-specific installation:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-poetry-cross-platform.sh"
    ```

#### Poetry build methods comparison

| Method | Cross-platform Safe | Speed | Reproducibility | Recommendation |
|--------|-------------------|-------|-----------------|----------------|
| **Poetry + pip** | ✅ Yes | Fast | High | ✅ Recommended |
| **Poetry native** | ❌ No | Fastest | Medium | ⚠️ Development only |
| **Poetry + Docker** | ✅ Yes | Slower | Highest | ✅ Complex dependencies |

???+ tip "Poetry best practices for Lambda"
    - Always use `poetry export` to generate requirements.txt for deployment
    - Use `--without-hashes` flag to avoid pip compatibility issues
    - Combine with `pip install --platform` for cross-platform builds
    - Keep `poetry.lock` in version control for reproducible builds

### Poetry with Docker for consistent builds

Use Docker to ensure consistent builds across different development environments and avoid platform-specific dependency issues.

=== "Dockerfile"

    ```dockerfile title="Dockerfile.poetry"
    --8<-- "examples/build_recipes/poetry/Dockerfile.poetry"
    ```

=== "build-with-poetry-docker.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-with-poetry-docker.sh"
    ```

## SAM

**AWS SAM (Serverless Application Model)** is AWS's framework for building serverless applications using CloudFormation templates. It provides local testing capabilities, built-in best practices, and seamless integration with AWS services, making it the go-to choice for AWS-native serverless development.

SAM automatically resolves multi-architecture compatibility issues by building functions inside Lambda-compatible containers (`--use-container` flag), ensuring dependencies are installed with the correct architecture and glibc versions for the Lambda runtime environment. This eliminates the common problem of architecture mismatches when building on macOS/Windows.

Learn more at [AWS SAM documentation](https://docs.aws.amazon.com/serverless-application-model/){target="_blank"}.

### SAM without Layers (All-in-one package)

Simple approach where all dependencies are packaged with the function code:

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/no-layers/template.yaml"
    ```

=== "requirements.txt"

    ```txt
    aws-lambda-powertools[all]==3.18.0
    pydantic==2.10.4
    requests>=2.32.4
    ```

=== "src/app_sam_no_layer.py"

    ```python
    --8<-- "examples/build_recipes/sam/no-layers/src/app_sam_no_layer.py"
    ```

=== "build-sam-no-layers.sh"

    ```bash
    --8<-- "examples/build_recipes/sam/no-layers/build-sam-no-layers.sh"
    ```

### SAM with Layers (Optimized approach)

Optimized approach using Lambda Layers to separate dependencies from application code. This example demonstrates:

* **Public Powertools for AWS Lambda layer** - Uses AWS-managed layer ARN for better performance and maintenance
* **Custom dependencies layer** - Separates application-specific dependencies

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/with-layers/template.yaml"
    ```

=== "layers/dependencies/requirements.txt"

    ```txt
    pydantic==2.10.4
    requests>=2.32.4
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

### Advanced SAM with multiple environments

Configure different environments (dev, staging, prod) with environment-specific settings and layer references. This example demonstrates how to use parameters, mappings, and conditions to create flexible, multi-environment deployments.

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/multi-env/template.yaml"
    ```

## CDK

The **AWS CDK (Cloud Development Kit)** allows you to define cloud infrastructure using familiar programming languages like Python, TypeScript, or Java. It provides type safety, IDE support, and the ability to create reusable constructs, making it perfect for complex infrastructure requirements and teams that prefer code over YAML.

Learn more at [AWS CDK documentation](https://docs.aws.amazon.com/cdk/){target="_blank"}.

### Basic CDK setup with Python

CDK uses the concept of **Apps**, **Stacks**, and **Constructs** to organize infrastructure. A CDK app contains one or more stacks, and each stack contains constructs that represent AWS resources.

#### Project structure

```bash
my-lambda-cdk/
├── app.py                 # CDK app entry point
├── cdk.json              # CDK configuration
├── requirements.txt      # CDK dependencies
├── src/
│   └── lambda_function.py # Lambda function code
└── stacks/
    └── lambda_stack.py   # Stack definition (optional)
```

#### Key CDK concepts for Lambda

| Concept | Description | Lambda Usage |
|---------|-------------|--------------|
| **App** | Root construct, contains stacks | Entry point for your Lambda infrastructure |
| **Stack** | Unit of deployment | Groups related Lambda functions and resources |
| **Construct** | Reusable cloud component | Lambda function, API Gateway, DynamoDB table |
| **Asset** | Local files bundled with deployment | Lambda function code, layers |

#### Prerequisites

Before starting, ensure you have:

```bash
--8<-- "examples/build_recipes/cdk/basic/setup-cdk.sh"
```

#### Basic implementation

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
    aws-cdk-lib>=2.100.0
    constructs>=10.0.0
    ```

=== "src/lambda_function.py"

    ```python
    --8<-- "examples/build_recipes/cdk/basic/src/lambda_function.py"
    ```

=== "build-cdk.sh"

    ```bash
    --8<-- "examples/build_recipes/cdk/basic/build-cdk.sh"
    ```

#### CDK bundling options

CDK provides several ways to handle Lambda function dependencies:

| Method | Description | Best For |
|--------|-------------|----------|
| **Inline bundling** | CDK bundles dependencies automatically | Simple functions with few dependencies |
| **Docker bundling** | Uses Docker for consistent builds | Complex dependencies, cross-platform builds |
| **Pre-built assets** | Upload pre-packaged ZIP files | Custom build processes, CI/CD integration |
| **Lambda Layers** | Separate dependencies from code | Shared dependencies across functions |

#### Common CDK commands

```bash
--8<-- "examples/build_recipes/cdk/basic/cdk-commands.sh"
```

### Advanced CDK with multiple stacks

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

## Pants

**Pants** is a powerful build system designed for large codebases and monorepos. It provides incremental builds, dependency inference, and advanced caching mechanisms. Ideal for organizations with complex Python projects that need fine-grained build control and optimization.

### Setup

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

### Advanced Pants with multiple targets

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
