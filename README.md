# Lambda Powertools

![Python Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier.

## Tenets

* **AWS Lambda only** – We optimise for AWS Lambda function environments only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
* **Eases the adoption of best practices** – The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
* **Keep it lean** – Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time. 
* **We strive for backwards compatibility** – New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
* **We work backwards from the community** – We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs)
* **Idiomatic** – Utilities follow programming language idioms and language-specific best practices.

_`*` Core utilities are Tracer, Logger and Metrics. Optional utilities may vary across languages._

## Powertools available

* [Python - Beta](./python/README.md)

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
