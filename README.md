<!-- markdownlint-disable MD013 MD041 MD043  -->
# Powertools for AWS Lambda (Python)

[![Build](https://github.com/aws-powertools/powertools-lambda-python/actions/workflows/quality_check.yml/badge.svg)](https://github.com/aws-powertools/powertools-lambda-python/actions/workflows/quality_check.yml)
[![codecov.io](https://codecov.io/github/aws-powertools/powertools-lambda-python/branch/develop/graphs/badge.svg)](https://app.codecov.io/gh/aws-powertools/powertools-lambda-python)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=%203.10|%203.11|%203.12|%203.13|%203.14&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools) [![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/aws-powertools/powertools-lambda-python/badge)](https://scorecard.dev/viewer/?uri=github.com/aws-powertools/powertools-lambda-python)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-7289da.svg)](https://discord.gg/B8zZKbbyET)

Powertools for AWS Lambda (Python) is a developer toolkit for AWS Lambda: structured logging, tracing, metrics, event handlers for API Gateway, AppSync and Bedrock Agents, idempotency, batch processing, parameters, validation, and more. Each utility is independent, follows the Lambda execution model, and is designed to add as little as possible to your cold start.

Also available in [TypeScript](https://github.com/aws-powertools/powertools-lambda-typescript), [Java](https://github.com/aws-powertools/powertools-lambda-java), and [.NET](https://github.com/aws-powertools/powertools-lambda-dotnet).

[📜 Documentation](https://docs.powertools.aws.dev/lambda/python/) | [🐍 PyPI](https://pypi.org/project/aws-lambda-powertools/) | [🎓 Workshop](https://s12d.com/powertools-for-aws-lambda-workshop) | [🗺️ Roadmap](https://docs.powertools.aws.dev/lambda/python/latest/roadmap/) | [📝 Changelog](https://docs.powertools.aws.dev/lambda/python/latest/changelog/)

![hero-image](https://user-images.githubusercontent.com/3340292/198254617-d0fdb672-86a6-4988-8a40-adf437135e0a.png)

## Installation

```bash
pip install aws-lambda-powertools
# or
uv add aws-lambda-powertools
```

Or use the [public Lambda layer](https://docs.powertools.aws.dev/lambda/python/latest/getting-started/install/#lambda-layer), published for every supported Python version on `x86_64` and `arm64`. Some utilities need an extra, for example `aws-lambda-powertools[parser]` for Pydantic; the [installation guide](https://docs.powertools.aws.dev/lambda/python/latest/getting-started/install/) lists them.

Building with a coding agent? Install the [Powertools skill](https://docs.powertools.aws.dev/lambda/python/latest/getting-started/coding-agent-skills/) so Claude Code, Codex, Cursor or Gemini CLI work from the current documentation and examples: `npx skills add aws-powertools/powertools-lambda-python`.

## Features

### Core

* **[Logger](https://docs.powertools.aws.dev/lambda/python/latest/core/logger/)** - Structured JSON logging with Lambda context, correlation IDs, sampling and log buffering
* **[Tracer](https://docs.powertools.aws.dev/lambda/python/latest/core/tracer/)** - Decorators and utilities to trace Lambda function handlers and sync or async functions with AWS X-Ray
* **[Metrics](https://docs.powertools.aws.dev/lambda/python/latest/core/metrics/)** - Custom metrics created asynchronously via CloudWatch Embedded Metric Format (EMF), with a [Datadog](https://docs.powertools.aws.dev/lambda/python/latest/core/metrics/datadog/) provider
* **[Event Handler: REST and HTTP APIs](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/)** - Routing, validation and middleware for API Gateway, ALB, Lambda Function URL and VPC Lattice, with [OpenAPI schema generation and Swagger UI](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/openapi/)
* **[Event Handler: AppSync](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/appsync/)** - Resolvers for AppSync Direct Lambda Resolvers and Amplify GraphQL Transformer functions
* **[Event Handler: AppSync Events](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/appsync_events/)** - Handlers for AppSync Events real-time WebSocket APIs with pub/sub
* **[Event Handler: Bedrock Agents](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/bedrock_agents/)** - Build Amazon Bedrock Agents action groups with automatically generated OpenAPI schemas

### Utilities

* **[Parameters](https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/)** - Retrieve and cache parameter values from Parameter Store, Secrets Manager, AppConfig or DynamoDB
* **[Idempotency](https://docs.powertools.aws.dev/lambda/python/latest/utilities/idempotency/)** - Make your Lambda functions idempotent and safe to retry, with DynamoDB, Redis or Valkey persistence
* **[Batch processing](https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/)** - Handle partial failures for SQS, Kinesis Data Streams and DynamoDB Streams batches
* **[Circuit Breaker](https://docs.powertools.aws.dev/lambda/python/latest/utilities/circuit_breaker/)** - Stop calling a failing downstream and recover with a single probe across execution environments
* **[Kafka](https://docs.powertools.aws.dev/lambda/python/latest/utilities/kafka/)** - Deserialize and validate Kafka events with Avro, Protocol Buffers and JSON Schema
* **[Event source data classes](https://docs.powertools.aws.dev/lambda/python/latest/utilities/data_classes/)** - Typed access to the payloads of common Lambda event sources
* **[Parser](https://docs.powertools.aws.dev/lambda/python/latest/utilities/parser/)** - Data parsing and deep validation with Pydantic, with models and envelopes for common event sources
* **[Validation](https://docs.powertools.aws.dev/lambda/python/latest/utilities/validation/)** - JSON Schema validation for inbound events and responses
* **[Feature Flags](https://docs.powertools.aws.dev/lambda/python/latest/utilities/feature_flags/)** - A rule engine to evaluate when one or more features should be enabled depending on the input
* **[Data Masking](https://docs.powertools.aws.dev/lambda/python/latest/utilities/data_masking/)** - Erase or encrypt confidential fields in your data with AWS KMS
* **[Auth (alpha)](https://docs.powertools.aws.dev/lambda/python/latest/utilities/auth/)** - JWT access-token verification and an [OAuth2 client-credentials client](https://docs.powertools.aws.dev/lambda/python/latest/utilities/oauth2/) for downstream APIs
* **[Streaming](https://docs.powertools.aws.dev/lambda/python/latest/utilities/streaming/)** - Stream S3 objects larger than the available memory, with gzip, CSV and other transforms
* **[Metadata](https://docs.powertools.aws.dev/lambda/python/latest/utilities/metadata/)** - Read the Lambda Metadata Endpoint, such as the Availability Zone ID of the execution environment
* **[Middleware factory](https://docs.powertools.aws.dev/lambda/python/latest/utilities/middleware_factory/)** - Decorator factory to run your own logic before and after each invocation
* **[Typing](https://docs.powertools.aws.dev/lambda/python/latest/utilities/typing/)** - Static typing for the Lambda context object
* **[JMESPath Functions](https://docs.powertools.aws.dev/lambda/python/latest/utilities/jmespath_functions/)** - Built-in JMESPath functions to deserialize common encoded JSON payloads

### Lambda features

* **[Lambda Managed Instances](https://docs.powertools.aws.dev/lambda/python/latest/lambda-features/managed-instances/)** - Using Powertools when one execution environment handles concurrent invocations
* **[Durable Functions](https://docs.powertools.aws.dev/lambda/python/latest/lambda-features/durable-functions/)** - Using Powertools with Lambda Durable Functions
* **[Build recipes](https://docs.powertools.aws.dev/lambda/python/latest/build_recipes/)** - Packaging, cross-platform builds, cold start optimization and CI/CD integration

## Tutorial and examples

* [Tutorial](https://docs.powertools.aws.dev/lambda/python/latest/tutorial/) and [workshop](https://s12d.com/powertools-for-aws-lambda-workshop)
* [Examples](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples) for every utility, the same code the documentation shows
* [Serverless Airline](https://github.com/aws-samples/aws-serverless-airline-booking), a sample application using Powertools end to end
* [What the community built](https://docs.powertools.aws.dev/lambda/python/latest/we_made_this/): blog posts, workshops, videos and sample apps

## How to support Powertools for AWS Lambda (Python)?

### Becoming a reference customer

Knowing which companies are using this library is important to help prioritize the project internally. If your company is using Powertools for AWS Lambda (Python), you can request to have your name and logo added to the README file by raising a [Support Powertools for AWS Lambda (Python) (become a reference)](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E) issue.

The following companies, among others, use Powertools:

* [Alma Media](https://www.almamedia.fi/en/)
* [Banxware](https://www.banxware.com/)
* [Brsk](https://www.brsk.co.uk/)
* [BusPatrol](https://buspatrol.com/)
* [Capital One](https://www.capitalone.com/)
* [Caylent](https://caylent.com/)
* [CHS Inc.](https://www.chsinc.com/)
* [CPQi (Exadel Financial Services)](https://cpqi.com/)
* [CloudZero](https://www.cloudzero.com/)
* [CyberArk](https://www.cyberark.com/)
* [EF Education First](https://www.ef.com/)
* [Flyweight](https://flyweight.io/)
* [globaldatanet](https://globaldatanet.com/)
* [Guild](https://guild.com/)
* [IMS](https://ims.tech/)
* [Instil](https://instil.co/)
* [Jit Security](https://www.jit.io/)
* [LocalStack](https://www.localstack.cloud/)
* [Propellor.ai](https://www.propellor.ai/)
* [Pushpay](https://pushpay.com/)
* [QuasiScience Limited](https://quasiscience.com/)
* [Recast](https://getrecast.com/)
* [TopSport](https://www.topsport.com.au/)
* [Transformity](https://transformity.tech/)
* [Trek10](https://www.trek10.com/)
* [Vertex Pharmaceuticals](https://www.vrtx.com/)

### Sharing your work

Share what you did with Powertools for AWS Lambda (Python) 💞💞. Blog post, workshops, presentation, sample apps and others. Check out what the community has already shared about Powertools for AWS Lambda (Python) [in this link](https://docs.powertools.aws.dev/lambda/python/latest/we_made_this/).

### Using the Lambda layer

Using the [public layer](https://docs.powertools.aws.dev/lambda/python/latest/getting-started/install/#lambda-layer) helps us understand who uses Powertools for AWS Lambda (Python) in a non-intrusive way, and helps us gain future investments for other Powertools for AWS Lambda languages. You can still add Powertools for AWS Lambda (Python) as a dev dependency (or as part of your virtual env) to not impact the development process.

## Contributing

Issues and pull requests are welcome, including the ones written with AI assistance. If you used an assistant, say so in the issue or PR and tell us how you verified the change: which tests you ran yourself, and which real AWS service or event you validated against when it applies. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the process, [AGENTS.md](AGENTS.md) for the rules the CI enforces, and [docs/adr](docs/adr/README.md) for the premises behind them.

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools for AWS Lambda (Python) idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## Connect

* **Powertools for AWS Lambda on Discord**: `#python` - **[Invite link](https://discord.gg/B8zZKbbyET)**
* **Email**: <aws-powertools-maintainers@amazon.com>

## Security disclosures

If you think you've found a potential security issue, please do not post it in the Issues. Instead, follow [SECURITY.md](SECURITY.md): report it through the [AWS vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/) or [email AWS security directly](mailto:aws-security@amazon.com).

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
