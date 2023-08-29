import json
import warnings
from collections import namedtuple

import pytest
from test_metrics_provider import capture_metrics_output

from aws_lambda_powertools.metrics.exceptions import MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics.provider.cold_start import reset_cold_start_flag
from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics, DatadogProvider


def test_datadog_coldstart(capsys):
    reset_cold_start_flag()

    # GIVEN DatadogMetrics is initialized
    dd_provider = DatadogProvider(flush_to_log=True)
    metrics = DatadogMetrics(provider=dd_provider)

    LambdaContext = namedtuple("LambdaContext", "function_name")

    # WHEN log_metrics is used with capture_cold_start_metric
    @metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(event, context):
        metrics.add_metric(name="item_sold", value=1, product="latte", order="online")

    lambda_handler({}, LambdaContext("example_fn2"))
    logs = capsys.readouterr().out.strip()

    # THEN ColdStart metric and function_name and service dimension should be logged
    assert "ColdStart" in logs
    assert "example_fn2" in logs


def test_datadog_write_to_log_with_env_variable(capsys, monkeypatch):
    # GIVEN DD_FLUSH_TO_LOG env is configured
    monkeypatch.setenv("DD_FLUSH_TO_LOG", "True")
    metrics = DatadogMetrics()

    # WHEN we add a metric
    metrics.add_metric(name="item_sold", value=1, product="latte", order="online")
    metrics.flush_metrics()
    logs = capture_metrics_output(capsys)

    # THEN metrics is flushed to log
    logs["e"] = ""
    assert logs == json.loads('{"m":"item_sold","v":1,"e":"","t":["product:latte","order:online"]}')


def test_datadog_with_invalid_metric_value():
    # GIVEN DatadogMetrics is initialized
    metrics = DatadogMetrics()

    # WHEN we pass an incorrect metric value (non-numeric)
    # WHEN we attempt to serialize a valid Datadog metric
    # THEN it should fail validation and raise MetricValueError
    with pytest.raises(MetricValueError, match=".*is not a valid number"):
        metrics.add_metric(name="item_sold", value="a", product="latte", order="online")


def test_datadog_with_invalid_metric_name():
    # GIVEN DatadogMetrics is initialized
    metrics = DatadogMetrics()

    # WHEN we a metric name starting with a number
    # WHEN we attempt to serialize a valid Datadog metric
    # THEN it should fail validation and raise MetricValueError
    with pytest.raises(SchemaValidationError, match="Invalid metric name.*"):
        metrics.add_metric(name="1_item_sold", value="a", product="latte", order="online")


def test_datadog_raise_on_empty():
    # GIVEN DatadogMetrics is initialized
    metrics = DatadogMetrics()

    LambdaContext = namedtuple("LambdaContext", "function_name")

    # WHEN we set raise_on_empty_metrics to True
    @metrics.log_metrics(raise_on_empty_metrics=True)
    def lambda_handler(event, context):
        pass

    # THEN it should fail with no metric serialized
    with pytest.raises(SchemaValidationError, match="Must contain at least one metric."):
        lambda_handler({}, LambdaContext("example_fn"))


def test_datadog_tags_using_kwargs(capsys):
    # GIVEN DatadogMetrics is initialized
    metrics = DatadogMetrics(flush_to_log=True)

    # WHEN we add tags using kwargs
    metrics.add_metric("order_valve", 12.45, sales="sam")
    metrics.flush_metrics()
    logs = capsys.readouterr().out.strip()
    log_dict = json.loads(logs)
    tag_list = log_dict.get("t")

    # THEN tags must be present
    assert "sales:sam" in tag_list


def test_metrics_clear_metrics_after_invocation(metric_datadog):
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics(flush_to_log=True)
    my_metrics.add_metric(**metric_datadog)

    # WHEN log_metrics is used to flush metrics from memory
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        pass

    lambda_handler({}, {})

    # THEN metric set should be empty after function has been run
    assert my_metrics.metric_set == []


def test_metrics_decorator_with_metrics_warning():
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics(flush_to_log=True)

    # WHEN using the log_metrics decorator and no metrics have been added
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        pass

    # THEN it should raise a warning instead of throwing an exception
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        lambda_handler({}, {})
        assert len(w) == 1
        assert str(w[-1].message) == (
            "No application metrics to publish. The cold-start metric may be published if enabled. "
            "If application metrics should never be empty, consider using 'raise_on_empty_metrics'"
        )


def test_metrics_with_default_namespace(capsys, namespace):
    # GIVEN DatadogMetrics is initialized with default namespace
    metrics = DatadogMetrics(flush_to_log=True)

    LambdaContext = namedtuple("LambdaContext", "function_name")

    # WHEN we add metrics
    @metrics.log_metrics
    def lambda_handler(event, context):
        metrics.add_metric(name="item_sold", value=1, product="latte", order="online")

    lambda_handler({}, LambdaContext("example_fn2"))
    logs = capsys.readouterr().out.strip()

    # THEN default namespace must be assumed
    assert namespace not in logs


def test_datadog_with_non_default_namespace(capsys, namespace):
    # GIVEN DatadogMetrics is initialized with a non-default namespace
    metrics = DatadogMetrics(namespace=namespace, flush_to_log=True)

    LambdaContext = namedtuple("LambdaContext", "function_name")

    # WHEN log_metrics is used
    @metrics.log_metrics
    def lambda_handler(event, context):
        metrics.add_metric(name="item_sold", value=1, product="latte", order="online")

    lambda_handler({}, LambdaContext("example_fn"))
    logs = capsys.readouterr().out.strip()

    # THEN namespace must be present in logs
    assert namespace in logs


def test_serialize_metrics(metric_datadog):
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics(flush_to_log=True)
    my_metrics.add_metric(**metric_datadog)

    # WHEN we serialize metrics
    my_metrics.serialize_metric_set()

    # THEN metric set should be empty after function has been run
    assert my_metrics.metric_set[0]["m"] == "single_metric"


def test_clear_metrics(metric):
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics(flush_to_log=True)
    my_metrics.add_metric(**metric)
    my_metrics.clear_metrics()

    # THEN metric set should be empty after function has been run
    assert my_metrics.metric_set == []


def test_persist_default_tags(capsys):
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics(flush_to_log=True)
    my_metrics.set_default_tags(environment="test", log_group="/lambda/test")

    # WHEN we utilize log_metrics to serialize
    # and flush metrics and clear all metrics and tags from memory
    # at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        my_metrics.add_metric(name="item_sold", value=1)

    lambda_handler({}, {})
    first_invocation = capsys.readouterr().out.strip()

    lambda_handler({}, {})
    second_invocation = capsys.readouterr().out.strip()

    # THEN we should have default tags in both outputs
    assert "environment" in first_invocation
    assert "environment" in second_invocation


def test_log_metrics_with_default_tags(capsys):
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics(flush_to_log=True)
    default_tags = {"environment": "test", "log_group": "/lambda/test"}

    # WHEN we utilize log_metrics with default dimensions to serialize
    # and flush metrics and clear all metrics and tags from memory
    # at the end of a function execution
    @my_metrics.log_metrics(default_tags=default_tags)
    def lambda_handler(evt, ctx):
        my_metrics.add_metric(name="item_sold", value=1)

    lambda_handler({}, {})
    first_invocation = capsys.readouterr().out.strip()

    lambda_handler({}, {})
    second_invocation = capsys.readouterr().out.strip()

    # THEN we should have default tags in both outputs
    assert "environment" in first_invocation
    assert "environment" in second_invocation


def test_log_metrics_precedence_metrics_tags_over_default_tags(capsys):
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics(flush_to_log=True)
    default_tags = {"environment": "test", "log_group": "/lambda/test"}

    # WHEN we use log_metrics with default_tags to serialize
    # and create metrics with a tag that has the same name as one of the default_tags
    @my_metrics.log_metrics(default_tags=default_tags)
    def lambda_handler(evt, ctx):
        my_metrics.add_metric(name="item_sold", value=1, environment="metric_precedence")

    lambda_handler({}, {})
    output = json.loads(capsys.readouterr().out.strip())

    # THEN tag defined in add_metric must have preference over default_tags
    assert "environment:metric_precedence" in output["t"]
    assert "environment:test" not in output["t"]


def test_log_metrics_merge_metrics_tags_and_default_tags(capsys):
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics(flush_to_log=True)
    default_tags = {"environment": "test", "log_group": "/lambda/test"}

    # WHEN we use log_metrics with default_tags to serialize
    # and create metrics with a tag that has the same name as one of the default_tags
    @my_metrics.log_metrics(default_tags=default_tags)
    def lambda_handler(evt, ctx):
        my_metrics.add_metric(name="item_sold", value=1, product="powertools")

    lambda_handler({}, {})
    output = json.loads(capsys.readouterr().out.strip())

    # THEN there should be serialized default_tags and metric tags
    output["e"] = ""
    assert output == json.loads(
        '{"m":"item_sold","v":1,"e":"","t":["environment:test","log_group:/lambda/test", "product:powertools"]}',
    )


def test_clear_default_tags():
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics()
    my_metrics.set_default_tags(environment="test", log_group="/lambda/test")

    # WHEN they are removed via clear_default_tags method
    my_metrics.clear_default_tags()

    # THEN there should be no default tags
    assert not my_metrics.default_tags


def test_namespace_var_precedence(monkeypatch, namespace):
    # GIVEN we use POWERTOOLS_METRICS_NAMESPACE
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", "a_namespace")
    my_metrics = DatadogMetrics(namespace=namespace, flush_to_log=True)

    # WHEN creating a metric and explicitly set a namespace
    my_metrics.add_metric(name="item_sold", value=1)

    output = my_metrics.serialize_metric_set()

    # THEN namespace should match the explicitly passed variable and not the env var
    assert output[0]["m"] == f"{namespace}.item_sold"


def test_namespace_env_var(monkeypatch):
    # GIVEN POWERTOOLS_METRICS_NAMESPACE is set
    env_namespace = "a_namespace"
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", env_namespace)
    my_metrics = DatadogMetrics(flush_to_log=True)

    # WHEN creating a metric and explicitly set a namespace
    my_metrics.add_metric(name="item_sold", value=1)

    output = my_metrics.serialize_metric_set()

    # THEN namespace should match the explicitly passed variable and not the env var
    assert output[0]["m"] == f"{env_namespace}.item_sold"
