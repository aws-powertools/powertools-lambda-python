---
title: Build with Poetry
description: Package Lambda functions using Poetry for modern dependency management
---

<!-- markdownlint-disable MD043 -->

**Poetry** is a modern Python dependency manager that handles packaging, dependency resolution, and virtual environments. It uses lock files to ensure reproducible builds and provides excellent developer experience with semantic versioning.

???+ warning "Cross-platform compatibility"
    When building on non-Linux systems, use `pip install` with `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags after exporting requirements from Poetry. This ensures Lambda-compatible wheels are installed.

## Setup Poetry

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

### Alternative: Poetry-only build (not recommended for production)

For development or when cross-platform compatibility is not a concern:

=== "build-poetry-native.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-poetry-native.sh"
    ```

## Cross-platform builds with Poetry

Build packages for different Lambda architectures by combining Poetry's dependency management with pip's platform-specific installation:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-poetry-cross-platform.sh"
    ```

### Poetry build methods comparison

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

## Poetry with Docker for consistent builds

Use Docker to ensure consistent builds across different development environments and avoid platform-specific dependency issues.

=== "Dockerfile"

    ```dockerfile title="Dockerfile.poetry"
    --8<-- "examples/build_recipes/poetry/Dockerfile.poetry"
    ```

=== "build-with-poetry-docker.sh"

    ```bash
    --8<-- "examples/build_recipes/poetry/build-with-poetry-docker.sh"
    ```
