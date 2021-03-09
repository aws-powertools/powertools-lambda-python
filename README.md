# AWS Lambda Powertools (Python)

![Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7|%203.8&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools)

A suite of Python utilities for AWS Lambda functions to ease adopting best practices such as tracing, structured logging, custom metrics, and more. ([AWS Lambda Powertools Java](https://github.com/awslabs/aws-lambda-powertools-java) is also available).

**[📜Documentation](https://awslabs.github.io/aws-lambda-powertools-python/)** | **[API Docs](https://awslabs.github.io/aws-lambda-powertools-python/api/)** | **[🐍PyPi](https://pypi.org/project/aws-lambda-powertools/)** | **[Feature request](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=)** | **[🐛Bug Report](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=bug%2C+triage&template=bug_report.md&title=)** | **[Hello world example](https://github.com/aws-samples/cookiecutter-aws-sam-python)** | **[Detailed blog post](https://aws.amazon.com/blogs/opensource/simplifying-serverless-best-practices-with-lambda-powertools/)**

> **Join us on the AWS Developers Slack at `#lambda-powertools`** - **[Invite, if you don't have an account](https://join.slack.com/t/awsdevelopers/shared_invite/zt-gu30gquv-EhwIYq3kHhhysaZ2aIX7ew)**

## Features

* **[Tracing](https://awslabs.github.io/aws-lambda-powertools-python/core/tracer/)** - Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions
* **[Logging](https://awslabs.github.io/aws-lambda-powertools-python/core/logger/)** - Structured logging made easier, and decorator to enrich structured logging with key Lambda context details
* **[Metrics](https://awslabs.github.io/aws-lambda-powertools-python/core/metrics/)** - Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)
* **[Bring your own middleware](https://awslabs.github.io/aws-lambda-powertools-python/utilities/middleware_factory/)** - Decorator factory to create your own middleware to run logic before, and after each Lambda invocation
* **[Parameters utility](https://awslabs.github.io/aws-lambda-powertools-python/utilities/parameters/)** - Retrieve and cache parameter values from Parameter Store, Secrets Manager, or DynamoDB
* **[Batch processing](https://awslabs.github.io/aws-lambda-powertools-python/utilities/batch/)** - Handle partial failures for AWS SQS batch processing
* **[Typing](https://awslabs.github.io/aws-lambda-powertools-python/utilities/typing/)** - Static typing classes to speedup development in your IDE
* **[Validation](https://awslabs.github.io/aws-lambda-powertools-python/utilities/validation/)** - JSON Schema validator for inbound events and responses
* **[Event source data classes](https://awslabs.github.io/aws-lambda-powertools-python/utilities/data_classes/)** - Data classes describing the schema of common Lambda event triggers
* **[Parser](https://awslabs.github.io/aws-lambda-powertools-python/utilities/parser/)** - Data parsing and deep validation using Pydantic
* **[Idempotency](https://awslabs.github.io/aws-lambda-powertools-python/utilities/idempotency/)** - Convert your Lambda functions into idempotent operations which are safe to retry

### Installation

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run: ``pip install aws-lambda-powertools``

## Examples

* [Serverless Shopping cart](https://github.com/aws-samples/aws-serverless-shopping-cart)
* [Serverless Airline](https://github.com/aws-samples/aws-serverless-airline-booking)
* [Serverless E-commerce platform](https://github.com/aws-samples/aws-serverless-ecommerce-platform)

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
