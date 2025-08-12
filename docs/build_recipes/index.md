---
title: Build Recipes
description: Lambda function packaging recipes with Powertools for AWS
---

<!-- markdownlint-disable MD043 MD013 -->

As the Python ecosystem continues to evolve with new package managers, build tools, and dependency resolution strategies, choosing the right approach for Lambda deployments has become increasingly complex. Modern Python applications often involve compiled extensions, platform-specific dependencies, and sophisticated toolchains that require careful consideration for serverless environments.

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

## Guide sections

This guide is organized into focused sections to help you find exactly what you need:

### 📚 Fundamentals

* **[Getting started](getting-started.md)** - Prerequisites, tool selection, and basic setup
* **[Cross-platform builds](cross-platform.md)** - Handle architecture differences and compiled dependencies

### 🔧 Build tools

* **[Build with pip](build-with-pip.md)** - Simple, universal package management
* **[Build with Poetry](build-with-poetry.md)** - Modern dependency management with lock files
* **[Build with uv](build-with-uv.md)** - Extremely fast Rust-based package manager
* **[Build with SAM](build-with-sam.md)** - AWS Serverless Application Model integration
* **[Build with CDK](build-with-cdk.md)** - Infrastructure as code with type safety
* **[Build with Pants](build-with-pants.md)** - Advanced build system for monorepos

### ⚡ Advanced topics

* **[Performance optimization](performance-optimization.md)** - Reduce cold starts and package size
* **[CI/CD integration](cicd-integration.md)** - Automate builds with GitHub Actions and CodeBuild
* **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
