---
title: Metrics
description: Core utility
---

Metrics creates custom metrics asynchronously by logging metrics to standard output following [Amazon CloudWatch Embedded Metric Format (EMF)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html).

These metrics can be visualized through [Amazon CloudWatch Console](https://console.aws.amazon.com/cloudwatch/).

## Key features

* Aggregate up to 100 metrics using a single CloudWatch EMF object (large JSON blob)
* Validate against common metric definitions mistakes (metric unit, values, max dimensions, max metrics, etc)
* Metrics are created asynchronously by CloudWatch service, no custom stacks needed
* Context manager to create a one off metric with a different dimension

## Terminologies

If you're new to Amazon CloudWatch, there are two terminologies you must be aware of before using this utility:

* **Namespace**. It's the highest level container that will group multiple metrics from multiple services for a given application, for example `ServerlessEcommerce`.
* **Dimensions**. Metrics metadata in key-value format. They help you slice and dice metrics visualization, for example `ColdStart` metric by Payment `service`.

<figure>
  <img src="../../media/metrics_terminology.png" />
  <figcaption>Metric terminology, visually explained</figcaption>
</figure>

## Getting started

Metric has two global settings that will be used across all metrics emitted:

| Setting              | Description                                                                     | Environment variable           | Constructor parameter |
| -------------------- | ------------------------------------------------------------------------------- | ------------------------------ | --------------------- |
| **Metric namespace** | Logical container where all metrics will be placed e.g. `ServerlessAirline`     | `POWERTOOLS_METRICS_NAMESPACE` | `namespace`           |
| **Service**          | Optionally, sets **service** metric dimension across all metrics e.g. `payment` | `POWERTOOLS_SERVICE_NAME`      | `service`             |

???+ tip
    Use your application or main service as the metric namespace to easily group all metrics.

???+ example
	**AWS Serverless Application Model (SAM)**

    === "template.yml"

        ```yaml hl_lines="12-13"
        --8<-- "docs/examples/core/metrics/template.yml"
        ```

    === "app.py"

        ```python hl_lines="4 6-8"
        --8<-- "docs/examples/core/metrics/example_app.py"
        ```

### Creating metrics

You can create metrics using `add_metric`, and you can create dimensions for all your aggregate metrics using `add_dimension` method.

???+ tip
	You can initialize Metrics in any other module too. It'll keep track of your aggregate metrics in memory to optimize costs (one blob instead of multiples).

=== "Metrics"

    ```python hl_lines="9"
    --8<-- "docs/examples/core/metrics/metrics_app.py"
    ```
=== "Metrics with custom dimensions"

    ```python hl_lines="9-10"
    --8<-- "docs/examples/core/metrics/metrics_custom_dimensions_app.py"
    ```

???+ tip "Tip: Autocomplete Metric Units"
    `MetricUnit` enum facilitate finding a supported metric unit by CloudWatch. Alternatively, you can pass the value as a string if you already know them e.g. "Count".

???+ note "Note: Metrics overflow"
    CloudWatch EMF supports a max of 100 metrics per batch. Metrics utility will flush all metrics when adding the 100th metric. Subsequent metrics, e.g. 101th, will be aggregated into a new EMF object, for your convenience.

???+ warning "Warning: Do not create metrics or dimensions outside the handler"
    Metrics or dimensions added in the global scope will only be added during cold start. Disregard if you that's the intended behaviour.

### Adding default dimensions

You can use either `set_default_dimensions` method or `default_permissions` parameter in `log_metrics` decorator to persist dimensions across Lambda invocations.

If you'd like to remove them at some point, you can use `clear_default_dimensions` method.

=== "set_default_dimensions method"

    ```python hl_lines="5"
    --8<-- "docs/examples/core/metrics/set_default_dimensions.py"
    ```
=== "with log_metrics decorator"

    ```python hl_lines="5 8"
    --8<-- "docs/examples/core/metrics/log_metrics_default_dimensions.py"
    ```

### Flushing metrics

As you finish adding all your metrics, you need to serialize and flush them to standard output. You can do that automatically with the `log_metrics` decorator.

This decorator also **validates**, **serializes**, and **flushes** all your metrics. During metrics validation, if no metrics are provided then a warning will be logged, but no exception will be raised.

=== "app.py"

    ```python hl_lines="7"
    --8<-- "docs/examples/core/metrics/flush_metrics.py"
    ```
=== "Example CloudWatch Logs excerpt"

    ```json hl_lines="2 7 10 15 22"
    {
        "BookingConfirmation": 1.0,
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
                "Name": "BookingConfirmation",
                "Unit": "Count"
                }
            ]
            }
        ]
        },
        "service": "ExampleService"
    }
    ```

???+ tip "Tip: Metric validation"
    If metrics are provided, and any of the following criteria are not met, **`SchemaValidationError`** exception will be raised:

    * Maximum of 8 user-defined dimensions
    * Namespace is set, and no more than one
    * Metric units must be [supported by CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)

#### Raising SchemaValidationError on empty metrics

If you want to ensure at least one metric is always emitted, you can pass `raise_on_empty_metrics` to the **log_metrics** decorator:

```python hl_lines="6" title="Raising SchemaValidationError exception if no metrics are added"
--8<-- "docs/examples/core/metrics/log_metrics_raise_on_empty_metrics.py"
```

???+ tip "Suppressing warning messages on empty metrics"
    If you expect your function to execute without publishing metrics every time, you can suppress the warning with **`warnings.filterwarnings("ignore", "No metrics to publish*")`**.

#### Nesting multiple middlewares

When using multiple middlewares, use `log_metrics` as your **last decorator** wrapping all subsequent ones to prevent early Metric validations when code hasn't been run yet.

```python hl_lines="8-9" title="Example with multiple decorators"
--8<-- "docs/examples/core/metrics/log_metrics_multiple_decorators.py"
```

### Capturing cold start metric

You can optionally capture cold start metrics with `log_metrics` decorator via `capture_cold_start_metric` param.

```python hl_lines="6" title="Generating function cold start metric"
--8<-- "docs/examples/core/metrics/log_metrics_capture_cold_start_metric.py"
```

If it's a cold start invocation, this feature will:

* Create a separate EMF blob solely containing a metric named `ColdStart`
* Add `function_name` and `service` dimensions

This has the advantage of keeping cold start metric separate from your application metrics, where you might have unrelated dimensions.

???+ info
    We do not emit 0 as a value for ColdStart metric for cost reasons. [Let us know](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=) if you'd prefer a flag to override it.

## Advanced

### Adding metadata

You can add high-cardinality data as part of your Metrics log with `add_metadata` method. This is useful when you want to search highly contextual information along with your metrics in your logs.

???+ info
    **This will not be available during metrics visualization** - Use **dimensions** for this purpose

=== "app.py"

    ```python hl_lines="10"
    --8<-- "docs/examples/core/metrics/add_metadata.py"
    ```

=== "Example CloudWatch Logs excerpt"

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

### Single metric with a different dimension

CloudWatch EMF uses the same dimensions across all your metrics. Use `single_metric` if you have a metric that should have different dimensions.

???+ info
    Generally, this would be an edge case since you [pay for unique metric](https://aws.amazon.com/cloudwatch/pricing). Keep the following formula in mind:

    **unique metric = (metric_name + dimension_name + dimension_value)**

```python hl_lines="6-7" title="Generating an EMF blob with a single metric"
--8<-- "docs/examples/core/metrics/single_metric.py"
```

### Flushing metrics manually

If you prefer not to use `log_metrics` because you might want to encapsulate additional logic when doing so, you can manually flush and clear metrics as follows:

???+ warning
	Metrics, dimensions and namespace validation still applies

```python hl_lines="11-13" title="Manually flushing and clearing metrics from memory"
--8<-- "docs/examples/core/metrics/flush_metrics_manually.py"
```

## Testing your code

### Environment variables

???+ tip
	Ignore this section, if you are explicitly setting namespace/default dimension via `namespace` and `service` parameters.

	For example, `Metrics(namespace=ApplicationName, service=ServiceName)`

Use `POWERTOOLS_METRICS_NAMESPACE` and `POWERTOOLS_SERVICE_NAME` env vars when unit testing your code to ensure metric namespace and dimension objects are created, and your code doesn't fail validation.

```bash title="Injecting dummy Metric Namespace before running tests"
POWERTOOLS_SERVICE_NAME="Example" POWERTOOLS_METRICS_NAMESPACE="Application" python -m pytest
```

### Clearing metrics

`Metrics` keep metrics in memory across multiple instances. If you need to test this behaviour, you can use the following Pytest fixture to ensure metrics are reset incl. cold start:

```python title="Clearing metrics between tests"
--8<-- "docs/examples/core/metrics/clear_metrics_between_tests.py"
```

### Functional testing

As metrics are logged to standard output, you can read standard output and assert whether metrics are present. Here's an example using `pytest` with `capsys` built-in fixture:

=== "Assert single EMF blob with pytest.py"

    ```python hl_lines="7 15-16 24-25"
    --8<-- "docs/examples/core/metrics/functional_testing.py"
    ```

=== "Assert multiple EMF blobs with pytest"

    ```python hl_lines="8-9 12 22-24 26 30-31 33"
    --8<-- "docs/examples/core/metrics/functional_testing_multiple_blobs.py"
    ```

???+ tip
    For more elaborate assertions and comparisons, check out [our functional testing for Metrics utility.](https://github.com/awslabs/aws-lambda-powertools-python/blob/develop/tests/functional/test_metrics.py)
