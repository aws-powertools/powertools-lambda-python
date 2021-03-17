---
title: Logger
description: Core utility
---


Logger provides an opinionated logger with output structured as JSON.

## Key features

* Capture key fields from Lambda context, cold start and structures logging output as JSON
* Log Lambda event when instructed (disabled by default)
* Log sampling enables DEBUG log level for a percentage of requests (disabled by default)
* Append additional keys to structured log at any point in time

## Getting started

Logger requires two settings:

Setting | Description | Environment variable | Constructor parameter
------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------
**Logging level** | Sets how verbose Logger should be (INFO, by default) |  `LOG_LEVEL` | `level`
**Service** | Sets **service** key that will be present across all log statements | `POWERTOOLS_SERVICE_NAME` | `service`

> Example using AWS Serverless Application Model (SAM)

=== "template.yaml"
	```yaml hl_lines="9 10"
    Resources:
      HelloWorldFunction:
        Type: AWS::Serverless::Function
        Properties:
          Runtime: python3.8
          Environment:
            Variables:
              LOG_LEVEL: INFO
              POWERTOOLS_SERVICE_NAME: example
	```
=== "app.py"
	```python hl_lines="2 4"
	from aws_lambda_powertools import Logger
	logger = Logger() # Sets service via env var
	# OR logger = Logger(service="example")
	```

### Standard structured keys

Your Logger will include the following keys to your structured logging, by default:

Key | Type | Example | Description
------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------
**timestamp** | str | "2020-05-24 18:17:33,774" | Timestamp of actual log statement
**level** | str | "INFO" | Logging level
**location** | str | "collect.handler:1" | Source code location where statement was executed
**service** | str | "payment" | Service name defined. "service_undefined" will be used if unknown
**sampling_rate** | int |  0.1 | Debug logging sampling rate in percentage e.g. 10% in this case
**message** | any |  "Collecting payment" | Log statement value. Unserializable JSON values will be casted to string
**xray_trace_id** | str | "1-5759e988-bd862e3fe1be46a994272793" | X-Ray Trace ID when Lambda function has enabled Tracing

### Capturing Lambda context info

You can enrich your structured logs with key Lambda context information via `inject_lambda_context`.

=== "collect.py"

    ```python hl_lines="5"
    from aws_lambda_powertools import Logger

    logger = Logger()

    @logger.inject_lambda_context
    def handler(event, context):
     logger.info("Collecting payment")
     ...
     # You can log entire objects too
     logger.info({
        "operation": "collect_payment",
        "charge_id": event['charge_id']
     })
     ...
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="6-10 26-27"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "lambda_function_name": "test",
	  "lambda_function_memory_size": 128,
	  "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
	  "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
	  "cold_start": true,
	  "sampling_rate": 0.0,
	  "message": "Collecting payment"
	},
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:15",
	  "service": "payment",
	  "lambda_function_name": "test",
	  "lambda_function_memory_size": 128,
	  "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
	  "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
	  "cold_start": true,
	  "sampling_rate": 0.0,
	  "message": {
		"operation": "collect_payment",
		"charge_id": "ch_AZFlk2345C0"
	  }
	}
    ```

When used, this will include the following keys:

Key | Type | Example
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
**cold_start**| bool | false
**function_name**| str | "example-powertools-HelloWorldFunction-1P1Z6B39FLU73"
**function_memory_size**| int | 128
**function_arn**| str | "arn:aws:lambda:eu-west-1:012345678910:function:example-powertools-HelloWorldFunction-1P1Z6B39FLU73"
**function_request_id**| str | "899856cb-83d1-40d7-8611-9e78f15f32f4"

#### Logging incoming event

When debugging in non-production environments, you can instruct Logger to log the incoming event with `log_event` param or via `POWERTOOLS_LOGGER_LOG_EVENT` env var.

!!! warning
    This is disabled by default to prevent sensitive info being logged.

=== "log_handler_event.py"

    ```python hl_lines="5"
    from aws_lambda_powertools import Logger

    logger = Logger()

    @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
       ...
    ```

#### Setting a Correlation ID

> New in 1.12.0

You can set a Correlation ID using `correlation_id_path` param by passing a [JMESPath expression](https://jmespath.org/tutorial.html){target="_blank"}.

=== "collect.py"

    ```python hl_lines="6"
	from aws_lambda_powertools import Logger

	logger = Logger()

	@logger.inject_lambda_context(correlation_id_path="headers.my_request_id_header")
	def handler(event, context):
		logger.info("Collecting payment")
        ...
    ```

=== "Example Event"

	```json hl_lines="3"
	{
	  "headers": {
		"my_request_id_header": "correlation_id_value"
	  }
	}
	```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "correlation_id": "correlation_id_value",
	  "message": "Collecting payment"
	}
    ```

We provide [built-in JMESPath expressions](#built-in-correlation-id-expressions) for known event sources, where either a request ID or X-Ray Trace ID are present.

=== "collect.py"

    ```python hl_lines="2"
	from aws_lambda_powertools import Logger
	from aws_lambda_powertools.logging import correlation_paths

	logger = Logger()

	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
	def handler(event, context):
		logger.info("Collecting payment")
        ...
    ```

=== "Example Event"

	```json hl_lines="3"
	{
	  "requestContext": {
		"requestId": "correlation_id_value"
	  }
	}
	```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "correlation_id": "correlation_id_value",
	  "message": "Collecting payment"
	}
    ```

### Appending additional keys

You can append additional keys using either mechanism:

* Persist new keys across all future log messages via `structure_logs` method
* Add additional keys on a per log message basis via `extra` parameter

#### structure_logs method

You can append your own keys to your existing Logger via `structure_logs(append=True, **kwargs)` method.

> Omitting `append=True` will reset the existing structured logs to standard keys + keys provided as arguments

=== "collect.py"

    ```python hl_lines="7"
    from aws_lambda_powertools import Logger

    logger = Logger()

    def handler(event, context):
     order_id = event.get("order_id")
     logger.structure_logs(append=True, order_id=order_id)
     logger.info("Collecting payment")
        ...
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "order_id": "order_id_value",
	  "message": "Collecting payment"
	}
    ```

!!! tip "Logger will automatically reject any key with a None value"
	If you conditionally add keys depending on the payload, you can use the highlighted line above as an example.

	This example will add `order_id` if its value is not empty, and in subsequent invocations where `order_id` might not be present it'll remove it from the logger.

#### extra parameter

> New in 1.10.0

Extra parameter is available for all log levels' methods, as implemented in the standard logging library - e.g. `logger.info, logger.warning`.

It accepts any dictionary, and all keyword arguments will be added as part of the root structure of the logs for that log statement.

!!! info "Any keyword argument added using `extra` will not be persisted for subsequent messages."

=== "extra_parameter.py"

    ```python hl_lines="6"
    logger = Logger(service="payment")

    fields = { "request_id": "1123" }

    logger.info("Hello", extra=fields)
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2021-01-12 14:08:12,357",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "request_id": "1123",
	  "message": "Collecting payment"
	}
    ```

#### set_correlation_id method

> New in 1.12.0

You can set a correlation_id to your existing Logger via `set_correlation_id(value)` method by passing any string value.

=== "collect.py"

    ```python hl_lines="6"
	from aws_lambda_powertools import Logger

	logger = Logger()

	def handler(event, context):
		logger.set_correlation_id(event["requestContext"]["requestId"])
		logger.info("Collecting payment")
        ...
    ```

=== "Example Event"

	```json hl_lines="3"
	{
	  "requestContext": {
		"requestId": "correlation_id_value"
	  }
	}
	```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "correlation_id": "correlation_id_value",
	  "message": "Collecting payment"
	}
    ```

Alternatively, you can combine [Data Classes utility](../utilities/data_classes.md) with Logger to use dot notation object:

=== "collect.py"

    ```python hl_lines="2 7-8"
	from aws_lambda_powertools import Logger
	from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

	logger = Logger()

	def handler(event, context):
		event = APIGatewayProxyEvent(event)
		logger.set_correlation_id(event.request_context.request_id)
		logger.info("Collecting payment")
        ...
    ```
=== "Example Event"

	```json hl_lines="3"
	{
	  "requestContext": {
		"requestId": "correlation_id_value"
	  }
	}
	```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
	{
	  "timestamp": "2020-05-24 18:17:33,774",
	  "level": "INFO",
	  "location": "collect.handler:1",
	  "service": "payment",
	  "sampling_rate": 0.0,
	  "correlation_id": "correlation_id_value",
	  "message": "Collecting payment"
	}
    ```

### Logging exceptions

When logging exceptions, Logger will add new keys named `exception_name` and `exception` with the full traceback as a string.

!!! tip
	> New in 1.12.0

	You can use your preferred Log Analytics tool to enumerate exceptions across all your services using `exception_name` key.

=== "logging_an_exception.py"

    ```python hl_lines="7"
    from aws_lambda_powertools import Logger
    logger = Logger()

    try:
         raise ValueError("something went wrong")
    except Exception:
         logger.exception("Received an exception")
    ```

=== "Example CloudWatch Logs excerpt"

    ```json
    {
       "level": "ERROR",
       "location": "<module>:4",
       "message": "Received an exception",
       "timestamp": "2020-08-28 18:11:38,886",
       "service": "service_undefined",
       "sampling_rate": 0.0,
       "exception_name": "ValueError",
       "exception": "Traceback (most recent call last):\n  File \"<input>\", line 2, in <module>\nValueError: something went wrong"
    }
    ```

## Advanced

### Reusing Logger across your code

Logger supports inheritance via `child` parameter. This allows you to create multiple Loggers across your code base, and propagate changes such as new keys to all Loggers.

=== "collect.py"

    ```python hl_lines="1 7"
    import shared # Creates a child logger named "payment.shared"
    from aws_lambda_powertools import Logger

    logger = Logger() # POWERTOOLS_SERVICE_NAME: "payment"

    def handler(event, context):
      	shared.inject_payment_id(event)
		...
    ```

=== "shared.py"

    ```python hl_lines="6"
    from aws_lambda_powertools import Logger

    logger = Logger(child=True) # POWERTOOLS_SERVICE_NAME: "payment"

    def inject_payment_id(event):
        logger.structure_logs(append=True, payment_id=event.get("payment_id"))
    ```

In this example, `Logger` will create a parent logger named `payment` and a child logger named `payment.shared`. Changes in either parent or child logger will be propagated bi-directionally.

!!! info "Child loggers will be named after the following convention `{service}.{filename}`"
	If you forget to use `child` param but the `service` name is the same of the parent, we will return the existing parent `Logger` instead.

### Sampling debug logs

Use sampling when you want to dynamically change your log level to DEBUG based on a **percentage of your concurrent/cold start invocations**.

You can set using `POWERTOOLS_LOGGER_SAMPLE_RATE` env var or explicitly with `sample_rate` parameter: Values range from `0.0` to `1` (100%)

!!! tip "When is this useful?"
	Take for example a sudden increase in concurrency. When looking into logs you might not have enough information, and while you can adjust log levels it might not happen again.

	This feature takes into account transient issues where additional debugging information can be useful.

Sampling decision happens at the Logger class initialization. This means sampling may happen significantly more or less than you expect if you have a steady low number of invocations and thus few cold starts.

!!! note
    If you want Logger to calculate sampling upon every invocation, please open a [feature request](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=).

=== "collect.py"

    ```python hl_lines="4 7"
    from aws_lambda_powertools import Logger

    # Sample 10% of debug logs e.g. 0.1
    logger = Logger(sample_rate=0.1, level="INFO")

    def handler(event, context):
     logger.debug("Verifying whether order_id is present")
     if "order_id" in event:
        logger.info("Collecting payment")
        ...
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="3 11 25"
    {
       "timestamp": "2020-05-24 18:17:33,774",
       "level": "DEBUG",
       "location": "collect.handler:1",
       "service": "payment",
       "lambda_function_name": "test",
       "lambda_function_memory_size": 128,
       "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
       "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
       "cold_start": true,
       "sampling_rate": 0.1,
       "message": "Verifying whether order_id is present"
    }

    {
       "timestamp": "2020-05-24 18:17:33,774",
       "level": "INFO",
       "location": "collect.handler:1",
       "service": "payment",
       "lambda_function_name": "test",
       "lambda_function_memory_size": 128,
       "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
       "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
       "cold_start": true,
       "sampling_rate": 0.1,
       "message": "Collecting payment"
    }
    ```

### Migrating from other Loggers

If you're migrating from other Loggers, there are few key points to be aware of: [Service parameter](#the-service-parameter), [Inheriting Loggers](#inheriting-loggers), [Overriding Log records](#overriding-log-records), and [Logging exceptions](#logging-exceptions).

#### The service parameter

Service is what defines the Logger name, including what the Lambda function is responsible for, or part of (e.g payment service).

For Logger, the `service` is the logging key customers can use to search log operations for one or more functions - For example, **search for all errors, or messages like X, where service is payment**.

??? tip "Logging output example"
    ```json hl_lines="5"
    {
       "timestamp": "2020-05-24 18:17:33,774",
       "level": "DEBUG",
       "location": "collect.handler:1",
       "service": "payment",
       "lambda_function_name": "test",
       "lambda_function_memory_size": 128,
       "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
       "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
       "cold_start": true,
       "sampling_rate": 0.1,
       "message": "Verifying whether order_id is present"
    }
	```

#### Inheriting Loggers

> Python Logging hierarchy happens via the dot notation: `service`, `service.child`, `service.child_2`

For inheritance, Logger uses a `child=True` parameter along with `service` being the same value across Loggers.

For child Loggers, we introspect the name of your module where `Logger(child=True, service="name")` is called, and we name your Logger as **{service}.{filename}**.

A common issue when migrating from other Loggers is that `service` might be defined in the parent Logger (no child param), and not defined in the child Logger:

=== "incorrect_logger_inheritance.py"

    ```python hl_lines="4 10"
    import my_module
    from aws_lambda_powertools import Logger

    logger = Logger(service="payment")
    ...

    # my_module.py
    from aws_lambda_powertools import Logger

    logger = Logger(child=True)
    ```
=== "correct_logger_inheritance.py"

    ```python hl_lines="4 10"
    import my_module
    from aws_lambda_powertools import Logger

    logger = Logger(service="payment")
    ...

    # my_module.py
    from aws_lambda_powertools import Logger

    logger = Logger(service="payment", child=True)
    ```

In this case, Logger will register a Logger named `payment`, and a Logger named `service_undefined`. The latter isn't inheriting from the parent, and will have no handler, resulting in no message being logged to standard output.

!!! tip
	This can be fixed by either ensuring both has the `service` value as `payment`, or simply use the environment variable `POWERTOOLS_SERVICE_NAME` to ensure service value will be the same across all Loggers when not explicitly set.

#### Overriding Log records

You might want to continue to use the same date formatting style, or override `location` to display the `package.function_name:line_number` as you previously had.

Logger allows you to either change the format or suppress the following keys altogether at the initialization: `location`, `timestamp`, `level`, `xray_trace_id`, and `datefmt`. However, `sampling_rate` key is part of the specification and cannot be suppressed.

!!! note "`xray_trace_id` logging key"
	This key is only added if X-Ray Tracing is enabled for your Lambda function. Once enabled, this key allows the integration between CloudWatch Logs and Service Lens.

=== "lambda_handler.py"
	> We honour standard [logging library string formats](https://docs.python.org/3/howto/logging.html#displaying-the-date-time-in-messages).

    ```python hl_lines="4 7"
    from aws_lambda_powertools import Logger

    # override default values for location and timestamp format
    logger = Logger(location="[%(funcName)s] %(module)s", datefmt="%m/%d/%Y %I:%M:%S %p")

    # suppress location key
    logger = Logger(stream=stdout, location=None)
    ```
=== "Example CloudWatch Logs excerpt"
	```json hl_lines="3 5"
	{
		"level": "INFO",
		"location": "[<module>] scratch",
		"message": "hello world",
		"timestamp": "02/09/2021 09:25:17 AM",
		"service": "service_undefined",
		"sampling_rate": 0.0
	}
	```


##### Reordering log records position

You can also change the order of the following log record keys via the `log_record_order` parameter: `level`, `location`, `message`, `xray_trace_id`, and `timestamp`

=== "lambda_handler.py"

    ```python hl_lines="4 7"
    from aws_lambda_powertools import Logger

    # make message as the first key
    logger = Logger(stream=stdout, log_record_order=["message"])

    # Default key sorting order
    # Logger(stream=stdout, log_record_order=["level","location","message","timestamp"])
    ```
=== "Example CloudWatch Logs excerpt"
	```json hl_lines="3 5"
	{
		"message": "hello world",
		"level": "INFO",
		"location": "[<module>]:6",
		"timestamp": "2021-02-09 09:36:12,280",
		"service": "service_undefined",
		"sampling_rate": 0.0
	}
	```

## Testing your code

When unit testing your code that makes use of `inject_lambda_context` decorator, you need to pass a dummy Lambda Context, or else Logger will fail.

This is a Pytest sample that provides the minimum information necessary for Logger to succeed:

=== "fake_lambda_context_for_logger.py"
	Note that dataclasses are available in Python 3.7+ only.

    ```python
	from dataclasses import dataclass

	import pytest

    @pytest.fixture
    def lambda_context():
		@dataclass
		class LambdaContext:
			function_name: str = "test"
			memory_limit_in_mb: int = 128
			invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
			aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        return LambdaContext()

    def test_lambda_handler(lambda_context):
        test_event = {'test': 'event'}
        your_lambda_handler(test_event, lambda_context) # this will now have a Context object populated
    ```
=== "fake_lambda_context_for_logger_py36.py"
    ```python
	from collections import namedtuple

	import pytest

    @pytest.fixture
    def lambda_context():
        lambda_context = {
            "function_name": "test",
            "memory_limit_in_mb": 128,
            "invoked_function_arn": "arn:aws:lambda:eu-west-1:809313241:function:test",
            "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
        }

        return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())

    def test_lambda_handler(lambda_context):
        test_event = {'test': 'event'}

		# this will now have a Context object populated
		your_lambda_handler(test_event, lambda_context)
    ```

### Pytest live log feature

Pytest Live Log feature duplicates emitted log messages in order to style log statements according to their levels, for this to work use `POWERTOOLS_LOG_DEDUPLICATION_DISABLED` env var.

```bash
POWERTOOLS_LOG_DEDUPLICATION_DISABLED="1" pytest -o log_cli=1
```

!!! warning
    This feature should be used with care, as it explicitly disables our ability to filter propagated messages to the root logger (if configured).

## Built-in Correlation ID expressions

> New in 1.12.0

You can use any of the following built-in JMESPath expressions as part of [inject_lambda_context decorator](#setting-a-correlation-id).

!!! note "Escaping necessary for the `-` character"
	Any object key named with `-` must be escaped, for example **`request.headers."x-amzn-trace-id"`**.

Name | Expression | Description
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
**API_GATEWAY_REST** | `"requestContext.requestId"` | API Gateway REST API request ID
**API_GATEWAY_HTTP** | `"requestContext.requestId"` | API Gateway HTTP API request ID
**APPSYNC_RESOLVER** | `'request.headers."x-amzn-trace-id"'` | AppSync X-Ray Trace ID
**APPLICATION_LOAD_BALANCER** | `'headers."x-amzn-trace-id"'` | ALB X-Ray Trace ID
**EVENT_BRIDGE** | `"id"` | EventBridge Event ID

## FAQ

**How can I enable boto3 and botocore library logging?**

You can enable the `botocore` and `boto3` logs by using the `set_stream_logger` method, this method will add a stream handler
for the given name and level to the logging module. By default, this logs all boto3 messages to stdout.

=== "log_botocore_and_boto3.py"

    ```python hl_lines="6-7"
    from typing import Dict, List
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools import Logger

    import boto3
    boto3.set_stream_logger()
    boto3.set_stream_logger('botocore')

    logger = Logger()
    client = boto3.client('s3')


    def handler(event: Dict, context: LambdaContext) -> List:
        response = client.list_buckets()

        return response.get("Buckets", [])
    ```

**What's the difference between `structure_log` and `extra`?**

Keys added with `structure_log` will persist across multiple log messages while keys added via `extra` will only be available in a given log message operation.

Here's an example where we persist `payment_id` not `request_id`. Note that `payment_id` remains in both log messages while `booking_id` is only available in the first message.

=== "lambda_handler.py"

    ```python hl_lines="4 8"
    from aws_lambda_powertools import Logger

    logger = Logger(service="payment")
    logger.structure_logs(append=True, payment_id="123456789")

    try:
        booking_id = book_flight()
        logger.info("Flight booked successfully", extra={ "booking_id": booking_id})
    except BookingReservationError:
        ...

    logger.info("goodbye")
    ```
=== "Example CloudWatch Logs excerpt"

	```json hl_lines="8-9 18"
	{
		"level": "INFO",
		"location": "<module>:5",
		"message": "Flight booked successfully",
		"timestamp": "2021-01-12 14:09:10,859",
		"service": "payment",
		"sampling_rate": 0.0,
		"payment_id": "123456789",
		"booking_id": "75edbad0-0857-4fc9-b547-6180e2f7959b"
	},
	{
		"level": "INFO",
		"location": "<module>:6",
		"message": "goodbye",
		"timestamp": "2021-01-12 14:09:10,860",
		"service": "payment",
		"sampling_rate": 0.0,
		"payment_id": "123456789"
	}
	```
