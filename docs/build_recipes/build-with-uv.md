---
title: Build with uv
description: Package Lambda functions using uv for extremely fast builds
---

<!-- markdownlint-disable MD043 -->

**uv** is an extremely fast Python package manager written in Rust, designed as a drop-in replacement for pip and pip-tools. It offers 10-100x faster dependency resolution and installation, making it ideal for CI/CD pipelines and performance-critical builds. Learn more at [docs.astral.sh/uv/](https://docs.astral.sh/uv/){target="_blank"}.

???+ warning "Cross-platform compatibility"
    Use `uv pip install` with `--platform manylinux2014_x86_64` and `--only-binary=:all:` flags when building on non-Linux systems. This ensures Lambda-compatible wheels are downloaded instead of compiling from source.

## Setup uv

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

## uv with lock file for reproducible builds

Generate and use lock files to ensure exact dependency versions across all environments and team members.

=== "build-uv-locked.sh"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv-locked.sh"
    ```

## Cross-platform builds with uv

Build packages for different Lambda architectures using uv's platform-specific installation:

=== "Multi-architecture build"

    ```bash
    --8<-- "examples/build_recipes/uv/build-uv-cross-platform.sh"
    ```

### uv performance advantages

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
