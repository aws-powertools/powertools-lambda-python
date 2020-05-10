# Lambda Powertools

![PackageStatus](https://img.shields.io/static/v1?label=status&message=beta&color=blueviolet?style=flat-square) ![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7|%203.8&color=blue?style=flat-square&logo=python) ![PyPI version](https://badge.fury.io/py/aws-lambda-powertools.svg) ![PyPi monthly downloads](https://img.shields.io/pypi/dm/aws-lambda-powertools) ![Build](https://github.com/awslabs/aws-lambda-powertools/workflows/Powertools%20Python/badge.svg?branch=master)

A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging, and creating custom metrics asynchronously easier - Compatible with Python >=3.6.

> During beta, this library may change its API/methods, or environment variables as it receives feedback from customers.

* **Status**: Beta
* **How long until GA?**: [Current progress](https://github.com/awslabs/aws-lambda-powertools/projects/1)

## Features

**[Tracing](###Tracing)**

* Capture cold start as annotation, and response and exceptions as metadata
* Run functions locally with SAM CLI without code change to disable tracing
* Explicitly disable tracing via env var `POWERTOOLS_TRACE_DISABLED="true"`
* Support tracing async methods

**[Logging](###Logging)**

* Capture key fields from Lambda context, cold start and structures logging output as JSON
* Log Lambda event when instructed (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_LOG_EVENT="true"` or explicitly via decorator param
* Log sampling enables DEBUG log level for a percentage of requests (disabled by default)
    - Enable via `POWERTOOLS_LOGGER_SAMPLE_RATE=0.1`, ranges from 0 to 1, where 0.1 is 10% and 1 is 100%
* Append additional keys to structured log at any point in time

**[Metrics](###Metrics)**

* Aggregate up to 100 metrics using a single CloudWatch Embedded Metric Format object (large JSON blob)
* Context manager to create an one off metric with a different dimension than metrics already aggregated
* Validate against common metric definitions mistakes (metric unit, values, max dimensions, max metrics, etc)

**[Bring your own middleware](###Bring-your-own-middleware)**

* Utility to easily create your own middleware
* Run logic before, after, and handle exceptions
* Receive lambda handler, event, context
* Optionally create sub-segment for each custom middleware

**Environment variables** used across suite of utilities

Environment variable | Description | Default | Utility
------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------
POWERTOOLS_SERVICE_NAME | Sets service name used for tracing namespace, metrics dimensions and structured logging | "service_undefined" | all
POWERTOOLS_TRACE_DISABLED | Disables tracing | "false" | [Tracing](###Tracing)
POWERTOOLS_TRACE_MIDDLEWARES | Creates sub-segment for each middleware created by lambda_handler_decorator | "false" | [middleware_factory](###Bring-your-own-middleware)
POWERTOOLS_LOGGER_LOG_EVENT | Logs incoming event | "false" | [Logging](###Logging)
POWERTOOLS_LOGGER_SAMPLE_RATE | Debug log sampling  | 0 | [Logging](###Logging)
POWERTOOLS_METRICS_NAMESPACE | Metrics namespace  | None | [Metrics](###Metrics)
LOG_LEVEL | Sets logging level | "INFO" | [Logging](###Logging)

## Usage

See **[example](./example/README.md)** of all features, testing, and a SAM template with all Powertools env vars. All features also provide full docs, and code completion for VSCode and PyCharm.

### Installation

With [pip](https://pip.pypa.io/en/latest/index.html) installed, run: ``pip install aws-lambda-powertools``

### Tracing

#### Tracing Lambda handler and a function

```python
from aws_lambda_powertools.tracing import Tracer
tracer = Tracer()
# tracer = Tracer(service="payment") # can also be explicitly defined

@tracer.capture_method
def collect_payment(charge_id):
  ret = requests.post(PAYMENT_ENDPOINT) # logic
  tracer.put_annotation("PAYMENT_STATUS", "SUCCESS") # custom annotation
  return ret

@tracer.capture_lambda_handler
def handler(event, context)
  charge_id = event.get('charge_id')
  payment = collect_payment(charge_id)
  ...
```

#### Tracing asynchronous functions

```python
import asyncio

from aws_lambda_powertools.tracing import Tracer
tracer = Tracer()
# tracer = Tracer(service="payment") # can also be explicitly defined

@tracer.capture_method
async def collect_payment(charge_id):
    ...

@tracer.capture_lambda_handler
def handler(event, context)
  charge_id = event.get('charge_id')
  payment = asyncio.run(collect_payment(charge_id)) # python 3.7+  
  ...
```

#### Using escape hatch mechanisms

You can use `tracer.provider` attribute to access all methods provided by `xray_recorder`. This is useful when you need a feature available in X-Ray that is not available in the Tracer middleware, for example [thread-safe](https://github.com/aws/aws-xray-sdk-python/#user-content-trace-threadpoolexecutor), or [context managers](https://github.com/aws/aws-xray-sdk-python/#user-content-start-a-custom-segmentsubsegment).

**Example using aiohttp with an async context manager**

```python
import asyncio

from aws_lambda_powertools.tracing import Tracer, aiohttp_trace_config
tracer = Tracer()

async def aiohttp_task():
    # Async context manager as opposed to `@tracer.capture_method`
    async with tracer.provider.in_subsegment_async("## aiohttp escape hatch"):
        async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
            async with session.get("https://httpbin.org/json") as resp:
                resp = await resp.json()
                return resp

@tracer.capture_method
async def async_tasks():
    ret = await aiohttp_task()
    ...

    return {
        "task": "done",
        **ret
    }

@tracer.capture_lambda_handler
def handler(event, context)
  ret = asyncio.run(async_tasks()) # python 3.7+  
  ...
```

#### Using a pre-configured tracer anywhere

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

#### Structuring logs with Lambda context info

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

<details>
<summary>Exerpt output in CloudWatch Logs</summary>

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
</details>

#### Appending additional keys to current logger

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

<details>
<summary>Exerpt output in CloudWatch Logs</summary>

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
</details>

### Metrics

This feature makes use of CloudWatch Embedded Metric Format (EMF), and metrics are created asynchronously by CloudWatch service.

Metrics middleware validates against the minimum necessary for a metric to be published:

* At least of one Metric and Dimension 
* Maximum of 9 dimensions
* Only one Namespace
* [Any Metric unit supported by CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)

#### Creating multiple metrics

If using multiple middlewares, use `log_metrics` as the last decorator, or else it will fail with `SchemaValidationError` if no metrics are recorded.

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

> **NOTE**: When using Metrics() in multiple places in your code, make sure to use `POWERTOOLS_METRICS_NAMESPACE` env var, or setting namespace param.

### Bring your own middleware

This feature allows you to create your own middleware as a decorator with ease by following a simple signature. 

* Accept 3 mandatory args - `handler, event, context` 
* Always return the handler with event/context or response if executed
  - Supports nested middleware/decorators use case

#### Middleware with no params

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

#### Middleware with params

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

#### Tracing middleware execution

This makes use of an existing Tracer instance that you may have initialized anywhere in your code. If no Tracer instance is found,  it'll initialize one using default options.

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

By default, all log statements from AWS Lambda Powertools package are suppressed. If you'd like to enable them, use `set_package_logger` utility:

```python
import aws_lambda_powertools
aws_lambda_powertools.logging.logger.set_package_logger()
...
```
