---
title: Build with CDK
description: Package Lambda functions using AWS CDK for infrastructure as code
---

<!-- markdownlint-disable MD043 -->

The **AWS CDK (Cloud Development Kit)** allows you to define cloud infrastructure using familiar programming languages like Python, TypeScript, or Java. It provides type safety, IDE support, and the ability to create reusable constructs, making it perfect for complex infrastructure requirements and teams that prefer code over YAML.

Learn more at [AWS CDK documentation](https://docs.aws.amazon.com/cdk/){target="_blank"}.

## Basic CDK setup with Python

CDK uses the concept of **Apps**, **Stacks**, and **Constructs** to organize infrastructure. A CDK app contains one or more stacks, and each stack contains constructs that represent AWS resources.

### Project structure

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

### Key CDK concepts for Lambda

| Concept | Description | Lambda Usage |
|---------|-------------|--------------|
| **App** | Root construct, contains stacks | Entry point for your Lambda infrastructure |
| **Stack** | Unit of deployment | Groups related Lambda functions and resources |
| **Construct** | Reusable cloud component | Lambda function, API Gateway, DynamoDB table |
| **Asset** | Local files bundled with deployment | Lambda function code, layers |

### Prerequisites

Before starting, ensure you have:

```bash
--8<-- "examples/build_recipes/cdk/basic/setup-cdk.sh"
```

### Basic implementation

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

### CDK bundling options

CDK provides several ways to handle Lambda function dependencies:

| Method | Description | Best For |
|--------|-------------|----------|
| **Inline bundling** | CDK bundles dependencies automatically | Simple functions with few dependencies |
| **Docker bundling** | Uses Docker for consistent builds | Complex dependencies, cross-platform builds |
| **Pre-built assets** | Upload pre-packaged ZIP files | Custom build processes, CI/CD integration |
| **Lambda Layers** | Separate dependencies from code | Shared dependencies across functions |

### Common CDK commands

```bash
--8<-- "examples/build_recipes/cdk/basic/cdk-commands.sh"
```

## Advanced CDK with multiple stacks

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
