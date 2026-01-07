---
title: Lambda Managed Instances
description: Using Powertools for AWS Lambda (Python) with Lambda Managed Instances
---

<!-- markdownlint-disable MD043 -->

[Lambda Managed Instances](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html){target="_blank" rel="nofollow"} enables you to run Lambda functions on Amazon EC2 instances without managing infrastructure. It supports multi-concurrent invocations, EC2 pricing models, and specialized compute options like Graviton4.

## Key differences from Lambda (default)

| Aspect           | Lambda (default)                            | Lambda Managed Instances                        |
| ---------------- | ------------------------------------------- | ----------------------------------------------- |
| **Concurrency**  | Single invocation per execution environment | Multiple concurrent invocations per environment |
| **Python model** | One process, one request                    | Multiple processes, one request each            |
| **Pricing**      | Per-request duration                        | EC2-based with Savings Plans support            |
| **Scaling**      | Scale on demand with cold starts            | Async scaling based on CPU, no cold starts      |
| **Isolation**    | Firecracker microVMs                        | Containers on EC2 Nitro                         |

## How Lambda Python runtime handles concurrency

Unlike Java or Node.js which use threads, the **Lambda Python runtime uses multiple processes** for concurrent requests. Each request runs in a separate process, which provides natural isolation between requests.

This means:

- **Memory is not shared** between concurrent requests
- **Global variables** are isolated per process
- **`/tmp` directory is shared** across all processes - use caution with file operations

## Isolation model

Lambda Managed Instances use a different isolation model than Lambda (default):

| Layer                  | Lambda (default)                         | Lambda Managed Instances                   |
| ---------------------- | ---------------------------------------- | ------------------------------------------ |
| **Instance level**     | Firecracker microVMs on shared AWS fleet | Containers on EC2 Nitro in your account    |
| **Security boundary**  | Execution environment                    | Capacity provider                          |
| **Function isolation** | Strong isolation via microVMs            | Container-based isolation within instances |

**Capacity providers** serve as the security boundary. Functions within the same capacity provider share the underlying EC2 instances. For workloads requiring strong isolation between functions, use separate capacity providers.

For Python specifically, the multi-process model adds another layer of isolation - each concurrent request runs in its own process with separate memory space.

## Powertools integration

Powertools for AWS Lambda (Python) works seamlessly with Lambda Managed Instances. All utilities are compatible with the multi-process concurrency model used by Python.

### Logger

Logger works without any changes. Each process has its own logger instance.

```python hl_lines="4 7" title="Using Logger with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_logger.py"
```

### Tracer

Tracer works without any changes. X-Ray traces are captured per request.

???+ note "VPC connectivity required"
    Lambda Managed Instances run in your VPC. Ensure you have [network connectivity](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-networking.html){target="_blank" rel="nofollow"} to send traces to X-Ray.

```python hl_lines="4 8 12" title="Using Tracer with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_tracer.py"
```

### Metrics

Metrics work without any changes. Each process flushes metrics independently.

???+ note "VPC connectivity required"
    Ensure you have [network connectivity](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-networking.html){target="_blank" rel="nofollow"} to send metrics to CloudWatch.

```python hl_lines="5 9 12" title="Using Metrics with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_metrics.py"
```

### Parameters

Parameters utility works correctly, but be aware that **cache is per-process**.

```python hl_lines="9" title="Using Parameters with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_parameters.py"
```

???+ tip "Cache behavior"
    Since each process has its own cache, you might see more calls to SSM/Secrets Manager during initial warm-up. Once each process has cached the value, subsequent requests within that process use the cache.

### Idempotency

Idempotency works without any changes. It uses DynamoDB for state management, which is external to the process.

```python hl_lines="7 10" title="Using Idempotency with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_idempotency.py"
```

### Batch Processing

Batch Processing works without any changes. Each batch is processed within a single process.

```python hl_lines="5 8 14" title="Using Batch Processing with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_batch.py"
```

???+ note "Other utilities"
    All other Powertools for AWS utilities (Feature Flags, Validation, Parser, Data Masking, etc.) work without any changes. If you encounter any issues, please [open an issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new?template=bug_report.yml){target="_blank"}.

## Working with shared resources

### The `/tmp` directory

The `/tmp` directory is **shared across all processes** in the execution environment. Use caution when writing files.

```python title="Safe file handling with unique names"
--8<-- "examples/lambda_features/managed_instances/src/tmp_file_handling.py"
```

### Database connections

Since each process is independent, connection pooling behaves differently than in threaded runtimes.

```python title="Database connections per process"
--8<-- "examples/lambda_features/managed_instances/src/database_connections.py"
```

## VPC connectivity

Lambda Managed Instances require VPC configuration for:

- Sending logs to CloudWatch Logs
- Sending traces to X-Ray
- Accessing AWS services (SSM, Secrets Manager, DynamoDB, etc.)

Configure connectivity using one of these options:

1. **VPC Endpoints** - Private connectivity without internet access
2. **NAT Gateway** - Internet access from private subnets
3. **Public subnet with Internet Gateway** - Direct internet access

See [Networking for Lambda Managed Instances](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-networking.html){target="_blank" rel="nofollow"} for detailed setup instructions.

## FAQ

### Does Powertools for AWS Lambda (Python) work with Lambda Managed Instances?

Yes, all Powertools for AWS utilities work seamlessly with Lambda Managed Instances. The multi-process model in Python provides natural isolation between concurrent requests.

### Is my code thread-safe?

For Python, you don't need to worry about thread safety because Lambda Managed Instances uses **multiple processes**, not threads. Each request runs in its own process with isolated memory.

### Why is my cache not shared between requests?

Each process maintains its own cache (for Parameters, Feature Flags, etc.). This is expected behavior. The cache will warm up independently per process, which may result in slightly more calls to backend services during initial warm-up.

### Can I use global variables?

Yes, but remember they are **per-process**, not shared across concurrent requests. This is actually safer than shared state.

### How should I handle files in `/tmp`?

Use unique file names (include request ID or UUID) to avoid conflicts between concurrent requests. Always clean up files after use to avoid filling the shared `/tmp` directory.

### Do I need to change my existing Powertools for AWS code?

No changes are required. Your existing code will work as-is with Lambda Managed Instances.
