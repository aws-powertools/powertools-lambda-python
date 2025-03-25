<!-- markdownlint-disable MD013 MD041 MD043  -->
# Powertools for AWS Lambda (Python)

[![Build](https://github.com/aws-powertools/powertools-lambda-python/actions/workflows/quality_check.yml/badge.svg)](https://github.com/aws-powertools/powertools-lambda-python/actions/workflows/python_build.yml)
[![codecov.io](https://codecov.io/github/aws-powertools/powertools-lambda-python/branch/develop/graphs/badge.svg)](https://app.codecov.io/gh/aws-powertools/powertools-lambda-python)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=%203.9|%203.10|%203.11|%203.12|%203.13&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools) [![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/aws-powertools/powertools-lambda-python/badge)](https://api.securityscorecards.dev/projects/github.com/aws-powertools/powertools-lambda-python) [![Join our Discord](https://dcbadge.vercel.app/api/server/B8zZKbbyET?style=flat-square)](https://discord.gg/B8zZKbbyET)

Powertools for AWS Lambda (Python) is a developer toolkit to implement Serverless [best practices and increase developer velocity](https://docs.powertools.aws.dev/lambda/python/latest/#features).

> Also available in [Java](https://github.com/aws-powertools/powertools-lambda-java), [Typescript](https://github.com/aws-powertools/powertools-lambda-typescript), and [.NET](https://github.com/aws-powertools/powertools-lambda-dotnet).

**[📜Documentation](https://docs.powertools.aws.dev/lambda/python/)** | **[🐍PyPi](https://pypi.org/project/aws-lambda-powertools/)** | **[Roadmap](https://docs.powertools.aws.dev/lambda/python/latest/roadmap/)** | **[Detailed blog post](https://aws.amazon.com/blogs/opensource/simplifying-serverless-best-practices-with-lambda-powertools/)**

![hero-image](https://user-images.githubusercontent.com/3340292/198254617-d0fdb672-86a6-4988-8a40-adf437135e0a.png)

## Features

* **[Tracing](https://docs.powertools.aws.dev/lambda/python/latest/core/tracer/)** - Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions
* **[Logging](https://docs.powertools.aws.dev/lambda/python/latest/core/logger/)** - Structured logging made easier, and decorator to enrich structured logging with key Lambda context details
* **[Metrics](https://docs.powertools.aws.dev/lambda/python/latest/core/metrics/)** - Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)
* **[Event handler: AppSync](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/appsync/)** - AWS AppSync event handler for Lambda Direct Resolver and Amplify GraphQL Transformer function
* **[Event handler: API Gateway and ALB](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/)** - Amazon API Gateway REST/HTTP API and ALB event handler for Lambda functions invoked using Proxy integration
* **[Event handler: Agents for Amazon Bedrock](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/bedrock_agents/)** - Create Agents for Amazon Bedrock, automatically generating OpenAPI schemas
* **[Bring your own middleware](https://docs.powertools.aws.dev/lambda/python/latest/utilities/middleware_factory/)** - Decorator factory to create your own middleware to run logic before, and after each Lambda invocation
* **[Parameters utility](https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/)** - Retrieve and cache parameter values from Parameter Store, Secrets Manager, or DynamoDB
* **[Batch processing](https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/)** - Handle partial failures for AWS SQS batch processing
* **[Typing](https://docs.powertools.aws.dev/lambda/python/latest/utilities/typing/)** - Static typing classes to speedup development in your IDE
* **[Validation](https://docs.powertools.aws.dev/lambda/python/latest/utilities/validation/)** - JSON Schema validator for inbound events and responses
* **[Event source data classes](https://docs.powertools.aws.dev/lambda/python/latest/utilities/data_classes/)** - Data classes describing the schema of common Lambda event triggers
* **[Parser](https://docs.powertools.aws.dev/lambda/python/latest/utilities/parser/)** - Data parsing and deep validation using Pydantic
* **[Idempotency](https://docs.powertools.aws.dev/lambda/python/latest/utilities/idempotency/)** - Convert your Lambda functions into idempotent operations which are safe to retry
* **[Data Masking](https://docs.powertools.aws.dev/lambda/python/latest/utilities/data_masking/)** -  Protect confidential data with easy removal or encryption
* **[Feature Flags](https://docs.powertools.aws.dev/lambda/python/latest/utilities/feature_flags/)** - A simple rule engine to evaluate when one or multiple features should be enabled depending on the input
* **[Streaming](https://docs.powertools.aws.dev/lambda/python/latest/utilities/streaming/)** - Streams datasets larger than the available memory as streaming data.

### Installation

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run: ``pip install aws-lambda-powertools``

## Tutorial and Examples

* [Tutorial](https://docs.powertools.aws.dev/lambda/python/latest/tutorial)
* [Serverless Shopping cart](https://github.com/aws-samples/aws-serverless-shopping-cart)
* [Serverless Airline](https://github.com/aws-samples/aws-serverless-airline-booking)
* [Serverless E-commerce platform](https://github.com/aws-samples/aws-serverless-ecommerce-platform)
* [Serverless GraphQL Nanny Booking Api](https://github.com/trey-rosius/babysitter_api)

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
* [Flyweight](https://flyweight.io/)
* [globaldatanet](https://globaldatanet.com/)
* [Guild](https://guild.com/)
* [IMS](https://ims.tech/)
* [Jit Security](https://www.jit.io/)
* [LocalStack](https://www.localstack.cloud/)
* [Propellor.ai](https://www.propellor.ai/)
* [Pushpay](https://pushpay.com/)
* [Recast](https://getrecast.com/)
* [TopSport](https://www.topsport.com.au/)
* [Transformity](https://transformity.tech/)
* [Trek10](https://www.trek10.com/)
* [Vertex Pharmaceuticals](https://www.vrtx.com/)

### Sharing your work

Share what you did with Powertools for AWS Lambda (Python) 💞💞. Blog post, workshops, presentation, sample apps and others. Check out what the community has already shared about Powertools for AWS Lambda (Python) [here](https://docs.powertools.aws.dev/lambda/python/latest/we_made_this/).

### Using Lambda Layer or SAR

This helps us understand who uses Powertools for AWS Lambda (Python) in a non-intrusive way, and helps us gain future investments for other Powertools for AWS Lambda languages. When [using Layers](https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer), you can add Powertools for AWS Lambda (Python) as a dev dependency (or as part of your virtual env) to not impact the development process.

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools for AWS Lambda (Python) idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## Connect

* **Powertools for AWS Lambda on Discord**: `#python` - **[Invite link](https://discord.gg/B8zZKbbyET)**
* **Email**: <aws-powertools-maintainers@amazon.com>

## Security disclosures

If you think you’ve found a potential security issue, please do not post it in the Issues.  Instead, please follow the instructions [here](https://aws.amazon.com/security/vulnerability-reporting/) or [email AWS security directly](mailto:aws-security@amazon.com).

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
