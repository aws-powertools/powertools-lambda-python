---
title: CI/CD Integration
description: Automate Lambda function builds and deployments
---

<!-- markdownlint-disable MD043 -->

Automate your Lambda function builds and deployments using popular CI/CD platforms. These examples show how to build and deploy Lambda functions with Powertools for AWS with proper cross-platform compatibility and deploy them reliably.

## GitHub Actions

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

## AWS CodeBuild

**AWS CodeBuild** is a fully managed build service that compiles source code, runs tests, and produces deployment packages. It integrates seamlessly with other AWS services and provides consistent build environments with automatic scaling.

=== "Basic CodeBuild Configuration"

    ```yaml
    --8<-- "examples/build_recipes/cicd/codebuild/buildspec.yml"
    ```

## Best Practices for CI/CD

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
