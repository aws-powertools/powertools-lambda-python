# Lambda Powertools

[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fawslabs%2Faws-lambda-powertools%2Fbadge%3Fref%3Ddevelop&style=flat)](https://actions-badge.atrox.dev/awslabs/aws-lambda-powertools/goto?ref=develop) ![PackageStatus](https://img.shields.io/static/v1?label=status&message=beta&color=blueviolet?style=flat-square) ![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7&color=blue?style=flat-square&logo=python)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier - Currently available for Python only and compatible with Python >=3.6.

**Status**: Beta

## Features

**Tracing**

> It currently uses AWS X-Ray

* Decorators that capture cold start as annotation, and response and exceptions as metadata
* Run functions locally without code change to disable tracing
* Explicitly disable tracing via env var `POWERTOOLS_TRACE_DISABLED="true"`

**Logging**

* Decorators that capture key fields from Lambda context, cold start and structures logging output as JSON
* Optionally log Lambda request when instructed (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_LOG_EVENT="true"` or explicitly via decorator param
* Logs canonical custom metric line to logs that can be consumed asynchronously

**Environment variables** used across suite of utilities

Environment variable | Description | Default | Utility
------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------
POWERTOOLS_SERVICE_NAME | Sets service name used for tracing namespace, metrics dimensions and structured logging | "service_undefined" | all
POWERTOOLS_TRACE_DISABLED | Disables tracing | "false" | tracing
POWERTOOLS_LOGGER_LOG_EVENT | Logs incoming event | "false" | logging
LOG_LEVEL | Sets logging level | "INFO" | logging

## Usage

### Installation

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run: ``pip install aws-lambda-powertools``

### Tracing

**Example SAM template using supported environment variables**

```yaml
Globals:
  Function:
    Tracing: Active # can also be enabled per function
    Environment:
        Variables:
            POWERTOOLS_SERVICE_NAME: "payment" 
            POWERTOOLS_TRACE_DISABLED: "false" 
```

**Pseudo Python Lambda code**

```python
from aws_lambda_powertools.tracing import Tracer
tracer = Tracer()
# tracer = Tracer(service="payment") # can also be explicitly defined

@tracer.capture_method
def collect_payment(charge_id):
  # logic
  ret = requests.post(PAYMENT_ENDPOINT)
  # custom annotation
  tracer.put_annotation("PAYMENT_STATUS", "SUCCESS")
  return ret

@tracer.capture_lambda_handler
def handler(event, context)
  charge_id = event.get('charge_id')
  payment = collect_payment(charge_id)
  ...
```


### Logging

**Example SAM template using supported environment variables**

```yaml
Globals:
  Function:
    Environment:
        Variables:
            POWERTOOLS_SERVICE_NAME: "payment" 
            LOG_LEVEL: "INFO"
```

**Pseudo Python Lambda code**

```python
from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context

logger = logger_setup()  
# logger_setup(service="payment") # also accept explicit service name
# logger_setup(level="INFO") # also accept explicit log level

@logger_inject_lambda_context
def handler(event, context)
  logger.info("Collecting payment")
  ...
  # You can log entire objects too
  logger.info({
    "operation": "collect_payment",
    "charge_id": event['charge_id']
  })
  ...
```

**Exerpt output in CloudWatch Logs**

```json
{  
   "timestamp":"2019-08-22 18:17:33,774",
   "level":"INFO",
   "location":"collect.handler:1",
   "service":"payment",
   "lambda_function_name":"test",
   "lambda_function_memory_size":"128",
   "lambda_function_arn":"arn:aws:lambda:eu-west-1:12345678910:function:test",
   "lambda_request_id":"52fdfc07-2182-154f-163f-5f0f9a621d72",
   "cold_start": "true",
   "message": "Collecting payment"
}

{  
   "timestamp":"2019-08-22 18:17:33,774",
   "level":"INFO",
   "location":"collect.handler:15",
   "service":"payment",
   "lambda_function_name":"test",
   "lambda_function_memory_size":"128",
   "lambda_function_arn":"arn:aws:lambda:eu-west-1:12345678910:function:test",
   "lambda_request_id":"52fdfc07-2182-154f-163f-5f0f9a621d72",
   "cold_start": "true",
   "message":{  
      "operation":"collect_payment",
      "charge_id": "ch_AZFlk2345C0"
   }
}
```

#### Custom Metrics async

> **NOTE**: This will **likely change after Beta** in light of [new Amazon CloudWatch embedded metric format](https://aws.amazon.com/about-aws/whats-new/2019/11/amazon-cloudwatch-launches-embedded-metric-format/), meaning we won't need an additional stack and interface could change.

This feature requires [Custom Metrics SAR App](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:374852340823:applications~async-custom-metrics) in order to process canonical metric lines in CloudWatch Logs. 

If you're starting from scratch, you may want to see a working example, tune to your needs and deploy within your account - [Serverless Airline Log Processing Stack](https://github.com/aws-samples/aws-serverless-airline-booking/blob/develop/src/backend/log-processing/template.yaml)

```python
from aws_lambda_powertools.logging import MetricUnit, log_metric

def handler(event, context)
  log_metric(name="SuccessfulPayment", unit=MetricUnit.Count, value=10, namespace="MyApplication")
  
  # Optional dimensions
  log_metric(name="SuccessfulPayment", unit=MetricUnit.Count, value=10, namespace="MyApplication", customer_id="123-abc", charge_id="abc-123")
  
  # Explicit service name
  log_metric(service="paymentTest", name="SuccessfulPayment", namespace="MyApplication".....)
  ...
```

**Exerpt output in CloudWatch Logs**

```
MONITORING|10|Count|SuccessfulPayment|MyApplication|service="payment
MONITORING|10|Count|SuccessfulPayment|MyApplication|customer_id="123-abc",charge_id="abc-123",service="payment
MONITORING|10|Count|SuccessfulPayment|MyApplication|service="paymentTest
```


## Beta

This library may change its API/methods or environment variables as it receives feedback from customers. Currently looking for ideas in the following areas before making it stable:

* **Should Tracer patch all possible imported libraries by default or only AWS SDKs?**
    - Patching all libraries may have a small performance penalty (~50ms) at cold start
    - Alternatively, we could patch only AWS SDK if available and to provide a param to patch multiple `Tracer(modules=("boto3", "requests"))` 
* **Create a Tracer provider to support additional tracing**
    - Either duck typing or ABC to allow additional tracing providers

## TODO

* [ ] Enable CI
* [ ] Add an example code using powertools
* [ ] Automate release and version bumping in CI

## Credits

* Structured logging initial implementation from [aws-lambda-logging](https://gitlab.com/hadrien/aws_lambda_logging)
* Powertools idea [DAZN Powertools](https://github.com/getndazn/dazn-lambda-powertools/)

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
