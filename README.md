# Lambda Powertools

![Python Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier.

## Tenets

* **AWS Lambda only** – We optimize for AWS Lambda functions environment only. Utilities might work with web frameworks, and non-Lambda environments though they are not officially supported.
* **Eases the adoption of best practices** – Utilities’ main priority is to facilitate best practices adoption defined in AWS Well-Architected Serverless Lens; everything else is optional.
* **Keep it lean** – Additional dependencies are carefully considered to ease maintenance, security, and to prevent negatively impacting startup time. 
* **We strive for backwards compatibility** – New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
* **We work backwards from the community** – We aim to strike a balance of what would
work for 80% of customers. Emerging practices are considered and discussed via request for 
comments (RFCs)
* **Idiomatic** – Utilities follow language’s idioms and their best practices.

## Powertools available

* [Python - Beta](./python/README.md)

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
