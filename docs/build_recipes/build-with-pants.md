---
title: Build with Pants
description: Package Lambda functions using Pants for monorepos and complex projects
---

<!-- markdownlint-disable MD043 -->

**Pants** is a powerful build system designed for large codebases and monorepos. It provides incremental builds, dependency inference, and advanced caching mechanisms. Ideal for organizations with complex Python projects that need fine-grained build control and optimization.

## Setup

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

## Advanced Pants with multiple targets

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
