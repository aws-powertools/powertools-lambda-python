---
title: Durable Functions
description: Using Powertools for AWS Lambda (Python) with Lambda Durable Functions
---

<!-- markdownlint-disable MD043 -->

[Lambda Durable Functions](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions.html){target="_blank" rel="nofollow"} enable you to build resilient multi-step workflows that can execute for up to one year. They use checkpoints to track progress and automatically recover from failures through replay.

## Key concepts

| Concept               | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| **Durable execution** | Complete lifecycle of a durable function, from start to completion |
| **Checkpoint**        | Saved state that tracks progress through the workflow              |
| **Replay**            | Re-execution from the beginning, skipping completed checkpoints    |
| **Step**              | Business logic with built-in retries and progress tracking         |
| **Wait**              | Suspend execution without incurring compute charges                |

## How it works

Durable functions use a **checkpoint/replay mechanism**:

1. Your code runs always from the beginning
2. Completed operations are skipped using stored results
3. Execution of new steps continues from where it left off
4. State is automatically managed by the SDK

## Powertools integration

Powertools for AWS Lambda (Python) works seamlessly with Durable Functions. The [Durable Execution SDK](https://github.com/aws/aws-durable-execution-sdk-python){target="_blank" rel="nofollow"} has native integration with Logger via `context.set_logger()`.

???+ note "Found an issue?"
    If you encounter any issues using Powertools for AWS Lambda (Python) with Durable Functions, please [open an issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new?template=bug_report.yml){target="_blank"}.

### Logger

The Durable Execution SDK provides a `context.logger` instance that automatically handles **log deduplication during replays**. You can integrate Logger to get structured JSON logging while keeping the deduplication benefits.

For the best experience, set the Logger on the durable context. This gives you structured JSON logging with automatic log deduplication during replays:

```python hl_lines="5 8 12 15" title="Integrating Logger with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_logger.py"
```

This gives you:

- **JSON structured logging** from Powertools for AWS Lambda (Python)
- **Log deduplication** during replays (logs from completed operations don't repeat)
- **Automatic SDK enrichment** (execution_arn, parent_id, name, attempt)
- **Lambda context injection** (request_id, function_name, etc.)

???+ warning "Direct logger usage"
    If you use the Logger directly (not through `context.logger`), logs will be emitted on every replay:

    ```python
    # Logs will duplicate during replays
    logger.info("This appears on every replay")

    # Use context.logger instead for deduplication
    context.logger.info("This appears only once")
    ```

### Tracer

Tracer works with Durable Functions. Each execution creates trace segments.

???+ note "Trace continuity"
    Due to the replay mechanism, traces may be interleaved. Each execution (including replays) creates separate trace segments. Use the `execution_arn` to correlate traces.

```python hl_lines="5-6 9-10" title="Using Tracer with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_tracer.py"
```

### Metrics

Metrics work with Durable Functions, but be aware that **metrics may be emitted multiple times** during replay if not handled carefully. Emit metrics at workflow completion rather than during intermediate steps to avoid counting replays as new executions.

```python hl_lines="6 9 18 19 20 21" title="Using Metrics with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/best_practice_metrics.py"
```

### Idempotency

The `@idempotent` decorator integrates with Durable Functions and is **replay-aware**. It's useful for protecting the Lambda handler entry point, especially for Event Source Mapping (ESM) invocations like SQS, Kinesis, or DynamoDB Streams.

```python hl_lines="8 15" title="Using Idempotency with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_idempotency.py"
```

???+ warning "Decorator ordering matters"
    The `@idempotent` decorator must be placed **above** `@durable_execution`. This ensures the idempotency check runs first, preventing duplicate executions before the durable workflow begins. Reversing the order would cause the durable execution to start before the idempotency check, defeating its purpose.

**When to use Powertools Idempotency:**

- Protecting the Lambda handler entry point from duplicate invocations
- Methods you don't want to convert into steps but need idempotency guarantees
- Event Source Mapping triggers (SQS, Kinesis, DynamoDB Streams)

**When you don't need it:**

- Steps within a durable function are already idempotent via the checkpoint mechanism

### Parameters

Parameters work normally with Durable Functions.

```python hl_lines="13" title="Using Parameters with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_parameters.py"
```

???+ note "Parameter freshness"
    If the replay or execution happens within the cache TTL on the same execution environment, the parameter value may come from cache. For long-running workflows (hours/days), parameters fetched at the start may become stale. Consider fetching parameters within steps that need the latest values, and customize the caching behavior with `max_age` to control freshness.

## Best practices

### Use Idempotency for ESM triggers

When your durable function is triggered by Event Source Mappings (SQS, Kinesis, DynamoDB Streams), use the `@idempotent` decorator to protect against duplicate invocations.

```python title="Idempotency for ESM"
--8<-- "examples/lambda_features/durable_functions/src/best_practice_idempotency.py"
```

## FAQ

### Do I need Idempotency utility with Durable Functions?

It depends on your use case. Steps within a durable function are already idempotent via checkpoints. However, the `@idempotent` decorator is useful for protecting the Lambda handler entry point, especially for Event Source Mapping invocations (SQS, Kinesis, DynamoDB Streams) where the same event might trigger multiple invocations.

### Why do I see duplicate logs?

If you're using the logger directly instead of `context.logger`, logs will be emitted on every replay. Use `context.set_logger(logger)` and then `context.logger.info()` to get automatic log deduplication.

### How do I correlate logs across replays?

Use the `execution_arn` field that's automatically added to every log entry when using `context.logger`:

```sql
fields @timestamp, @message, execution_arn
| filter execution_arn = "arn:aws:lambda:us-east-1:123456789012:function:my-function:execution-id"
| sort @timestamp asc
```

### Can I use Tracer with Durable Functions?

Yes, but be aware that each execution (including replays) creates separate trace segments. Use the `execution_arn` as a correlation identifier for end-to-end visibility.

### How should I emit metrics without duplicates?

Emit metrics at workflow completion rather than during intermediate steps. This ensures you count completed workflows, not replay attempts.
