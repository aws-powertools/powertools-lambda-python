---
title: Build with SAM
description: Package Lambda functions using AWS SAM for serverless applications
---

<!-- markdownlint-disable MD043 -->

**AWS SAM (Serverless Application Model)** is AWS's framework for building serverless applications using CloudFormation templates. It provides local testing capabilities, built-in best practices, and seamless integration with AWS services, making it the go-to choice for AWS-native serverless development.

SAM automatically resolves multi-architecture compatibility issues by building functions inside Lambda-compatible containers (`--use-container` flag), ensuring dependencies are installed with the correct architecture and glibc versions for the Lambda runtime environment. This eliminates the common problem of architecture mismatches when building on macOS/Windows.

Learn more at [AWS SAM documentation](https://docs.aws.amazon.com/serverless-application-model/){target="_blank"}.

## SAM without Layers (All-in-one package)

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

## SAM with Layers (Optimized approach)

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

## Comparison: with vs without Layers

| Aspect | Without Layers | With Layers |
|--------|----------------|-------------|
| **Deployment Speed** | Slower (uploads all deps each time) | Faster (layers cached, only app code changes) |
| **Package Size** | Larger function packages | Smaller function packages |
| **Cold Start** | Slightly faster (everything in one place) | Slightly slower (layer loading overhead) |
| **Reusability** | No sharing between functions | Layers shared across functions |
| **Complexity** | Simple, single package | More complex, multiple components |
| **Best For** | Single function, simple apps | Multiple functions, shared dependencies |

## Advanced SAM with multiple environments

Configure different environments (dev, staging, prod) with environment-specific settings and layer references. This example demonstrates how to use parameters, mappings, and conditions to create flexible, multi-environment deployments.

=== "template.yaml"

    ```yaml
    --8<-- "examples/build_recipes/sam/multi-env/template.yaml"
    ```
