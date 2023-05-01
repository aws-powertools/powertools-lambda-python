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
* **Metric**. It's the name of the metric, for example: `SuccessfulBooking` or `UpdatedBooking`.
* **Unit**. It's a value representing the unit of measure for the corresponding metric, for example: `Count` or `Seconds`.
* **Resolution**. It's a value representing the storage resolution for the corresponding metric. Metrics can be either Standard or High resolution. Read more [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html#high-resolution-metrics).

<figure>
  <img src="../../media/metrics_terminology.png" />
  <figcaption>Metric terminology, visually explained</figcaption>
</figure>

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/awslabs/aws-lambda-powertools-python/tree/develop/examples){target="_blank"}.

Metric has two global settings that will be used across all metrics emitted:

| Setting              | Description                                                                     | Environment variable           | Constructor parameter |
| -------------------- | ------------------------------------------------------------------------------- | ------------------------------ | --------------------- |
| **Metric namespace** | Logical container where all metrics will be placed e.g. `ServerlessAirline`     | `POWERTOOLS_METRICS_NAMESPACE` | `namespace`           |
| **Service**          | Optionally, sets **service** metric dimension across all metrics e.g. `payment` | `POWERTOOLS_SERVICE_NAME`      | `service`             |

???+ tip
    Use your application or main service as the metric namespace to easily group all metrics.

```yaml hl_lines="13" title="AWS Serverless Application Model (SAM) example"
--8<-- "examples/metrics/sam/template.yaml"
```

???+ note
    For brevity, all code snippets in this page will rely on environment variables above being set.

    This ensures we instantiate `metrics = Metrics()` over `metrics = Metrics(service="booking", namespace="ServerlessAirline")`, etc.

### Creating metrics

You can create metrics using `add_metric`, and you can create dimensions for all your aggregate metrics using `add_dimension` method.

???+ tip
	You can initialize Metrics in any other module too. It'll keep track of your aggregate metrics in memory to optimize costs (one blob instead of multiples).

=== "add_metrics.py"

    ```python hl_lines="10"
    --8<-- "examples/metrics/src/add_metrics.py"
    ```

=== "add_dimension.py"

    ```python hl_lines="13"
    --8<-- "examples/metrics/src/add_dimension.py"
    ```

???+ tip "Tip: Autocomplete Metric Units"
    `MetricUnit` enum facilitate finding a supported metric unit by CloudWatch. Alternatively, you can pass the value as a string if you already know them _e.g. `unit="Count"`_.

???+ note "Note: Metrics overflow"
    CloudWatch EMF supports a max of 100 metrics per batch. Metrics utility will flush all metrics when adding the 100th metric. Subsequent metrics (101th+) will be aggregated into a new EMF object, for your convenience.

???+ warning "Warning: Do not create metrics or dimensions outside the handler"
    Metrics or dimensions added in the global scope will only be added during cold start. Disregard if you that's the intended behavior.

### Adding high-resolution metrics

You can create [high-resolution metrics](https://aws.amazon.com/about-aws/whats-new/2023/02/amazon-cloudwatch-high-resolution-metric-extraction-structured-logs/) passing `resolution` parameter to `add_metric`.

???+ tip "When is it useful?"
    High-resolution metrics are data with a granularity of one second and are very useful in several situations such as telemetry, time series, real-time incident management, and others.

=== "add_high_resolution_metrics.py"

    ```python hl_lines="10"
    --8<-- "examples/metrics/src/add_high_resolution_metric.py"
    ```

???+ tip "Tip: Autocomplete Metric Resolutions"
    `MetricResolution` enum facilitates finding a supported metric resolution by CloudWatch. Alternatively, you can pass the values 1 or 60 (must be one of them) as an integer _e.g. `resolution=1`_.

### Adding multi-value metrics

You can call `add_metric()` with the same metric name multiple times. The values will be grouped together in a list.

=== "add_multi_value_metrics.py"

    ```python hl_lines="14-15"
    --8<-- "examples/metrics/src/add_multi_value_metrics.py"
    ```

=== "add_multi_value_metrics_output.json"

    ```python hl_lines="15 24-26"
    --8<-- "examples/metrics/src/add_multi_value_metrics_output.json"
    ```

### Adding default dimensions

You can use `set_default_dimensions` method, or `default_dimensions` parameter in `log_metrics` decorator, to persist dimensions across Lambda invocations.

If you'd like to remove them at some point, you can use `clear_default_dimensions` method.

=== "set_default_dimensions.py"

    ```python hl_lines="9"
    --8<-- "examples/metrics/src/set_default_dimensions.py"
    ```

=== "set_default_dimensions_log_metrics.py"

    ```python hl_lines="9 13"
    --8<-- "examples/metrics/src/set_default_dimensions_log_metrics.py"
    ```

### Flushing metrics

As you finish adding all your metrics, you need to serialize and flush them to standard output. You can do that automatically with the `log_metrics` decorator.

This decorator also **validates**, **serializes**, and **flushes** all your metrics. During metrics validation, if no metrics are provided then a warning will be logged, but no exception will be raised.

=== "add_metrics.py"

    ```python hl_lines="8"
    --8<-- "examples/metrics/src/add_metrics.py"
    ```

=== "log_metrics_output.json"

    ```json hl_lines="6 9 14 21-23"
    --8<-- "examples/metrics/src/log_metrics_output.json"
    ```

???+ tip "Tip: Metric validation"
    If metrics are provided, and any of the following criteria are not met, **`SchemaValidationError`** exception will be raised:

    * Maximum of 29 user-defined dimensions
    * Namespace is set, and no more than one
    * Metric units must be [supported by CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)

#### Raising SchemaValidationError on empty metrics

If you want to ensure at least one metric is always emitted, you can pass `raise_on_empty_metrics` to the **log_metrics** decorator:

```python hl_lines="7" title="Raising SchemaValidationError exception if no metrics are added"
--8<-- "examples/metrics/src/raise_on_empty_metrics.py"
```

???+ tip "Suppressing warning messages on empty metrics"
    If you expect your function to execute without publishing metrics every time, you can suppress the warning with **`warnings.filterwarnings("ignore", "No metrics to publish*")`**.

### Capturing cold start metric

You can optionally capture cold start metrics with `log_metrics` decorator via `capture_cold_start_metric` param.

=== "capture_cold_start_metric.py"

    ```python hl_lines="7"
    --8<-- "examples/metrics/src/capture_cold_start_metric.py"
    ```

=== "capture_cold_start_metric_output.json"

    ```json hl_lines="9 15 22 24-25"
    --8<-- "examples/metrics/src/capture_cold_start_metric_output.json"
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

=== "add_metadata.py"

    ```python hl_lines="14"
    --8<-- "examples/metrics/src/add_metadata.py"
    ```

=== "add_metadata_output.json"

    ```json hl_lines="22"
    --8<-- "examples/metrics/src/add_metadata_output.json"
    ```

### Single metric with a different dimension

CloudWatch EMF uses the same dimensions across all your metrics. Use `single_metric` if you have a metric that should have different dimensions.

???+ info
    Generally, this would be an edge case since you [pay for unique metric](https://aws.amazon.com/cloudwatch/pricing). Keep the following formula in mind:

    **unique metric = (metric_name + dimension_name + dimension_value)**

=== "single_metric.py"

    ```python hl_lines="11"
    --8<-- "examples/metrics/src/single_metric.py"
    ```

=== "single_metric_output.json"

    ```json hl_lines="15"
    --8<-- "examples/metrics/src/single_metric_output.json"
    ```

By default it will skip all previously defined dimensions including default dimensions. Use `default_dimensions` keyword argument if you want to reuse default dimensions or specify custom dimensions from a dictionary.

=== "single_metric_default_dimensions_inherit.py"

    ```python hl_lines="10 15"
    --8<-- "examples/metrics/src/single_metric_default_dimensions_inherit.py"
    ```

=== "single_metric_default_dimensions.py"

    ```python hl_lines="12"
    --8<-- "examples/metrics/src/single_metric_default_dimensions.py"
    ```

### Flushing metrics manually

If you are using the AWS Lambda Web Adapter project, or a middleware with custom metric logic, you can use `flush_metrics()`. This method will serialize, print metrics available to standard output, and clear in-memory metrics data.

???+ warning
    This does not capture Cold Start metrics, and metric data validation still applies.

Contrary to the `log_metrics` decorator, you are now also responsible to flush metrics in the event of an exception.

```python hl_lines="18" title="Manually flushing and clearing metrics from memory"
--8<-- "examples/metrics/src/flush_metrics.py"
```

### Metrics isolation

You can use `EphemeralMetrics` class when looking to isolate multiple instances of metrics with distinct namespaces and/or dimensions.

!!! note "This is a typical use case is for multi-tenant, or emitting same metrics for distinct applications."

```python hl_lines="1 4" title="EphemeralMetrics usage"
--8<-- "examples/metrics/src/ephemeral_metrics.py"
```

**Differences between `EphemeralMetrics` and `Metrics`**

`EphemeralMetrics` has only two differences while keeping nearly the exact same set of features:

| Feature                                                                                                     | Metrics | EphemeralMetrics |
| ----------------------------------------------------------------------------------------------------------- | ------- | ---------------- |
| **Share data across instances** (metrics, dimensions, metadata, etc.)                                       | Yes     | -                |
| **[Default dimensions](#adding-default-dimensions) that persists across Lambda invocations** (metric flush) | Yes     | -                |

!!! question "Why not changing the default `Metrics` behaviour to not share data across instances?"

This is an intentional design to prevent accidental data deduplication or data loss issues due to [CloudWatch EMF](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html){target="_blank"} metric dimension constraint.

In CloudWatch, there are two metric ingestion mechanisms: [EMF (async)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html){target="_blank"} and [`PutMetricData` API (sync)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data){target="_blank"}.

The former creates metrics asynchronously via CloudWatch Logs, and the latter uses a synchronous and more flexible ingestion API.

!!! important "Key concept"
    CloudWatch [considers a metric unique](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Metric){target="_blank"} by a combination of metric **name**, metric **namespace**, and zero or more metric **dimensions**.

With EMF, metric dimensions are shared with any metrics you define. With `PutMetricData` API, you can set a [list](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html) defining one or more metrics with distinct dimensions.

This is a subtle yet important distinction. Imagine you had the following metrics to emit:

| Metric Name            | Dimension                                 | Intent             |
| ---------------------- | ----------------------------------------- | ------------------ |
| **SuccessfulBooking**  | service="booking", **tenant_id**="sample" | Application metric |
| **IntegrationLatency** | service="booking", function_name="sample" | Operational metric |
| **ColdStart**          | service="booking", function_name="sample" | Operational metric |

The `tenant_id` dimension could vary leading to two common issues:

1. `ColdStart` metric will be created multiple times (N * number of unique tenant_id dimension value), despite the `function_name` being the same
2. `IntegrationLatency` metric will be also created multiple times due to `tenant_id` as well as `function_name` (may or not be intentional)

These issues are exacerbated when you create **(A)** metric dimensions conditionally, **(B)** multiple metrics' instances throughout your code  instead of reusing them (globals). Subsequent metrics' instances will have (or lack) different metric dimensions resulting in different metrics and data points with the same name.

!!! note "Intentional design to address these scenarios"

**On 1**, when you enable [capture_start_metric feature](#capturing-cold-start-metric), we transparently create and flush an additional EMF JSON Blob that is independent from your application metrics. This prevents data pollution.

**On 2**, you can use `EphemeralMetrics` to create an additional EMF JSON Blob from your application metric (`SuccessfulBooking`). This ensures that `IntegrationLatency` operational metric data points aren't tied to any dynamic dimension values like `tenant_id`.

That is why `Metrics` shares data across instances by default, as that covers 80% of use cases and different personas using Powertools. This allows them to instantiate `Metrics` in multiple places throughout their code - be a separate file, a middleware, or an abstraction that sets default dimensions.

## Testing your code

### Environment variables

???+ tip
	Ignore this section, if:

    * You are explicitly setting namespace/default dimension via `namespace` and `service` parameters
    * You're not instantiating `Metrics` in the global namespace

	For example, `Metrics(namespace="ServerlessAirline", service="booking")`

Make sure to set `POWERTOOLS_METRICS_NAMESPACE` and `POWERTOOLS_SERVICE_NAME` before running your tests to prevent failing on `SchemaValidation` exception. You can set it before you run tests or via pytest plugins like [dotenv](https://pypi.org/project/pytest-dotenv/).

```bash title="Injecting dummy Metric Namespace before running tests"
--8<-- "examples/metrics/src/run_tests_env_var.sh"
```

### Clearing metrics

`Metrics` keep metrics in memory across multiple instances. If you need to test this behavior, you can use the following Pytest fixture to ensure metrics are reset incl. cold start:

```python title="Clearing metrics between tests"
--8<-- "examples/metrics/src/clear_metrics_in_tests.py"
```

### Functional testing

You can read standard output and assert whether metrics have been flushed. Here's an example using `pytest` with `capsys` built-in fixture:

=== "assert_single_emf_blob.py"

    ```python hl_lines="6 9-10 23-34"
    --8<-- "examples/metrics/src/assert_single_emf_blob.py"
    ```

=== "add_metrics.py"

    ```python
    --8<-- "examples/metrics/src/add_metrics.py"
    ```

=== "assert_multiple_emf_blobs.py"

    This will be needed when using `capture_cold_start_metric=True`, or when both `Metrics` and `single_metric` are used.

    ```python hl_lines="20-21 27"
    --8<-- "examples/metrics/src/assert_multiple_emf_blobs.py"
    ```

=== "assert_multiple_emf_blobs_module.py"

    ```python
    --8<-- "examples/metrics/src/assert_multiple_emf_blobs_module.py"
    ```

???+ tip
    For more elaborate assertions and comparisons, check out [our functional testing for Metrics utility.](https://github.com/awslabs/aws-lambda-powertools-python/blob/develop/tests/functional/test_metrics.py)
