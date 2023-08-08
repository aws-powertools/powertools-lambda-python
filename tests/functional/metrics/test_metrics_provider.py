import json
from collections import namedtuple
from typing import Any, List

import pytest

from aws_lambda_powertools.metrics import (
    EphemeralMetrics,
    Metrics,
    SchemaValidationError,
)
from aws_lambda_powertools.metrics.provider import BaseProvider
from aws_lambda_powertools.metrics.provider.base import reset_cold_start_flag_provider


def capture_metrics_output(capsys):
    return json.loads(capsys.readouterr().out.strip())


@pytest.fixture
def metrics_provider() -> BaseProvider:
    class MetricsProvider:
        def __init__(self):
            self.metric_store: List = []
            self.result: str
            super().__init__()

        def add_metric(self, name: str, value: float, tag: List = None, *args, **kwargs):
            self.metric_store.append({"name": name, "value": value, "tag": tag})

        def serialize_metric_set(self, raise_on_empty_metrics: bool = False, *args, **kwargs):
            if raise_on_empty_metrics and len(self.metric_store) == 0:
                raise SchemaValidationError("Must contain at least one metric.")

            self.result = json.dumps(self.metric_store)

        def flush(self, *args, **kwargs):
            print(self.result)

        def clear(self):
            self.result = ""
            self.metric_store = []

    return MetricsProvider


@pytest.fixture
def metrics_class() -> BaseProvider:
    class MetricsClass(BaseProvider):
        def __init__(self, provider):
            self.provider = provider
            super().__init__()

        def add_metric(self, name: str, value: float, tag: List = None, *args, **kwargs):
            self.provider.add_metric(name=name, value=value, tag=tag)

        def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
            self.provider.serialize_metric_set(raise_on_empty_metrics=raise_on_empty_metrics)
            self.provider.flush()
            self.provider.clear()

        def add_cold_start_metric(self, context: Any) -> None:
            self.provider.add_metric(name="ColdStart", value=1, function_name=context.function_name)

        def serialize_metric_set(self, raise_on_empty_metrics: bool = False, *args, **kwargs):
            if raise_on_empty_metrics and len(self.metric_store) == 0:
                raise SchemaValidationError("Must contain at least one metric.")

            self.result = self.provider.flush()

        def clear_metrics(self) -> None:
            self.provider.clear_metrics()

    return MetricsClass


def test_metrics_provider_basic(capsys, metrics_provider, metric):
    provider = metrics_provider()
    provider.add_metric(**metric)
    provider.serialize_metric_set()
    provider.flush()
    output = capture_metrics_output(capsys)
    assert output[0]["name"] == metric["name"]
    assert output[0]["value"] == metric["value"]


def test_metrics_provider_class_basic(capsys, metrics_provider, metrics_class, metric):
    metrics = metrics_class(provider=metrics_provider())
    metrics.add_metric(**metric)
    metrics.flush_metrics()
    output = capture_metrics_output(capsys)
    assert output[0]["name"] == metric["name"]
    assert output[0]["value"] == metric["value"]


def test_metrics_provider_class_decorate(metrics_class, metrics_provider):
    # GIVEN Metrics is initialized
    my_metrics = metrics_class(provider=metrics_provider())

    # WHEN log_metrics is used to serialize metrics
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        return True

    # THEN log_metrics should invoke the function it decorates
    # and return no error if we have a namespace and dimension
    assert lambda_handler({}, {}) is True


def test_metrics_provider_class_coldstart(capsys, metrics_provider, metrics_class):
    my_metrics = metrics_class(provider=metrics_provider())

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))

    output = capture_metrics_output(capsys)

    # THEN ColdStart metric and function_name and service dimension should be logged
    assert output[0]["name"] == "ColdStart"


def test_metrics_provider_class_no_coldstart(capsys, metrics_provider, metrics_class):
    reset_cold_start_flag_provider()
    my_metrics = metrics_class(provider=metrics_provider())

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))
    _ = capture_metrics_output(capsys)
    # drop first one

    lambda_handler({}, LambdaContext("example_fn"))
    output = capture_metrics_output(capsys)

    # no coldstart is here
    assert "ColdStart" not in json.dumps(output)


def test_metric_provider_raise_on_empty_metrics(metrics_provider, metrics_class):
    # GIVEN Metrics is initialized
    my_metrics = metrics_class(provider=metrics_provider())

    # WHEN log_metrics is used with raise_on_empty_metrics param and has no metrics
    @my_metrics.log_metrics(raise_on_empty_metrics=True)
    def lambda_handler(evt, context):
        pass

    # THEN the raised exception should be SchemaValidationError
    # and specifically about the lack of Metrics
    with pytest.raises(SchemaValidationError, match="Must contain at least one metric."):
        lambda_handler({}, {})


def test_log_metrics_capture_cold_start_metric_once_with_provider_and_ephemeral(capsys, namespace, service):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)
    my_isolated_metrics = EphemeralMetrics(service=service, namespace=namespace)

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    @my_isolated_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))

    output = capture_metrics_output(capsys)

    # THEN ColdStart metric and function_name and service dimension should be logged
    assert output["ColdStart"] == [1.0]
    assert output["function_name"] == "example_fn"
    assert output["service"] == service
