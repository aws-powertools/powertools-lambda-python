---
title: Lambda Managed Instances
description: Using Powertools for AWS Lambda (Python) with Lambda Managed Instances
---

<!-- markdownlint-disable MD043 -->

[Lambda Managed Instances](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html){target="_blank" rel="nofollow"} enables you to run Lambda functions on Amazon EC2 instances without managing infrastructure. It supports multi-concurrent invocations, EC2 pricing models, and specialized compute options like Graviton4.

## Key differences from Lambda On Demand

| Aspect           | Lambda On Demand                            | Lambda Managed Instances                        |
| ---------------- | ------------------------------------------- | ----------------------------------------------- |
| **Concurrency**  | Single invocation per execution environment | Multiple concurrent invocations per environment |
| **Python model** | One process, one request                    | Multiple processes, one request each            |
| **Pricing**      | Per-request duration                        | EC2-based with Savings Plans support            |
| **Scaling**      | Scale on demand with cold starts            | Async scaling based on CPU                      |
| **Isolation**    | Firecracker microVMs                        | Containers on EC2 Nitro                         |

## How Lambda Python runtime handles concurrency

The **Lambda Python runtime uses multiple processes** for concurrent requests. Each request runs in a separate process, which provides natural isolation between requests.

This means:

- **Each process has its own memory** - global variables are isolated per process
- **`/tmp` directory is shared** across all processes - use caution with file operations

For more details on the isolation model, see [Lambda Managed Instances documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html){target="_blank" rel="nofollow"}.

## Powertools integration

Powertools for AWS Lambda (Python) works seamlessly with Lambda Managed Instances. All utilities are compatible with the multi-process concurrency model used by Python.

### Logger, Tracer, and Metrics

Core utilities work without any changes. Each process has its own instances, so correlation IDs and traces are naturally isolated per request.

???+ note "VPC connectivity required"
    Lambda Managed Instances run in your VPC. Ensure you have [network connectivity](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-networking.html){target="_blank" rel="nofollow"} to send logs to CloudWatch, traces to X-Ray, and metrics to CloudWatch.

```python hl_lines="5 6 7 10 11 12 20 25" title="Using Logger, Tracer, and Metrics with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_tracer.py"
```

### Parameters

Parameters utility works as expected, but be aware that **caching is per-process**.

```python hl_lines="9" title="Using Parameters with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_parameters.py"
```

???+ tip "Cache behavior"
    Since each process has its own cache, you might see more calls to SSM/Secrets Manager during initial warm-up. Once each process has cached the value, subsequent requests within that process use the cache. You can customize the caching behavior with `max_age` to control the TTL.

### Idempotency

Idempotency works without any changes. It uses DynamoDB for state management, which is external to the process.

```python hl_lines="7 10" title="Using Idempotency with Managed Instances"
--8<-- "examples/lambda_features/managed_instances/src/using_idempotency.py"
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
4. **Egress-only Internet Gateway** - IPv6 outbound connectivity without inbound access ([learn more](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html){target="_blank" rel="nofollow"})

See [Networking for Lambda Managed Instances](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-networking.html){target="_blank" rel="nofollow"} for detailed setup instructions.

## FAQ

### Does Powertools for AWS Lambda (Python) work with Lambda Managed Instances?

Yes, all Powertools for AWS Lambda (Python) utilities work seamlessly with Lambda Managed Instances. The multi-process model in Python provides natural isolation between concurrent requests.

### Is my code thread-safe?

Lambda Managed Instances uses **multiple processes**, instead of threads. Each request runs in its own process with isolated memory. If you implement multi-threading within your handler, you are responsible for thread safety.

### Why is my cache not shared between requests?

Each process maintains its own cache (for Parameters, Feature Flags, etc.). This is expected behavior. The cache will warm up independently per process, which may result in slightly more calls to backend services during initial warm-up.

### Can I use global variables?

Yes, but remember they are **per-process**, not shared across concurrent requests. This is actually safer than shared state.

### Do I need to change my existing Powertools for AWS Lambda (Python) code?

No changes are required if you are running Powertools for AWS Lambda (Python) version **3.4.0** or later. Your existing code will work as-is with Lambda Managed Instances.
