---
name: building-lambda-functions-with-powertools-python
description: Build AWS Lambda functions in Python with Powertools for AWS Lambda (Python), structured logging, tracing, metrics, REST/GraphQL/Bedrock event handlers, idempotency, batch processing, parameters, validation, parsing and more. Use when the user mentions Powertools, imports aws_lambda_powertools, or asks for a Lambda handler with logging, tracing, metrics, API routing, idempotency, batch or SQS/Kinesis/DynamoDB Streams processing, parameter or secret retrieval, event parsing or validation.
license: MIT-0
compatibility: Python 3.10 to 3.14, AWS Lambda
metadata:
  author: aws-powertools
  source: https://github.com/aws-powertools/powertools-lambda-python
---

<!-- markdownlint-disable MD013 MD041 -->

# Building Lambda functions with Powertools for AWS Lambda (Python)

Powertools for AWS Lambda (Python) is a toolkit of independent utilities for Lambda functions: Logger, Tracer, Metrics, Event Handler, Idempotency, Batch Processing, Parameters, Parser, Validation, Feature Flags, Data Masking, Circuit Breaker, Kafka, Streaming and others. Each utility is designed around the Lambda execution model and adds as little as possible to cold start.

## When to use this skill

- The user mentions Powertools, or code imports `aws_lambda_powertools`
- The user asks for a Lambda handler with structured logging, X-Ray tracing or CloudWatch metrics
- The user wants to route API Gateway, ALB, Function URL, VPC Lattice, AppSync or Bedrock Agents requests inside one function
- The user needs idempotent handlers, partial batch failure handling for SQS, Kinesis or DynamoDB Streams, cached parameters or secrets, typed access to event payloads, or input validation

Do not use it for non-Lambda web frameworks, or for the Powertools libraries of other languages (TypeScript, Java, .NET).

## Before writing code

- Read the reference for the utility you are about to use from [`references/`](references/). Each file is the full documentation page with every example inlined; open it and look for the section you need instead of reading the whole file.
- Check the installed version before relying on a feature: `uv run python -c "import aws_lambda_powertools; print(aws_lambda_powertools.__version__)"`. The references describe the latest release.
- Prefer the public Lambda layer or the `aws-lambda-powertools` package with the extra the utility needs (`[tracer]`, `[parser]`, `[validation]`, `[datamasking]`, `[redis]`, `[valkey]`, `[jwt]`, `[oauth2]`, `[all]`). See [references/installation.md](references/installation.md).

## Essential patterns

### Logger, Tracer and Metrics on a handler

```python
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()      # service name from POWERTOOLS_SERVICE_NAME
tracer = Tracer()      # needs the [tracer] extra or the layer, and Active tracing on the function
metrics = Metrics()    # namespace from POWERTOOLS_METRICS_NAMESPACE


@tracer.capture_method
def collect_payment(charge_id: str) -> dict:
    return {"charge_id": charge_id, "status": "collected"}


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Collecting payment", extra={"charge_id": event["charge_id"]})
    metrics.add_metric(name="SuccessfulPayments", unit=MetricUnit.Count, value=1)
    return collect_payment(event["charge_id"])
```

Create the three objects once at module level and reuse them across invocations. Use `logger.append_keys(...)` for keys that must appear in every following log line, `extra=` for one line only. `inject_lambda_context` adds cold start, function name, memory, ARN and request id; add `correlation_id_path=correlation_paths.API_GATEWAY_REST` (or another path from `aws_lambda_powertools.logging.correlation_paths`) to pick up a correlation id from the event.

### REST API with Event Handler

```python
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)


@app.get("/todos/<todo_id>")
@tracer.capture_method
def get_todo(todo_id: int) -> dict:
    todo = find_todo(todo_id)
    if todo is None:
        raise NotFoundError(f"todo {todo_id} not found")
    return todo


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
```

Pick the resolver that matches the trigger: `APIGatewayRestResolver` (REST API), `APIGatewayHttpResolver` (HTTP API), `ALBResolver`, `LambdaFunctionUrlResolver`, `VPCLatticeV2Resolver`, `AppSyncResolver`, `AppSyncEventsResolver`, `BedrockAgentResolver`. With `enable_validation=True`, type hints on path, query, header and body parameters are validated and a 422 is returned on failure; `app.get_openapi_json_schema()` and `app.enable_swagger()` come from the same annotations. Split large APIs with `Router` and `app.include_router(router, prefix="/v1")`. See [references/event-handler-rest-http.md](references/event-handler-rest-http.md) and [references/event-handler-openapi.md](references/event-handler-openapi.md).

### Idempotent handler

```python
import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name=os.environ["IDEMPOTENCY_TABLE"])
config = IdempotencyConfig(event_key_jmespath="order_id", expires_after_seconds=3600)


@idempotent(persistence_store=persistence_layer, config=config)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return create_order(event)
```

The table needs a string partition key named `id` and TTL on `expiration`. Use `event_key_jmespath` so the key is the business identifier, not the whole event. For a function inside the handler use `@idempotent_function(data_keyword_argument="order", ...)`. Create one persistence layer instance per decorated function; sharing one instance between two decorated functions mixes their records. Redis and Valkey are supported through `CachePersistenceLayer`. See [references/idempotency.md](references/idempotency.md).

### Partial batch failures for SQS, Kinesis and DynamoDB Streams

```python
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
processor = BatchProcessor(event_type=EventType.SQS)


def record_handler(record: SQSRecord) -> None:
    payload = record.json_body  # record.body for plain strings
    logger.info(payload)


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
```

The event source mapping must have `ReportBatchItemFailures` enabled, otherwise the whole batch is retried. Use `EventType.KinesisDataStreams` or `EventType.DynamoDBStreams` for the other sources, `SqsFifoPartialProcessor` for FIFO queues, and `AsyncBatchProcessor` with `async_process_partial_response` for async record handlers. Raise from `record_handler` to mark a record as failed; do not catch and swallow. See [references/batch-processing.md](references/batch-processing.md).

### Parameters and secrets

```python
from aws_lambda_powertools.utilities import parameters

api_key = parameters.get_parameter("/payments/api-key", decrypt=True, max_age=300)
settings = parameters.get_parameter("/payments/settings", transform="json")
db_secret = parameters.get_secret("payments/db", transform="json")
```

Values are cached for `max_age` seconds (5 seconds by default) inside the execution environment; call these inside the handler, not at import time, unless the value never changes. `get_parameters` fetches a path recursively, `get_parameters_by_name` fetches a batch, `get_app_config` reads AppConfig. Use `SSMProvider`, `SecretsProvider`, `AppConfigProvider` or `DynamoDBProvider` when you need a custom client or region. See [references/parameters.md](references/parameters.md).

### Typed events and parsing

```python
from aws_lambda_powertools.utilities.data_classes import event_source, S3Event
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=S3Event)
def lambda_handler(event: S3Event, context: LambdaContext) -> None:
    for record in event.records:
        print(record.s3.bucket.name, record.s3.get_object.key)
```

Event source data classes give typed, dict-backed access without a dependency. When you need validation of the payload, use the Parser with Pydantic: `@event_parser(model=MyModel, envelope=envelopes.SqsEnvelope)` validates each record body against `MyModel`. Both have a class or model for every common event source; see [references/event-source-data-classes.md](references/event-source-data-classes.md) and [references/parser.md](references/parser.md).

## Rules the project follows, and your code should too

These come from the project's architecture decision records.

- **Lambda first.** No background threads or timers, no state that assumes the process survives the invocation. Anything shared between invocations lives in the execution environment and may be touched by concurrent invocations on Lambda Managed Instances. See [references/lambda-managed-instances.md](references/lambda-managed-instances.md).
- **Cold start is a budget.** Import `aws_lambda_powertools` utilities at module level, but import heavy optional libraries (Pydantic models, boto3 clients) where they are used, and create clients once at module level, never per invocation.
- **The layer never ships boto3.** The Lambda runtime provides `boto3` and `botocore`; do not add them to the deployment package or the layer, and do not pin `urllib3` yourself.
- **One extra per feature.** Install only the extra you use. `[all]` is for development.
- **Use the public API.** Import from `aws_lambda_powertools`, `aws_lambda_powertools.event_handler`, `aws_lambda_powertools.utilities.<utility>` and the `.exceptions`/`.types` modules. Names starting with `_` are internal and change without notice.
- **Environment variables over code** for service name, namespace, log level, sampling and metric flags: `POWERTOOLS_SERVICE_NAME`, `POWERTOOLS_METRICS_NAMESPACE`, `POWERTOOLS_LOG_LEVEL`, `POWERTOOLS_LOGGER_SAMPLE_RATE`, `POWERTOOLS_LOGGER_LOG_EVENT`, `POWERTOOLS_TRACE_DISABLED`, `POWERTOOLS_METRICS_DISABLED`, `POWERTOOLS_IDEMPOTENCY_DISABLED`.

## Testing the functions you write

- Decorators that read the Lambda context work with any object exposing `function_name`, `memory_limit_in_mb`, `invoked_function_arn` and `aws_request_id`; build a small dataclass in tests.
- Set `POWERTOOLS_TRACE_DISABLED=1` and `POWERTOOLS_METRICS_DISABLED=1` in unit tests so Tracer and Metrics do not try to reach X-Ray or print EMF.
- Event Handler apps are plain callables: `app.resolve(event, context)` with a dict from the AWS sample events, or `HttpResolverLocal` to run them under uvicorn locally.
- Idempotency and Batch tests can use the in-memory or stubbed layers shown in each reference; the real services are only needed for integration tests.

## Reference files

| Topic | File |
| --- | --- |
| Installation, extras, Lambda layer ARNs | [references/installation.md](references/installation.md) |
| Logger | [references/logger.md](references/logger.md) |
| Tracer | [references/tracer.md](references/tracer.md) |
| Metrics, Datadog provider | [references/metrics.md](references/metrics.md) |
| Event Handler: REST, HTTP, ALB, Function URL, VPC Lattice | [references/event-handler-rest-http.md](references/event-handler-rest-http.md) |
| Event Handler: OpenAPI schema, validation, Swagger UI | [references/event-handler-openapi.md](references/event-handler-openapi.md) |
| Event Handler: AppSync GraphQL resolvers | [references/event-handler-appsync.md](references/event-handler-appsync.md) |
| Event Handler: AppSync Events | [references/event-handler-appsync-events.md](references/event-handler-appsync-events.md) |
| Event Handler: Bedrock Agents | [references/event-handler-bedrock-agents.md](references/event-handler-bedrock-agents.md) |
| Parameters and secrets | [references/parameters.md](references/parameters.md) |
| Auth (alpha): JWT verification, OAuth2 client | [references/auth-jwt-oauth2.md](references/auth-jwt-oauth2.md) |
| Batch processing | [references/batch-processing.md](references/batch-processing.md) |
| Kafka consumer | [references/kafka.md](references/kafka.md) |
| Typing | [references/typing.md](references/typing.md) |
| Validation (JSON Schema) | [references/validation.md](references/validation.md) |
| Event source data classes | [references/event-source-data-classes.md](references/event-source-data-classes.md) |
| Parser (Pydantic) | [references/parser.md](references/parser.md) |
| Idempotency | [references/idempotency.md](references/idempotency.md) |
| Circuit Breaker | [references/circuit-breaker.md](references/circuit-breaker.md) |
| Data Masking | [references/data-masking.md](references/data-masking.md) |
| Feature Flags | [references/feature-flags.md](references/feature-flags.md) |
| Metadata (Lambda Metadata Endpoint) | [references/metadata.md](references/metadata.md) |
| Streaming | [references/streaming.md](references/streaming.md) |
| Middleware factory | [references/middleware-factory.md](references/middleware-factory.md) |
| JMESPath functions | [references/jmespath-functions.md](references/jmespath-functions.md) |
| Lambda Managed Instances | [references/lambda-managed-instances.md](references/lambda-managed-instances.md) |
| Durable Functions | [references/durable-functions.md](references/durable-functions.md) |

The references are generated from the documentation by `scripts/build_agent_skill_references.py`; the documentation at <https://docs.powertools.aws.dev/lambda/python/latest/> is the source of truth.
