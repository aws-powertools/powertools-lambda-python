# Metrics
## Core utility

Metrics creates custom metrics asynchronously by logging metrics to standard output following Amazon CloudWatch Embedded Metric Format (EMF).

These metrics can be visualized through [Amazon CloudWatch Console](https://console.aws.amazon.com/cloudwatch/).

**Key features**

* Aggregate up to 100 metrics using a single CloudWatch EMF object (large JSON blob)
* Validate against common metric definitions mistakes (metric unit, values, max dimensions, max metrics, etc)
* Metrics are created asynchronously by CloudWatch service, no custom stacks needed
* Context manager to create an one off metric with a different dimension

## Initialization

Set `POWERTOOLS_SERVICE_NAME` and `POWERTOOLS_METRICS_NAMESPACE` env vars as a start - Here is an example using AWS Serverless Application Model (SAM)

=== "template.yml"

    ```yaml hl_lines="9 10"
    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
            ...
            Runtime: python3.8
            Environment:
                Variables:
                    POWERTOOLS_SERVICE_NAME: payment
                    POWERTOOLS_METRICS_NAMESPACE: ServerlessAirline
    ```

We recommend you use your application or main service as a metric namespace.
You can explicitly set a namespace name via `namespace` param or via `POWERTOOLS_METRICS_NAMESPACE` env var.

This sets **namespace** key that will be used for all metrics.
You can also pass a service name via `service` param or `POWERTOOLS_SERVICE_NAME` env var. This will create a dimension with the service name.

=== "app.py"

    ```python hl_lines="5"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    # POWERTOOLS_METRICS_NAMESPACE and POWERTOOLS_SERVICE_NAME defined
    metrics = Metrics() # highlight-line

    # Explicit definition
    Metrics(namespace="ServerlessAirline", service="orders")  # creates a default dimension {"service": "orders"} under the namespace "ServerlessAirline"


    ```

You can initialize Metrics anywhere in your code as many times as you need - It'll keep track of your aggregate metrics in memory.

## Creating metrics

You can create metrics using `add_metric`, and manually create dimensions for all your aggregate metrics using `add_dimension`.

=== "app.py"

    ```python hl_lines="5 6"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(namespace="ExampleApplication", service="booking")
    metrics.add_dimension(name="environment", value="prod")
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
    ```

`MetricUnit` enum facilitate finding a supported metric unit by CloudWatch. Alternatively, you can pass the value as a string if you already know them e.g. "Count".

CloudWatch EMF supports a max of 100 metrics. Metrics utility will flush all metrics when adding the 100th metric while subsequent metrics will be aggregated into a new EMF object, for your convenience.

## Creating a metric with a different dimension

CloudWatch EMF uses the same dimensions across all your metrics. Use `single_metric` if you have a metric that should have different dimensions.


!!! info
    Generally, this would be an edge case since you [pay for unique metric](https://aws.amazon.com/cloudwatch/pricing/"). Keep the following formula in mind:

    **unique metric = (metric_name + dimension_name + dimension_value)**

=== "single_metric.py"

    ```python hl_lines="4"
    from aws_lambda_powertools import single_metric
    from aws_lambda_powertools.metrics import MetricUnit

    with single_metric(name="ColdStart", unit=MetricUnit.Count, value=1, namespace="ExampleApplication") as metric: # highlight-line
        metric.add_dimension(name="function_context", value="$LATEST")
        ...
    ```

## Adding metadata

You can use `add_metadata` for advanced use cases, where you want to metadata as part of the serialized metrics object.

!!! info
    **This will not be available during metrics visualization** - Use **dimensions** for this purpose

=== "app.py"

    ```python hl_lines="6"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(namespace="ExampleApplication", service="booking")
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="booking_id", value="booking_uuid")
    ```

This will be available in CloudWatch Logs to ease operations on high cardinal data.


??? example "Excerpt output in CloudWatch Logs"

    ```json hl_lines="23"
    {
        "SuccessfulBooking": 1.0,
        "_aws": {
            "Timestamp": 1592234975665,
            "CloudWatchMetrics": [
                {
                    "Namespace": "ExampleApplication",
                    "Dimensions": [
                        [
                            "service"
                        ]
                    ],
                    "Metrics": [
                        {
                            "Name": "SuccessfulBooking",
                            "Unit": "Count"
                        }
                    ]
                }
            ]
        },
        "service": "booking",
        "booking_id": "booking_uuid"
    }
    ```

## Flushing metrics

As you finish adding all your metrics, you need to serialize and flush them to standard output. You can do that right before you return your response to the caller via `log_metrics`.

=== "lambda_handler.py"

    ```python hl_lines="7"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(service="ExampleService")
    metrics.add_metric(name="ColdStart", unit="Count", value=1)

    @metrics.log_metrics
    def lambda_handler(evt, ctx):
        metrics.add_dimension(name="service", value="booking")
        metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
        ...
    ```

`log_metrics` decorator **validates**, **serializes**, and **flushes** all your metrics. During metrics validation, if no metrics are provided then a warning will be logged, but no exception will be raised.

If metrics are provided, and any of the following criteria are not met, `SchemaValidationError` exception will be raised:

* Minimum of 1 dimension
* Maximum of 9 dimensions
* Namespace is set, and no more than one
* Metric units must be [supported by CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)

If you want to ensure that at least one metric is emitted, you can pass `raise_on_empty_metrics` to the **log_metrics** decorator:

=== "lambda_handler.py"

    ```python hl_lines="3"
    from aws_lambda_powertools.metrics import Metrics

    @metrics.log_metrics(raise_on_empty_metrics=True) # highlight-line
    def lambda_handler(evt, ctx):
        ...
    ```

!!! info
    If you expect your function to execute without publishing metrics every time, you can suppress the warning with **`warnings.filterwarnings("ignore", "No metrics to publish*")`**.

!!! warning
    When nesting multiple middlewares, you should use **`log_metrics` as your last decorator wrapping all subsequent ones**.

=== "lambda_handler_nested_middlewares.py"

    ```python hl_lines="7-8"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(namespace="ExampleApplication", service="booking")
    metrics.add_metric(name="ColdStart", unit="Count", value=1)

    @metrics.log_metrics
    @tracer.capture_lambda_handler
    def lambda_handler(evt, ctx):
        metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
        ...
    ```

## Flushing metrics manually

If you prefer not to use `log_metrics` because you might want to encapsulate additional logic when doing so, you can manually flush and clear metrics as follows:

!!! warning
    Metrics, dimensions and namespace validation still applies.

=== "manual_metric_serialization.py"

    ```python hl_lines="8-10"
    import json
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(namespace="ExampleApplication", service="booking")
    metrics.add_metric(name="ColdStart", unit="Count", value=1)

    your_metrics_object = metrics.serialize_metric_set()
    metrics.clear_metrics()
    print(json.dumps(your_metrics_object))
    ```

## Capturing cold start metric

You can capture cold start metrics automatically with `log_metrics` via `capture_cold_start_metric` param.

=== "lambda_handler.py"

    ```python hl_lines="6"
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit

    metrics = Metrics(service="ExampleService")

    @metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, ctx):
        ...
    ```

If it's a cold start invocation, this feature will:

* Create a separate EMF blob solely containing a metric named `ColdStart`
* Add `function_name` and `service` dimensions

This has the advantage of keeping cold start metric separate from your application metrics.

## Testing your code

### Environment variables

Use `POWERTOOLS_METRICS_NAMESPACE` and `POWERTOOLS_SERVICE_NAME` env vars when unit testing your code to ensure metric namespace and dimension objects are created, and your code doesn't fail validation.

```bash
POWERTOOLS_SERVICE_NAME="Example" POWERTOOLS_METRICS_NAMESPACE="Application" python -m pytest
```

If you prefer setting environment variable for specific tests, and are using Pytest, you can use [monkeypatch](https://docs.pytest.org/en/latest/monkeypatch.html) fixture:

=== "pytest_env_var.py"

    ```python
    def test_namespace_env_var(monkeypatch):
        # Set POWERTOOLS_METRICS_NAMESPACE before initializating Metrics
        monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", namespace)

        metrics = Metrics()
        ...
    ```

> Ignore this, if you are explicitly setting namespace/default dimension via `namespace` and `service` parameters: `metrics = Metrics(namespace=ApplicationName, service=ServiceName)`

### Clearing metrics

`Metrics` keep metrics in memory across multiple instances. If you need to test this behaviour, you can use the following Pytest fixture to ensure metrics are reset incl. cold start:

=== "pytest_metrics_reset_fixture.py"

    ```python
    @pytest.fixture(scope="function", autouse=True)
    def reset_metric_set():
        # Clear out every metric data prior to every test
        metrics = Metrics()
        metrics.clear_metrics()
        metrics_global.is_cold_start = True  # ensure each test has cold start
        yield
    ```
