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

| Setting           | Description                                                         | Environment variable      | Constructor parameter |
| ----------------- | ------------------------------------------------------------------- | ------------------------- | --------------------- |
| **Logging level** | Sets how verbose Logger should be (INFO, by default)                | `LOG_LEVEL`               | `level`               |
| **Service**       | Sets **service** key that will be present across all log statements | `POWERTOOLS_SERVICE_NAME` | `service`             |

```yaml hl_lines="12-13" title="AWS Serverless Application Model (SAM) example"
--8<-- "examples/logger/sam/template.yaml"
```

### Standard structured keys

Your Logger will include the following keys to your structured logging:

| Key                        | Example                               | Note                                                                                                                                 |
| -------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **level**: `str`           | `INFO`                                | Logging level                                                                                                                        |
| **location**: `str`        | `collect.handler:1`                   | Source code location where statement was executed                                                                                    |
| **message**: `Any`         | `Collecting payment`                  | Unserializable JSON values are casted as `str`                                                                                       |
| **timestamp**: `str`       | `2021-05-03 10:20:19,650+0200`        | Timestamp with milliseconds, by default uses local timezone                                                                          |
| **service**: `str`         | `payment`                             | Service name defined, by default `service_undefined`                                                                                 |
| **xray_trace_id**: `str`   | `1-5759e988-bd862e3fe1be46a994272793` | When [tracing is enabled](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html){target="_blank"}, it shows X-Ray Trace ID |
| **sampling_rate**: `float` | `0.1`                                 | When enabled, it shows sampling rate in percentage e.g. 10%                                                                          |
| **exception_name**: `str`  | `ValueError`                          | When `logger.exception` is used and there is an exception                                                                            |
| **exception**: `str`       | `Traceback (most recent call last)..` | When `logger.exception` is used and there is an exception                                                                            |

### Capturing Lambda context info

You can enrich your structured logs with key Lambda context information via `inject_lambda_context`.

=== "collect.py"

    ```python hl_lines="7"
    --8<-- "examples/logger/src/inject_lambda_context.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="8-12 17-20"
    --8<-- "examples/logger/src/inject_lambda_context_output.json"
    ```

When used, this will include the following keys:

| Key                             | Example                                                                                              |
| ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **cold_start**: `bool`          | `false`                                                                                              |
| **function_name** `str`         | `example-powertools-HelloWorldFunction-1P1Z6B39FLU73`                                                |
| **function_memory_size**: `int` | `128`                                                                                                |
| **function_arn**: `str`         | `arn:aws:lambda:eu-west-1:012345678910:function:example-powertools-HelloWorldFunction-1P1Z6B39FLU73` |
| **function_request_id**: `str`  | `899856cb-83d1-40d7-8611-9e78f15f32f4`                                                               |

### Logging incoming event

When debugging in non-production environments, you can instruct Logger to log the incoming event with `log_event` param or via `POWERTOOLS_LOGGER_LOG_EVENT` env var.

???+ warning
	This is disabled by default to prevent sensitive info being logged

```python hl_lines="7" title="Logging incoming event"
--8<-- "examples/logger/src/log_incoming_event.py"
```

### Setting a Correlation ID

You can set a Correlation ID using `correlation_id_path` param by passing a [JMESPath expression](https://jmespath.org/tutorial.html){target="_blank"}.

???+ tip
	You can retrieve correlation IDs via `get_correlation_id` method

=== "collect.py"

    ```python hl_lines="7"
    --8<-- "examples/logger/src/set_correlation_id.py"
    ```

=== "Example Event"

    ```json hl_lines="3"
    --8<-- "examples/logger/src/set_correlation_id_event.json"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="12"
    --8<-- "examples/logger/src/set_correlation_id_output.json"
    ```

#### set_correlation_id method

You can also use `set_correlation_id` method to inject it anywhere else in your code. Example below uses [Event Source Data Classes utility](../utilities/data_classes.md) to easily access events properties.

=== "collect.py"

    ```python hl_lines="11"
    --8<-- "examples/logger/src/set_correlation_id_method.py"
    ```
=== "Example Event"

    ```json hl_lines="3"
    --8<-- "examples/logger/src/set_correlation_id_method_event.json"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/set_correlation_id_method_output.json"
    ```

#### Known correlation IDs

To ease routine tasks like extracting correlation ID from popular event sources, we provide [built-in JMESPath expressions](#built-in-correlation-id-expressions).

=== "collect.py"

    ```python hl_lines="2 8"
    --8<-- "examples/logger/src/set_correlation_id_jmespath.py"
    ```

=== "Example Event"

    ```json hl_lines="3"
    --8<-- "examples/logger/src/set_correlation_id_jmespath_event.json"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="12"
    --8<-- "examples/logger/src/set_correlation_id_jmespath_output.json"
    ```

### Appending additional keys

???+ info "Info: Custom keys are persisted across warm invocations"
    Always set additional keys as part of your handler to ensure they have the latest value, or explicitly clear them with [`clear_state=True`](#clearing-all-state).

You can append additional keys using either mechanism:

* Persist new keys across all future log messages via `append_keys` method
* Add additional keys on a per log message basis via `extra` parameter

#### append_keys method

???+ note
	`append_keys` replaces `structure_logs(append=True, **kwargs)` method. structure_logs will be removed in v2.

You can append your own keys to your existing Logger via `append_keys(**additional_key_values)` method.

=== "collect.py"

    ```python hl_lines="12"
    --8<-- "examples/logger/src/append_keys.py"
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/append_keys_output.json"
    ```

???+ tip "Tip: Logger will automatically reject any key with a None value"
    If you conditionally add keys depending on the payload, you can follow the example above.

    This example will add `order_id` if its value is not empty, and in subsequent invocations where `order_id` might not be present it'll remove it from the Logger.

#### extra parameter

Extra parameter is available for all log levels' methods, as implemented in the standard logging library - e.g. `logger.info, logger.warning`.

It accepts any dictionary, and all keyword arguments will be added as part of the root structure of the logs for that log statement.

???+ info
    Any keyword argument added using `extra` will not be persisted for subsequent messages.

=== "extra_parameter.py"

    ```python hl_lines="9"
    --8<-- "examples/logger/src/append_keys_extra.py"
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/append_keys_extra_output.json"
    ```

### Removing additional keys

You can remove any additional key from Logger state using `remove_keys`.

=== "collect.py"

    ```python hl_lines="11"
    --8<-- "examples/logger/src/remove_keys.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/remove_keys_output.json"
    ```

#### Clearing all state

Logger is commonly initialized in the global scope. Due to [Lambda Execution Context reuse](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-context.html), this means that custom keys can be persisted across invocations. If you want all custom keys to be deleted, you can use `clear_state=True` param in `inject_lambda_context` decorator.

???+ tip "Tip: When is this useful?"
    It is useful when you add multiple custom keys conditionally, instead of setting a default `None` value if not present. Any key with `None` value is automatically removed by Logger.

???+ danger "Danger: This can have unintended side effects if you use Layers"
    Lambda Layers code is imported before the Lambda handler.

    This means that `clear_state=True` will instruct Logger to remove any keys previously added before Lambda handler execution proceeds.

    You can either avoid running any code as part of Lambda Layers global scope, or override keys with their latest value as part of handler's execution.

=== "collect.py"

    ```python hl_lines="7 10"
    --8<-- "examples/logger/src/clear_state.py"
    ```

=== "#1 request"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/clear_state_event_one.json"
    ```

=== "#2 request"

    ```json hl_lines="7"
    --8<-- "examples/logger/src/clear_state_event_two.json"
    ```

### Logging exceptions

Use `logger.exception` method to log contextual information about exceptions. Logger will include `exception_name` and `exception` keys to aid troubleshooting and error enumeration.

???+ tip
    You can use your preferred Log Analytics tool to enumerate and visualize exceptions across all your services using `exception_name` key.

=== "collect.py"

    ```python hl_lines="15"
    --8<-- "examples/logger/src/logging_exceptions.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="7-8"
    --8<-- "examples/logger/src/logging_exceptions_output.json"
    ```

## Advanced

### Built-in Correlation ID expressions

You can use any of the following built-in JMESPath expressions as part of [inject_lambda_context decorator](#setting-a-correlation-id).

???+ note "Note: Any object key named with `-` must be escaped"
    For example, **`request.headers."x-amzn-trace-id"`**.

| Name                          | Expression                            | Description                     |
| ----------------------------- | ------------------------------------- | ------------------------------- |
| **API_GATEWAY_REST**          | `"requestContext.requestId"`          | API Gateway REST API request ID |
| **API_GATEWAY_HTTP**          | `"requestContext.requestId"`          | API Gateway HTTP API request ID |
| **APPSYNC_RESOLVER**          | `'request.headers."x-amzn-trace-id"'` | AppSync X-Ray Trace ID          |
| **APPLICATION_LOAD_BALANCER** | `'headers."x-amzn-trace-id"'`         | ALB X-Ray Trace ID              |
| **EVENT_BRIDGE**              | `"id"`                                | EventBridge Event ID            |

### Reusing Logger across your code

Similar to [Tracer](./tracer.md#reusing-tracer-across-your-code), a new instance that uses the same `service` name - env var or explicit parameter - will reuse a previous Logger instance. Just like `logging.getLogger("logger_name")` would in the standard library if called with the same logger name.

Notice in the CloudWatch Logs output how `payment_id` appeared as expected when logging in `collect.py`.

=== "collect.py"

    ```python hl_lines="1 9 11 12"
    --8<-- "examples/logger/src/logger_reuse.py"
    ```

=== "payment.py"

    ```python hl_lines="3 7"
    --8<-- "examples/logger/src/logger_reuse_payment.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="12"
    --8<-- "examples/logger/src/logger_reuse_output.json"
    ```

???+ note "Note: About Child Loggers"
    Coming from standard library, you might be used to use `logging.getLogger(__name__)`. This will create a new instance of a Logger with a different name.

    In Powertools, you can have the same effect by using `child=True` parameter: `Logger(child=True)`. This creates a new Logger instance named after `service.<module>`. All state changes will be propagated bi-directonally between Child and Parent.

    For that reason, there could be side effects depending on the order the Child Logger is instantiated, because Child Loggers don't have a handler.

    For example, if you instantiated a Child Logger and immediately used `logger.append_keys/remove_keys/set_correlation_id` to update logging state, this might fail if the Parent Logger wasn't instantiated.

    In this scenario, you can either ensure any calls manipulating state are only called when a Parent Logger is instantiated (example above), or refrain from using `child=True` parameter altogether.

### Sampling debug logs

Use sampling when you want to dynamically change your log level to **DEBUG** based on a **percentage of your concurrent/cold start invocations**.

You can use values ranging from `0.0` to `1` (100%) when setting `POWERTOOLS_LOGGER_SAMPLE_RATE` env var, or `sample_rate` parameter in Logger.

???+ tip "Tip: When is this useful?"
    Let's imagine a sudden spike increase in concurrency triggered a transient issue downstream. When looking into the logs you might not have enough information, and while you can adjust log levels it might not happen again.

    This feature takes into account transient issues where additional debugging information can be useful.

Sampling decision happens at the Logger initialization. This means sampling may happen significantly more or less than depending on your traffic patterns, for example a steady low number of invocations and thus few cold starts.

???+ note
	Open a [feature request](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=) if you want Logger to calculate sampling for every invocation

=== "collect.py"

    ```python hl_lines="6 10"
    --8<-- "examples/logger/src/logger_reuse.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="3 5 13 16 25"
    --8<-- "examples/logger/src/sampling_debug_logs_output.json"
    ```

### LambdaPowertoolsFormatter

Logger propagates a few formatting configurations to the built-in `LambdaPowertoolsFormatter` logging formatter.

If you prefer configuring it separately, or you'd want to bring this JSON Formatter to another application, these are the supported settings:

| Parameter                    | Description                                                                                                              | Default                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| **`json_serializer`**        | function to serialize `obj` to a JSON formatted `str`                                                                    | `json.dumps`                                                  |
| **`json_deserializer`**      | function to deserialize `str`, `bytes`, `bytearray` containing a JSON document to a Python obj                           | `json.loads`                                                  |
| **`json_default`**           | function to coerce unserializable values, when no custom serializer/deserializer is set                                  | `str`                                                         |
| **`datefmt`**                | string directives (strftime) to format log timestamp                                                                     | `%Y-%m-%d %H:%M:%S,%F%z`, where `%F` is a custom ms directive |
| **`use_datetime_directive`** | format the `datefmt` timestamps using `datetime`, not `time`  (also supports the custom `%F` directive for milliseconds) | `False`                                                       |
| **`utc`**                    | set logging timestamp to UTC                                                                                             | `False`                                                       |
| **`log_record_order`**       | set order of log keys when logging                                                                                       | `["level", "location", "message", "timestamp"]`               |
| **`kwargs`**                 | key-value to be included in log messages                                                                                 | `None`                                                        |

```python hl_lines="2 7-8" title="Pre-configuring Lambda Powertools Formatter"
--8<-- "examples/logger/src/powertools_formatter_setup.py"
```

### Migrating from other Loggers

If you're migrating from other Loggers, there are few key points to be aware of: [Service parameter](#the-service-parameter), [Inheriting Loggers](#inheriting-loggers), [Overriding Log records](#overriding-log-records), and [Logging exceptions](#logging-exceptions).

#### The service parameter

Service is what defines the Logger name, including what the Lambda function is responsible for, or part of (e.g payment service).

For Logger, the `service` is the logging key customers can use to search log operations for one or more functions - For example, **search for all errors, or messages like X, where service is payment**.

#### Inheriting Loggers

??? tip "Tip: Prefer [Logger Reuse feature](#reusing-logger-across-your-code) over inheritance unless strictly necessary, [see caveats.](#reusing-logger-across-your-code)"

> Python Logging hierarchy happens via the dot notation: `service`, `service.child`, `service.child_2`

For inheritance, Logger uses a `child=True` parameter along with `service` being the same value across Loggers.

For child Loggers, we introspect the name of your module where `Logger(child=True, service="name")` is called, and we name your Logger as **{service}.{filename}**.

???+ danger
    A common issue when migrating from other Loggers is that `service` might be defined in the parent Logger (no child param), and not defined in the child Logger:

=== "incorrect_logger_inheritance.py"

    ```python hl_lines="1 9"
    --8<-- "examples/logger/src/logging_inheritance_bad.py"
    ```

=== "my_other_module.py"

    ```python hl_lines="1 9"
    --8<-- "examples/logger/src/logging_inheritance_module.py"
    ```

In this case, Logger will register a Logger named `payment`, and a Logger named `service_undefined`. The latter isn't inheriting from the parent, and will have no handler, resulting in no message being logged to standard output.

???+ tip
    This can be fixed by either ensuring both has the `service` value as `payment`, or simply use the environment variable `POWERTOOLS_SERVICE_NAME` to ensure service value will be the same across all Loggers when not explicitly set.

Do this instead:

=== "correct_logger_inheritance.py"

    ```python hl_lines="1 9"
    --8<-- "examples/logger/src/logging_inheritance_good.py"
    ```

=== "my_other_module.py"

    ```python hl_lines="1 9"
    --8<-- "examples/logger/src/logging_inheritance_module.py"
    ```

#### Overriding Log records

???+ tip
	Use `datefmt` for custom date formats - We honour standard [logging library string formats](https://docs.python.org/3/howto/logging.html#displaying-the-date-time-in-messages){target="_blank"}.

	Prefer using [datetime string formats](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes){target="_blank"}? Set `use_datetime_directive` at Logger constructor or at [Lambda Powertools Formatter](#lambdapowertoolsformatter).

You might want to continue to use the same date formatting style, or override `location` to display the `package.function_name:line_number` as you previously had.

Logger allows you to either change the format or suppress the following keys altogether at the initialization: `location`, `timestamp`, `level`, `xray_trace_id`.

=== "lambda_handler.py"

    ```python hl_lines="7 10"
    --8<-- "examples/logger/src/overriding_log_records.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="3 5"
    --8<-- "examples/logger/src/overriding_log_records_output.json"
    ```

#### Reordering log keys position

You can change the order of [standard Logger keys](#standard-structured-keys) or any keys that will be appended later at runtime via the `log_record_order` parameter.

=== "app.py"

    ```python hl_lines="5 8"
    --8<-- "examples/logger/src/reordering_log_keys.py"
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="3 10"
    --8<-- "examples/logger/src/reordering_log_keys_output.json"
    ```

#### Setting timestamp to UTC

By default, this Logger and standard logging library emits records using local time timestamp. You can override this behavior via `utc` parameter:

=== "app.py"

    ```python hl_lines="6"
    --8<-- "examples/logger/src/setting_utc_timestamp.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="6 13"
    --8<-- "examples/logger/src/setting_utc_timestamp_output.json"
    ```

#### Custom function for unserializable values

By default, Logger uses `str` to handle values non-serializable by JSON. You can override this behavior via `json_default` parameter by passing a Callable:

=== "app.py"

    ```python hl_lines="6 17"
    --8<-- "examples/logger/src/unserializable_values.py"
    ```

=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="4-6"
    --8<-- "examples/logger/src/unserializable_values_output.json"
    ```

#### Bring your own handler

By default, Logger uses StreamHandler and logs to standard output. You can override this behaviour via `logger_handler` parameter:

```python hl_lines="3-4 9 12" title="Configure Logger to output to a file"
import logging
from pathlib import Path

from aws_lambda_powertools import Logger

log_file = Path("/tmp/log.json")
log_file_handler = logging.FileHandler(filename=log_file)
logger = Logger(service="payment", logger_handler=log_file_handler)

logger.info("Collecting payment")
```

#### Bring your own formatter

By default, Logger uses [LambdaPowertoolsFormatter](#lambdapowertoolsformatter) that persists its custom structure between non-cold start invocations. There could be scenarios where the existing feature set isn't sufficient to your formatting needs.

???+ info
    The most common use cases are remapping keys by bringing your existing schema, and redacting sensitive information you know upfront.

For these, you can override the `serialize` method from [LambdaPowertoolsFormatter](#lambdapowertoolsformatter).

=== "custom_formatter.py"

    ```python hl_lines="6-7 12"
    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter

    from typing import Dict

    class CustomFormatter(LambdaPowertoolsFormatter):
        def serialize(self, log: Dict) -> str:
            """Serialize final structured log dict to JSON str"""
            log["event"] = log.pop("message")  # rename message key to event
            return self.json_serializer(log)   # use configured json serializer

    logger = Logger(service="example", logger_formatter=CustomFormatter())
    logger.info("hello")
    ```

=== "Example CloudWatch Logs excerpt"
	```json hl_lines="5"
	{
		"level": "INFO",
		"location": "<module>:16",
		"timestamp": "2021-12-30 13:41:53,413+0100",
		"event": "hello"
	}
	```

The `log` argument is the final log record containing [our standard keys](#standard-structured-keys), optionally [Lambda context keys](#capturing-lambda-context-info), and any custom key you might have added via [append_keys](#append_keys-method) or the [extra parameter](#extra-parameter).

For exceptional cases where you want to completely replace our formatter logic, you can subclass `BasePowertoolsFormatter`.

???+ warning
    You will need to implement `append_keys`, `clear_state`, override `format`, and optionally `remove_keys` to keep the same feature set Powertools Logger provides. This also means keeping state of logging keys added.

=== "collect.py"

    ```python hl_lines="5 7 9-10 13 17 21 24 35"
    import logging
    from typing import Iterable, List, Optional

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.logging.formatter import BasePowertoolsFormatter

    class CustomFormatter(BasePowertoolsFormatter):
        def __init__(self, log_record_order: Optional[List[str]], *args, **kwargs):
            self.log_record_order = log_record_order or ["level", "location", "message", "timestamp"]
            self.log_format = dict.fromkeys(self.log_record_order)
            super().__init__(*args, **kwargs)

        def append_keys(self, **additional_keys):
            # also used by `inject_lambda_context` decorator
            self.log_format.update(additional_keys)

        def remove_keys(self, keys: Iterable[str]):
            for key in keys:
                self.log_format.pop(key, None)

        def clear_state(self):
            self.log_format = dict.fromkeys(self.log_record_order)

        def format(self, record: logging.LogRecord) -> str:  # noqa: A003
            """Format logging record as structured JSON str"""
            return json.dumps(
                {
                    "event": super().format(record),
                    "timestamp": self.formatTime(record),
                    "my_default_key": "test",
                    **self.log_format,
                }
            )

    logger = Logger(service="payment", logger_formatter=CustomFormatter())

    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Collecting payment")
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="2-4"
    {
        "event": "Collecting payment",
        "timestamp": "2021-05-03 11:47:12,494",
        "my_default_key": "test",
        "cold_start": true,
        "lambda_function_name": "test",
        "lambda_function_memory_size": 128,
        "lambda_function_arn": "arn:aws:lambda:eu-west-1:12345678910:function:test",
        "lambda_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72"
    }
    ```

#### Bring your own JSON serializer

By default, Logger uses `json.dumps` and `json.loads` as serializer and deserializer respectively. There could be scenarios where you are making use of alternative JSON libraries like [orjson](https://github.com/ijl/orjson){target="_blank"}.

As parameters don't always translate well between them, you can pass any callable that receives a `Dict` and return a `str`:

```python hl_lines="1 5-6 9-10" title="Using Rust orjson library as serializer"
import orjson

from aws_lambda_powertools import Logger

custom_serializer = orjson.dumps
custom_deserializer = orjson.loads

logger = Logger(service="payment",
			json_serializer=custom_serializer,
			json_deserializer=custom_deserializer
)

# when using parameters, you can pass a partial
# custom_serializer=functools.partial(orjson.dumps, option=orjson.OPT_SERIALIZE_NUMPY)
```

## Testing your code

### Inject Lambda Context

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

???+ tip
	Check out the built-in [Pytest caplog fixture](https://docs.pytest.org/en/latest/how-to/logging.html){target="_blank"} to assert plain log messages

### Pytest live log feature

Pytest Live Log feature duplicates emitted log messages in order to style log statements according to their levels, for this to work use `POWERTOOLS_LOG_DEDUPLICATION_DISABLED` env var.

```bash title="Disabling log deduplication to use Pytest live log"
POWERTOOLS_LOG_DEDUPLICATION_DISABLED="1" pytest -o log_cli=1
```

???+ warning
    This feature should be used with care, as it explicitly disables our ability to filter propagated messages to the root logger (if configured).

## FAQ

**How can I enable boto3 and botocore library logging?**

You can enable the `botocore` and `boto3` logs by using the `set_stream_logger` method, this method will add a stream handler
for the given name and level to the logging module. By default, this logs all boto3 messages to stdout.

```python hl_lines="6-7" title="Enabling AWS SDK logging"
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

**How can I enable powertools logging for imported libraries?**

You can copy the Logger setup to all or sub-sets of registered external loggers. Use the `copy_config_to_registered_logger` method to do this. By default all registered loggers will be modified. You can change this behaviour by providing `include` and `exclude` attributes. You can also provide optional `log_level` attribute external loggers will be configured with.

```python hl_lines="10" title="Cloning Logger config to all other registered standard loggers"
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import utils

logger = Logger()

external_logger = logging.logger()

utils.copy_config_to_registered_loggers(source_logger=logger)
external_logger.info("test message")
```

**What's the difference between `append_keys` and `extra`?**

Keys added with `append_keys` will persist across multiple log messages while keys added via `extra` will only be available in a given log message operation.

Here's an example where we persist `payment_id` not `request_id`. Note that `payment_id` remains in both log messages while `booking_id` is only available in the first message.

=== "lambda_handler.py"

    ```python hl_lines="6 10"
    from aws_lambda_powertools import Logger

    logger = Logger(service="payment")

    def handler(event, context):
        logger.append_keys(payment_id="123456789")

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
        "location": "<module>:10",
        "message": "Flight booked successfully",
        "timestamp": "2021-01-12 14:09:10,859",
        "service": "payment",
        "sampling_rate": 0.0,
        "payment_id": "123456789",
        "booking_id": "75edbad0-0857-4fc9-b547-6180e2f7959b"
    },
    {
        "level": "INFO",
        "location": "<module>:14",
        "message": "goodbye",
        "timestamp": "2021-01-12 14:09:10,860",
        "service": "payment",
        "sampling_rate": 0.0,
        "payment_id": "123456789"
    }
    ```

**How do I aggregate and search Powertools logs across accounts?**

As of now, ElasticSearch (ELK) or 3rd party solutions are best suited to this task. Please refer to this [discussion for more details](https://github.com/awslabs/aws-lambda-powertools-python/issues/460)
