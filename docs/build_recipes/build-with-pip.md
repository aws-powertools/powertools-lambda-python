---
title: Build with pip
description: Package Lambda functions using pip - simple and universal
---

<!-- markdownlint-disable MD043 -->

**pip** is Python's standard package installer - simple, reliable, and available everywhere. Perfect for straightforward Lambda functions where you need basic dependency management without complex workflows.

???+ warning "Cross-platform compatibility"
    Always use `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags when building on non-Linux systems to ensure Lambda compatibility. This forces pip to download Linux-compatible wheels instead of compiling from source.

## Basic setup

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

## Advanced pip with Lambda Layers

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

## Cross-platform builds

Build packages for different Lambda architectures using platform-specific wheels:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/pip/build-cross-platform.sh"
    ```

### Platform compatibility

| Platform Flag | Lambda Architecture | Use Case |
|---------------|-------------------|----------|
| `manylinux2014_x86_64` | x86_64 | Standard Lambda functions |
| `manylinux2014_aarch64` | arm64 | Graviton2-based functions (lower cost) |

???+ tip "Architecture selection"
    - **x86_64**: Broader package compatibility, more mature ecosystem
    - **arm64**: Up to 20% better price-performance, newer architecture
