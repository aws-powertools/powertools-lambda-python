---
title: Troubleshooting
description: Common issues and solutions when building Lambda packages
---

<!-- markdownlint-disable MD043 -->

## Common issues and solutions

This section covers the most frequent issues encountered when building and deploying Lambda functions with Powertools for AWS Lambda (Python). Each issue includes symptoms to help identify the problem and practical solutions with working code examples.

### Package size issues

???+ warning "Lambda deployment package too large (>50MB unzipped)"
    **Symptoms:**
    - `RequestEntityTooLargeException` during deployment
    - Slow cold starts
    - High memory usage

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/optimize-package-size.sh"
    ```

### Import and runtime errors

???+ error "ModuleNotFoundError or ImportError"
    **Symptoms:**
    - `ModuleNotFoundError: No module named 'aws_lambda_powertools'`
    - Function fails at runtime with import errors

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/debug-import-errors.sh"
    ```

???+ error "Architecture mismatch errors"
    **Symptoms:**
    - `ImportError: /lib64/libc.so.6: version GLIBC_2.XX not found`
    - Compiled extensions fail to load

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/fix-architecture-mismatch.sh"
    ```

### Performance issues

???+ warning "Slow cold starts"
    **Symptoms:**
    - High initialization duration in CloudWatch logs
    - Timeouts on first invocation

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/optimize-cold-starts.sh"
    ```

### Build and deployment issues

???+ error "Build inconsistencies across environments"
    **Symptoms:**
    - Works locally but fails in CI/CD
    - Different behavior between team members

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/fix-build-inconsistencies.sh"
    ```

???+ error "Layer compatibility issues"
    **Symptoms:**
    - Layer not found or incompatible runtime
    - Version conflicts between layer and function dependencies

    **Solutions:**
    ```bash
    --8<-- "examples/build_recipes/troubleshooting/fix-layer-compatibility.sh"
    ```
