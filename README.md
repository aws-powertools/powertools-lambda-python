# Lambda Powertools

![Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7|%203.8&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier.

**[📜Documentation](https://awslabs.github.io/aws-lambda-powertools-python/)** | **[API Docs](https://awslabs.github.io/aws-lambda-powertools-python/api/)** | **[🐍PyPi](https://pypi.org/project/aws-lambda-powertools/)** | **[Feature request](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=)** | **[🐛Bug Report](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=bug%2C+triage&template=bug_report.md&title=)** | **[Kitchen sink example](https://github.com/awslabs/aws-lambda-powertools-python/tree/develop/example)** | **[Detailed blog post](https://aws.amazon.com/blogs/opensource/simplifying-serverless-best-practices-with-lambda-powertools/)**

## Features

* **[Tracing](https://awslabs.github.io/aws-lambda-powertools-python/core/tracer/)** - Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions
* **[Logging](https://awslabs.github.io/aws-lambda-powertools-python/core/logger/)** - Structured logging made easier, and decorator to enrich structured logging with key Lambda context details
* **[Metrics](https://awslabs.github.io/aws-lambda-powertools-python/core/metrics/)** - Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)
* **[Bring your own middleware](https://awslabs.github.io/aws-lambda-powertools-python/utilities/middleware_factory/)** - Decorator factory to create your own middleware to run logic before, and after each Lambda invocation

### Installation

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run: ``pip install aws-lambda-powertools``

## Example

See **[example](./example/README.md)** of all features, testing, and a SAM template with all Powertools env vars. All features also provide full docs, and code completion for VSCode and PyCharm.

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)
* [Gatsby Apollo Theme for Docs](https://github.com/apollographql/gatsby-theme-apollo/tree/master/packages/gatsby-theme-apollo-docs)

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
