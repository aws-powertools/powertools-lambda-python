# Lambda Powertools

![PackageStatus](https://img.shields.io/static/v1?label=status&message=beta&color=blueviolet?style=flat-square) ![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7|%203.8&color=blue?style=flat-square&logo=python)

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
* Log sampling enables DEBUG log level for a percentage of requests (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_SAMPLE_RATE=0.1`, ranges from 0 to 1, where 0.1 is 10% and 1 is 100%

**Metrics**

* Aggregate up to 100 metrics using a single CloudWatch Embedded Metric Format object (large JSON blob)
* Context manager to create an one off metric with a different dimension than metrics already aggregated
* Validate against common metric definitions mistakes (metric unit, values, max dimensions, max metrics, etc)
* No stack, custom resource, data collection needed — Metrics are created async by CloudWatch EMF

**Environment variables** used across suite of utilities

Environment variable | Description | Default | Utility
------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------
POWERTOOLS_SERVICE_NAME | Sets service name used for tracing namespace, metrics dimensions and structured logging | "service_undefined" | all
POWERTOOLS_TRACE_DISABLED | Disables tracing | "false" | tracing
POWERTOOLS_LOGGER_LOG_EVENT | Logs incoming event | "false" | logging
POWERTOOLS_LOGGER_SAMPLE_RATE | Debug log sampling  | 0 | logging
POWERTOOLS_METRICS_NAMESPACE | Metrics namespace  | None | metrics
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
            POWERTOOLS_LOGGER_SAMPLE_RATE: 0.1 # enable debug logging for 1% of requests, 0% by default
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

> **NOTE** `log_metric` will be removed once it's GA.

This feature makes use of CloudWatch Embedded Metric Format (EMF) and metrics are created asynchronously by CloudWatch service

> Contrary to `log_metric`, you don't need any custom resource or additional CloudFormation stack anymore.

Metrics middleware validates against the minimum necessary for a metric to be published:

* At least of one Metric and Dimension 
* Maximum of 9 dimensions
* Only one Namespace
* [Any Metric unit supported by CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)

**Creating multiple metrics**

`log_metrics` decorator calls the decorated function, so leave that for last decorator or will fail with `SchemaValidationError` if no metrics are recorded.

```python
from aws_lambda_powertools.metrics import Metrics, MetricUnit

metrics = Metrics()
metrics.add_namespace(name="ServerlessAirline")
metrics.add_metric(name="ColdStart", unit="Count", value=1)
metrics.add_dimension(name="service", value="booking")

@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(evt, ctx):
    metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
    some_code()
    return True

def some_code():
    metrics.add_metric(name="some_other_metric", unit=MetricUnit.Seconds, value=1)
    ...
```

CloudWatch EMF uses the same dimensions across all metrics. If you have metrics that should have different dimensions, use `single_metric` to create a single metric with any dimension you want. Generally, this would be an edge case since you [pay for unique metric](https://aws.amazon.com/cloudwatch/pricing/) 

> unique metric = (metric_name + dimension_name + dimension_value)

```python
from aws_lambda_powertools.metrics import MetricUnit, single_metric

with single_metric(name="ColdStart", unit=MetricUnit.Count, value=1) as metric:
    metric.add_dimension(name="function_context", value="$LATEST")
```

## Beta

> **[Progress towards GA](https://github.com/awslabs/aws-lambda-powertools/projects/1)**

This library may change its API/methods or environment variables as it receives feedback from customers. Currently looking for ideas in the following areas before making it stable:

* **Should Tracer patch all possible imported libraries by default or only AWS SDKs?**
    - Patching all libraries may have a small performance penalty (~50ms) at cold start
    - Alternatively, we could patch only AWS SDK if available and to provide a param to patch multiple `Tracer(modules=("boto3", "requests"))` 
