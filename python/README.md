# Lambda Powertools

![PackageStatus](https://img.shields.io/static/v1?label=status&message=beta&color=blueviolet?style=flat-square) ![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7|%203.8&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools) ![Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier - Currently available for Python only and compatible with Python >=3.6.

**Status**: Beta

## Features

**Tracing**

> It currently uses AWS X-Ray

* Decorators that capture cold start as annotation, and response and exceptions as metadata
* Run functions locally with SAM CLI without code change to disable tracing
* Explicitly disable tracing via env var `POWERTOOLS_TRACE_DISABLED="true"`

**Logging**

* Decorators that capture key fields from Lambda context, cold start and structures logging output as JSON
* Optionally log Lambda request when instructed (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_LOG_EVENT="true"` or explicitly via decorator param
* Logs canonical custom metric line to logs that can be consumed asynchronously
* Log sampling enables DEBUG log level for a percentage of requests (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_SAMPLE_RATE=0.1`, ranges from 0 to 1, where 0.1 is 10% and 1 is 100%
* Append additional keys to structured log at any point in time so they're available across log statements

**Metrics**

* Aggregate up to 100 metrics using a single CloudWatch Embedded Metric Format object (large JSON blob)
* Context manager to create an one off metric with a different dimension than metrics already aggregated
* Validate against common metric definitions mistakes (metric unit, values, max dimensions, max metrics, etc)
* No stack, custom resource, data collection needed — Metrics are created async by CloudWatch EMF

**Bring your own middleware**

* Utility to easily create your own middleware
* Run logic before, after, and handle exceptions
* Receive lambda handler, event, context
* Optionally create sub-segment for each custom middleware

**Environment variables** used across suite of utilities

Environment variable | Description | Default | Utility
------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------
POWERTOOLS_SERVICE_NAME | Sets service name used for tracing namespace, metrics dimensions and structured logging | "service_undefined" | all
POWERTOOLS_TRACE_DISABLED | Disables tracing | "false" | tracing
POWERTOOLS_TRACE_MIDDLEWARES | Creates sub-segment for each middleware created by lambda_handler_decorator | "false" | middleware_factory
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

**Fetching a pre-configured tracer anywhere**

```python
# handler.py
from aws_lambda_powertools.tracing import Tracer
tracer = Tracer(service="payment")

@tracer.capture_lambda_handler
def handler(event, context)
  charge_id = event.get('charge_id')
  payment = collect_payment(charge_id)
  ...

# another_file.py
from aws_lambda_powertools.tracing import Tracer
tracer = Tracer(auto_patch=False) # new instance using existing configuration with auto patching overriden
```

### Logging

> **NOTE** `logger_setup` and `logger_inject_lambda_context` are deprecated and will be completely removed once it's GA.

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
from aws_lambda_powertools.logging import Logger

logger = Logger()
# Logger(service="payment", level="INFO") # also accepts explicit service name, log level

@logger.inject_lambda_context
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
   "sampling_rate": 0.1,
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
   "sampling_rate": 0.1,
   "message":{  
      "operation":"collect_payment",
      "charge_id": "ch_AZFlk2345C0"
   }
}
```

**Append additional keys to structured log**

```python
from aws_lambda_powertools.logging import Logger

logger = Logger()

@logger.inject_lambda_context
def handler(event, context)
  if "order_id" in event:
      logger.structure_logs(append=True, order_id=event["order_id"])
  logger.info("Collecting payment")
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
   "sampling_rate": 0.1,
   "order_id": "order_id_value",
   "message": "Collecting payment"
}
```

### Custom Metrics async

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

> **NOTE**: If you want to instantiate Metrics() in multiple places in your code, make sure to use `POWERTOOLS_METRICS_NAMESPACE` env var as we don't keep a copy of that across instances.

### Utilities

#### Bring your own middleware

This feature allows you to create your own middleware as a decorator with ease by following a simple signature. 

* Accept 3 mandatory args - `handler, event, context` 
* Always return the handler with event/context or response if executed
  - Supports nested middleware/decorators use case

**Middleware with no params**

```python
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@lambda_handler_decorator
def middleware_name(handler, event, context):
    return handler(event, context)

@lambda_handler_decorator
def middleware_before_after(handler, event, context):
    logic_before_handler_execution()
    response = handler(event, context)
    logic_after_handler_execution()
    return response


# middleware_name will wrap Lambda handler 
# and simply return the handler as we're not pre/post-processing anything
# then middleware_before_after will wrap middleware_name
# run some code before/after calling the handler returned by middleware_name
# This way, lambda_handler is only actually called once (top-down)
@middleware_before_after # This will run last
@middleware_name # This will run first
def lambda_handler(event, context):
    return True
```

**Middleware with params**

```python
@lambda_handler_decorator
def obfuscate_sensitive_data(handler, event, context, fields=None):
    # Obfuscate email before calling Lambda handler
    if fields:
        for field in fields:
            field = event.get(field, "")
            event[field] = obfuscate_pii(field)

    return handler(event, context)

@obfuscate_sensitive_data(fields=["email"])
def lambda_handler(event, context):
    return True
```

**Optionally trace middleware execution**

This makes use of an existing Tracer instance that you may have initialized anywhere in your code, otherwise it'll initialize one using default options and provider (X-Ray).

```python
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@lambda_handler_decorator(trace_execution=True)
def middleware_name(handler, event, context):
    return handler(event, context)

@middleware_name
def lambda_handler(event, context):
    return True
```

Optionally, you can enrich the final trace with additional annotations and metadata by retrieving a copy of the Tracer used.

```python
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.tracing import Tracer

@lambda_handler_decorator(trace_execution=True)
def middleware_name(handler, event, context):
    tracer = Tracer() # Takes a copy of an existing tracer instance
    tracer.add_anotation...
    tracer.metadata...
    return handler(event, context)

@middleware_name
def lambda_handler(event, context):
    return True
```


### Debug mode

By default, all debug log statements from AWS Lambda Powertools package are suppressed. If you'd like to enable them, use `set_package_logger` utility:

```python
import aws_lambda_powertools
aws_lambda_powertools.logging.logger.set_package_logger()
...
```

## Beta

This library may change its API/methods or environment variables as it receives feedback from customers

**[Progress towards GA](https://github.com/awslabs/aws-lambda-powertools/projects/1)**
