---
title: Homepage
description: Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 MD013 -->

Powertools for AWS Lambda (Python) is a developer toolkit to implement Serverless best practices and increase developer velocity.

!!! tip "Ready to use Powertools for AWS Lambda? Jump to [Installation](./getting-started/install.md)."

<div class="grid cards" markdown>

- :material-battery-charging:{ .lg .middle } __Features__

    ---

    Adopt one, a few, or all industry practices. __Progressively__.

    [:octicons-arrow-right-24: All features](#features)

- :material-download:{ .lg .middle } __Installation__

    ---

    Install via pip, Lambda Layers, or SAR.

    [:octicons-arrow-right-24: Get started](./getting-started/install.md)

- :heart:{ .lg .middle } __Support this project__

    ---

    Become a public reference, share your work, join the community.

    [:octicons-arrow-right-24: Support](#support-powertools-for-aws-lambda-python)

- :material-file-code:{ .lg .middle } __Other languages__

    ---

    Powertools is also available in other languages.

    [:octicons-arrow-right-24: Java](https://docs.powertools.aws.dev/lambda/java/){target="_blank"}, [TypeScript](https://docs.powertools.aws.dev/lambda/typescript/latest/){target="_blank"}, [.NET](https://docs.powertools.aws.dev/lambda/dotnet/){target="_blank"}

</div>

## Features

| Utility | Description |
| ------- | ----------- |
| [Tracer](./core/tracer.md) | Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions |
| [Logger](./core/logger.md) | Structured logging made easier, and target to enrich structured logging with key Lambda context details |
| [Metrics](./core/metrics.md) | Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF) |
| [Event Handler](./core/event_handler/api_gateway.md) | Event handler for API Gateway, ALB, Lambda Function URL, VPC Lattice, AppSync, and Bedrock Agents |
| [Parameters](./utilities/parameters.md) | Retrieve and cache parameter values from Parameter Store, Secrets Manager, AppConfig, or DynamoDB |
| [Parser](./utilities/parser.md) | Data parsing and deep validation using Pydantic |
| [Batch Processing](./utilities/batch.md) | Handle partial failures for SQS, Kinesis Data Streams, and DynamoDB Streams |
| [Idempotency](./utilities/idempotency.md) | Make your Lambda functions idempotent and prevent duplicate execution |
| [Feature Flags](./utilities/feature_flags.md) | A simple rule engine to evaluate when features should be enabled |
| [Validation](./utilities/validation.md) | JSON Schema validator for inbound events and responses |
| [Data Masking](./utilities/data_masking.md) | Protect confidential data with easy removal or encryption |
| [Streaming](./utilities/streaming.md) | Stream datasets larger than available memory |
| [Middleware Factory](./utilities/middleware_factory.md) | Create your own middleware to run logic before and after each Lambda invocation |
| [Typing](./utilities/typing.md) | Static typing classes to speedup development in your IDE |
| [Event Source Data Classes](./utilities/data_classes.md) | Data classes describing the schema of common Lambda event triggers |
| [JMESPath Functions](./utilities/jmespath_functions.md) | Built-in JMESPath functions to deserialize common encoded JSON payloads |
| [Kafka](./utilities/kafka.md) | Deserialize and validate Kafka events with support for Avro, Protocol Buffers, and JSON Schema |

## Examples

You can find examples in the [examples directory](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples){target="_blank"} and a quick start using SAM CLI:

```bash
sam init --app-template hello-world-powertools-python --name sam-app --package-type Zip --runtime python3.13 --no-tracing
```

For a more complete example, check the [Powertools for AWS workshop](https://catalog.workshops.aws/serverless-powertools){target="_blank"}.

## Environment variables

???+ info
    Explicit parameters take precedence over environment variables.

| Environment variable | Description | Utility | Default |
| -------------------- | ----------- | ------- | ------- |
| `POWERTOOLS_SERVICE_NAME` | Service name for tracing, metrics, and logging | All | `service_undefined` |
| `POWERTOOLS_LOG_LEVEL` | Sets logging level | [Logger](./core/logger.md) | `INFO` |
| `POWERTOOLS_LOGGER_LOG_EVENT` | Logs incoming event | [Logger](./core/logger.md) | `false` |
| `POWERTOOLS_LOGGER_SAMPLE_RATE` | Debug log sampling | [Logger](./core/logger.md) | `0` |
| `POWERTOOLS_METRICS_NAMESPACE` | Namespace for metrics | [Metrics](./core/metrics.md) | `None` |
| `POWERTOOLS_METRICS_DISABLED` | Disables metrics emission | [Metrics](./core/metrics.md) | `false` |
| `POWERTOOLS_TRACE_DISABLED` | Disables tracing | [Tracer](./core/tracer.md) | `false` |
| `POWERTOOLS_TRACER_CAPTURE_RESPONSE` | Captures return as metadata | [Tracer](./core/tracer.md) | `true` |
| `POWERTOOLS_TRACER_CAPTURE_ERROR` | Captures exception as metadata | [Tracer](./core/tracer.md) | `true` |
| `POWERTOOLS_PARAMETERS_MAX_AGE` | Cache TTL in seconds | [Parameters](./utilities/parameters.md) | `5` |
| `POWERTOOLS_PARAMETERS_SSM_DECRYPT` | Decrypt SSM parameters | [Parameters](./utilities/parameters.md) | `false` |
| `POWERTOOLS_DEV` | Increases verbosity for development | Multiple | `false` |
| `POWERTOOLS_DEBUG` | Enables debug logging for Powertools | All | `false` |

### Development mode

When `POWERTOOLS_DEV` is set to `true`, it enables development-friendly settings:

| Utility | Effect |
| ------- | ------ |
| Logger | Increases JSON indentation to 4 for readability |
| Event Handler | Enables full traceback errors and CORS in dev mode |
| Tracer | Disables tracing in non-Lambda environments |
| Metrics | Disables metrics emission (can be overridden) |

## Support Powertools for AWS Lambda (Python)

<div class="grid cards" markdown>

- :heart:{ .lg .middle } __Become a public reference__

    ---

    Add your company name and logo on our [landing page](https://powertools.aws.dev){target="_blank"}.

    [:octicons-arrow-right-24: GitHub Issue template](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E){target="_blank"}

- :mega:{ .lg .middle } __Share your work__

    ---

    Blog posts, videos, and sample projects about Powertools.

    [:octicons-arrow-right-24: GitHub Issue template](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=community-content&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E){target="_blank"}

- :partying_face:{ .lg .middle } __Join the community__

    ---

    Connect, ask questions, and share what features you use.

    [:octicons-arrow-right-24: Discord invite](https://discord.gg/B8zZKbbyET){target="_blank"}

</div>

## Tenets

These are our core principles to guide our decision making.

- __AWS Lambda only__. We optimize for AWS Lambda function environments and supported runtimes only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
- __Eases the adoption of best practices__. The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
- __Keep it lean__. Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time.
- __We strive for backwards compatibility__. New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
- __We work backwards from the community__. We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs).
- __Progressive__. Utilities are designed to be incrementally adoptable for customers at any stage of their Serverless journey. They follow language idioms and their community's common practices.
