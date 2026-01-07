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
| **Steps**             | Business logic with built-in retries and progress tracking         |
| **Waits**             | Suspend execution without incurring compute charges                |

## How it works

Durable functions use a **checkpoint/replay mechanism**:

1. Your code runs from the beginning
2. Completed operations are skipped using stored results
3. Execution continues from where it left off
4. State is automatically managed by the SDK

## Powertools integration

Powertools for AWS Lambda (Python) works seamlessly with Durable Functions. The [Durable Execution SDK](https://github.com/aws/aws-durable-execution-sdk-python){target="_blank" rel="nofollow"} has native integration with Powertools Logger via `context.set_logger()`.

???+ note "Found an issue?"
    If you encounter any issues using Powertools for AWS with Durable Functions, please [open an issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new?template=bug_report.yml){target="_blank"}.

### Logger

The Durable Execution SDK provides a `context.logger` that automatically handles **log deduplication during replays**. You can integrate Powertools Logger to get structured JSON logging while keeping the deduplication benefits.

#### Using Powertools Logger with context.set_logger

For the best experience, set the Powertools Logger on the durable context:

```python hl_lines="5 10" title="Integrating Powertools Logger with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_logger.py"
```

This gives you:

- **JSON structured logging** from Powertools for AWS
- **Log deduplication** during replays (logs from completed operations don't repeat)
- **Automatic SDK enrichment** (execution_arn, parent_id, name, attempt)
- **Lambda context injection** (request_id, function_name, etc.)

#### Log deduplication during replay

When you use `context.logger`, the SDK prevents duplicate logs during replays:

```python title="Log deduplication behavior"
--8<-- "examples/lambda_features/durable_functions/src/log_deduplication.py"
```

???+ warning "Direct logger usage"
    If you use the Powertools Logger directly (not through `context.logger`), logs will be emitted on every replay:

    ```python
    # Logs will duplicate during replays
    logger.info("This appears on every replay")

    # Use context.logger instead for deduplication
    context.logger.info("This appears only once")
    ```

### Tracer

Tracer works with Durable Functions. Each execution creates trace segments.

???+ note "Trace continuity"
    Due to the replay mechanism, traces may not show a continuous flow. Each execution (including replays) creates separate trace segments. Use the `execution_arn` to correlate traces.

```python hl_lines="5 9" title="Using Tracer with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_tracer.py"
```

### Metrics

Metrics work with Durable Functions, but be aware that **metrics may be emitted multiple times** during replay if not handled carefully.

```python hl_lines="6 10 21" title="Using Metrics with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_metrics.py"
```

???+ tip "Accurate metrics"
    Emit metrics at workflow completion rather than during intermediate steps to avoid counting replays as new executions.

### Idempotency

The `@idempotent` decorator integrates with Durable Functions and is **replay-aware**. It's useful for protecting the Lambda handler entry point, especially for Event Source Mapping (ESM) invocations like SQS, Kinesis, or DynamoDB Streams.

```python hl_lines="9 15" title="Using Idempotency with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_idempotency.py"
```

**When to use Powertools Idempotency:**

- Protecting the Lambda handler entry point from duplicate invocations
- Methods you don't want to convert into steps but need idempotency guarantees
- Event Source Mapping triggers (SQS, Kinesis, DynamoDB Streams)

**When you don't need it:**

- Steps within a durable function are already idempotent via the checkpoint mechanism

### Parser

Parser works with Durable Functions for validating and parsing event payloads.

```python hl_lines="9 14" title="Using Parser with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_parser.py"
```

### Parameters

Parameters work normally with Durable Functions.

```python hl_lines="13" title="Using Parameters with Durable Functions"
--8<-- "examples/lambda_features/durable_functions/src/using_parameters.py"
```

???+ note "Parameter freshness"
    For long-running workflows (hours/days), parameters fetched at the start may become stale. Consider fetching parameters within steps that need the latest values.

## Best practices

### Use context.logger for log deduplication

Always use `context.set_logger()` and `context.logger` instead of using the Powertools Logger directly. This ensures logs are deduplicated during replays.

```python title="Recommended logging pattern"
--8<-- "examples/lambda_features/durable_functions/src/best_practice_logging.py"
```

### Emit metrics at workflow completion

To avoid counting replays as new executions, emit metrics only when the workflow completes successfully.

```python title="Metrics at completion"
--8<-- "examples/lambda_features/durable_functions/src/best_practice_metrics.py"
```

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
