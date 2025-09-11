---
title: Performance Optimization
description: Optimize Lambda functions for better performance and reduced costs
---

<!-- markdownlint-disable MD043 -->

Optimize your Lambda functions for better performance, reduced cold start times, and lower costs. These techniques help minimize package size, improve startup speed, and reduce memory usage.

Always validate your function's behavior after applying optimizations to ensure an optimization hasn't introduced any issues with your packages. For example, removal of directories that appear to be unnecessary, such as `docs`, can break some libraries. 

## Reduce cold start times

1. **Minimize package size** by excluding unnecessary files
2. **Use compiled dependencies** when possible
3. **Leverage Lambda SnapStart** or **Provisioned concurrency** when possible

## Build optimization

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
