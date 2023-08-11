---
title: Datadog
description: Core utility
---
<!-- markdownlint-disable MD013 -->
Datadog provider creates custom metrics by flushing metrics to standard output and exporting metrics using [Datadog Forwarder](https://docs.datadoghq.com/logs/guide/forwarder/?tab=cloudformation){target="_blank" rel="nofollow"} or flushing metrics to [Datadog extension](https://docs.datadoghq.com/serverless/installation/python/?tab=datadogcli){target="_blank" rel="nofollow"} using Datadog SDK.
<!-- markdownlint-enable MD013 -->

These metrics can be visualized through [Datadog console](https://app.datadoghq.com/metric/explore){target="_blank" rel="nofollow"}.

## Key features

* Flush metrics to standard output
* Flush metrics to Datadog extension
* Validate against common metric definitions mistakes (values)
* Support to add default tags to all created metrics

## Terminologies

If you're new to Datadog custom metrics, we suggest you read the Datadog [official documentation](https://docs.datadoghq.com/metrics/custom_metrics/){target="_blank" rel="nofollow"} for custom metrics.

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples){target="_blank" }.

Datadog provider has two global settings that will be used across all metrics emitted:

| Setting              | Description                                                                     | Environment variable           | Constructor parameter |
| -------------------- | ------------------------------------------------------------------------------- | ------------------------------ | --------------------- |
| **Metric namespace** | Logical container where all metrics will be placed e.g. `ServerlessAirline`     | `POWERTOOLS_METRICS_NAMESPACE` | `namespace`           |
| **Flush to log**     | Use this when you want to flush metrics to be exported through Datadog Forwarder| `DD_FLUSH_TO_LOG`              | `flush_to_log`        |

Experiment to use your application or main service as the metric namespace to easily group all metrics.

### Install

???+ note
    If you are using Datadog Forwarder, you can skip this step.

To adhere to Lambda best practices and effectively minimize the size of your development package, we recommend using the official Datadog layers built specifically for the SDK and extension components. Below is the template that demonstrates how to configure a SAM template with this information.

```yaml hl_lines="13 14 22 24" title="AWS Serverless Application Model (SAM) example"
--8<-- "examples/metrics_datadog/sam/template.yaml"
```

If you prefer not to utilize the Datadog SDK provided through the Datadog layer, add `aws-lambda-powertools[datadog]` as a dependency in your preferred tool: _e.g._, _requirements.txt_, _pyproject.toml_. This will ensure you have the required dependencies before using Datadog provider.

### Creating metrics

You can create metrics using `add_metric`. Optional parameter such as timestamp can be included, but if not provided, the Datadog Provider will automatically use the current timestamp by default.

???+ tip
	You can initialize DadatadogMetrics in any other module too. It'll keep track of your aggregate metrics in memory to optimize costs (one blob instead of multiples).

=== "add_metrics_with_provider.py"

    ```python hl_lines="6 12"
    --8<-- "examples/metrics_datadog/src/add_metrics_with_provider.py"
    ```

=== "add_metrics_without_provider.py"

    ```python hl_lines="11"
    --8<-- "examples/metrics_datadog/src/add_metrics_without_provider.py"
    ```

???+ warning "Warning: Do not create metrics outside the handler"
    Metrics added in the global scope will only be added during cold start. Disregard if you that's the intended behavior.

### Adding tags

Datadog offers the flexibility to configure tags per metric. To provider a better experience for our customers, you can pass an arbitrary number of keyword arguments (kwargs) that can be user as a tag.

=== "add_metrics_with_tags.py"

    ```python hl_lines="9"
    --8<-- "examples/metrics_datadog/src/add_metrics_with_tags.py"
    ```

### Adding default tags

If you want to set the same tags for all metrics, you can use the `set_default_tags` method or the `default_tags` parameter in the `log_metrics` decorator and then persist tags across the Lambda invocations.

If you'd like to remove them at some point, you can use `clear_default_tags` method.

???+ note
    When default tags are configured and an additional specific tag is assigned to a metric, the metric will exclusively contain that specific tag.

=== "set_default_tags.py"

    ```python hl_lines="5"
    --8<-- "examples/metrics_datadog/src/set_default_tags.py"
    ```

=== "set_default_tags_log_metrics.py"

    ```python hl_lines="6 9"
    --8<-- "examples/metrics_datadog/src/set_default_tags_log_metrics.py"
    ```

### Flushing metrics to standard output

You have the option to flush metrics to the standard output for exporting, which can then be seamlessly processed through the [Datadog Forwarder](https://docs.datadoghq.com/logs/guide/forwarder/?tab=cloudformation){target="_blank" rel="nofollow"}.

=== "flush_metrics_to_standard_output.py"

    ```python hl_lines="4"
    --8<-- "examples/metrics_datadog/src/flush_metrics_to_standard_output.py"
    ```

### Flushing metrics

As you finish adding all your metrics, you need to serialize and flush them to standard output. You can do that automatically with the `log_metrics` decorator.

This decorator also **validates**, **serializes**, and **flushes** all your metrics. During metrics validation, if no metrics are provided then a warning will be logged, but no exception will be raised.

=== "add_metrics.py"

    ```python hl_lines="7"
    --8<-- "examples/metrics_datadog/src/add_metrics_with_tags.py"
    ```

=== "log_metrics_output.json"

    ```json hl_lines="2 6 7"
    --8<-- "examples/metrics_datadog/src/log_metrics_output.json"
    ```

#### Raising SchemaValidationError on empty metrics

If you want to ensure at least one metric is always emitted, you can pass `raise_on_empty_metrics` to the **log_metrics** decorator:

```python hl_lines="7" title="Raising SchemaValidationError exception if no metrics are added"
--8<-- "examples/metrics_datadog/src/raise_on_empty_datadog_metrics.py"
```

???+ tip "Suppressing warning messages on empty metrics"
    If you expect your function to execute without publishing metrics every time, you can suppress the warning with **`warnings.filterwarnings("ignore", "No metrics to publish*")`**.

### Capturing cold start metric

You can optionally capture cold start metrics with `log_metrics` decorator via `capture_cold_start_metric` param.

=== "capture_cold_start_metric.py"

    ```python hl_lines="7"
    --8<-- "examples/metrics_datadog/src/capture_cold_start_datadog_metric.py"
    ```

=== "capture_cold_start_metric_output.json"

    ```json hl_lines="2 6"
    --8<-- "examples/metrics_datadog/src/capture_cold_start_metric_output.json"
    ```

If it's a cold start invocation, this feature will:

* Create a separate Datadog metric solely containing a metric named `ColdStart`
* Add `function_name` as a tag

This has the advantage of keeping cold start metric separate from your application metrics, where you might have unrelated dimensions.

???+ info
    We do not emit 0 as a value for ColdStart metric for cost reasons. [Let us know](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=feature-request%2C+triage&template=feature_request.md&title=){target="_blank"} if you'd prefer a flag to override it.

### Environment variables

The following environment variable is available to configure Metrics at a global scope:

| Setting            | Description                                                                  | Environment variable                    | Default |
|--------------------|------------------------------------------------------------------------------|-----------------------------------------|---------|
| **Namespace Name** | Sets namespace used for metrics.                                             | `POWERTOOLS_METRICS_NAMESPACE`          | `None`  |

`POWERTOOLS_METRICS_NAMESPACE` is also available on a per-instance basis with the `namespace` parameter, which will consequently override the environment variable value.

## Advanced

### Flushing metrics manually

If you are using the [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter){target="_blank"} project, or a middleware with custom metric logic, you can use `flush_metrics()`. This method will serialize, print metrics available to standard output, and clear in-memory metrics data.

???+ warning
    This does not capture Cold Start metrics, and metric data validation still applies.

Contrary to the `log_metrics` decorator, you are now also responsible to flush metrics in the event of an exception.

```python hl_lines="17" title="Manually flushing and clearing metrics from memory"
--8<-- "examples/metrics_datadog/src/flush_datadog_metrics.py"
```

## Testing your code

### Setting environment variables

???+ tip
	Ignore this section, if:

    * You are explicitly setting namespace via `namespace` parameter
    * You're not instantiating `DatadogMetrics` in the global namespace

	For example, `DatadogMetrics(namespace="ServerlessAirline")`

Make sure to set `POWERTOOLS_METRICS_NAMESPACE` before running your tests to prevent failing on `SchemaValidation` exception. You can set it before you run tests or via pytest plugins like [dotenv](https://pypi.org/project/pytest-dotenv/){target="_blank" rel="nofollow"}.

```bash title="Injecting dummy Metric Namespace before running tests"
--8<-- "examples/metrics_datadog/src/run_tests_env_var.sh"
```

### Clearing metrics

`DatadogMetrics` keep metrics in memory across multiple instances. If you need to test this behavior, you can use the following Pytest fixture to ensure metrics are reset incl. cold start:

```python title="Clearing metrics between tests"
--8<-- "examples/metrics_datadog/src/clear_datadog_metrics_in_tests.py"
```

### Functional testing

You can read standard output and assert whether metrics have been flushed. Here's an example using `pytest` with `capsys` built-in fixture:

=== "assert_single_datadog_metric.py"

    ```python hl_lines="7"
    --8<-- "examples/metrics_datadog/src/assert_single_datadog_metric.py"
    ```

=== "add_metrics.py"

    ```python
    --8<-- "examples/metrics_datadog/src/add_metrics_without_provider.py"
    ```

???+ tip
    For more elaborate assertions and comparisons, check out [our functional testing for DatadogMetrics utility.](https://github.com/aws-powertools/powertools-lambda-python/blob/develop/tests/functional/metrics/test_metrics_datadog.py){target="_blank"}
