from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from aws_lambda_powertools.metrics import (
    SchemaValidationError,
)
from aws_lambda_powertools.metrics.provider import BaseProvider
from aws_lambda_powertools.utilities.typing import LambdaContext


def capture_metrics_output(capsys):
    return json.loads(capsys.readouterr().out.strip())


class FakeMetricsProvider(BaseProvider):
    def __init__(self):
        self.metric_store: List = []

    def add_metric(self, name: str, value: float, tag: List = None, *args, **kwargs):
        self.metric_store.append({"name": name, "value": value})

    def serialize_metric_set(self, raise_on_empty_metrics: bool = False, *args, **kwargs):
        if raise_on_empty_metrics and len(self.metric_store) == 0:
            raise SchemaValidationError("Must contain at least one metric.")

        self.result = json.dumps(self.metric_store)

    def flush_metrics(self, *args, **kwargs):
        print(json.dumps(self.metric_store))

    def clear_metrics(self):
        self.metric_store = []

    def add_cold_start_metric(self, context: LambdaContext) -> Any:
        self.metric_store.append({"name": "ColdStart", "value": 1, "function_name": context.function_name})

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        **kwargs,
    ):
        return super().log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
        )


class FakeMetricsClass:
    def __init__(self, provider: FakeMetricsProvider | None = None):
        if provider is None:
            self.provider = FakeMetricsProvider()
        else:
            self.provider = provider

    def add_metric(self, name: str, value: float, tag: List = None, *args, **kwargs):
        self.provider.add_metric(name=name, value=value, tag=tag)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        self.provider.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

    def add_cold_start_metric(self, context: LambdaContext) -> None:
        self.provider.add_cold_start_metric(context=context)

    def serialize_metric_set(self, raise_on_empty_metrics: bool = False, *args, **kwargs):
        self.provider.serialize_metric_set(raise_on_empty_metrics=raise_on_empty_metrics)

    def clear_metrics(self) -> None:
        self.provider.clear_metrics()

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        default_dimensions: Dict[str, str] | None = None,
    ):
        return self.provider.log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
        )


def test_metrics_class_with_default_provider(capsys, metric):
    metrics = FakeMetricsClass()
    metrics.add_metric(**metric)
    metrics.flush_metrics()
    output = capture_metrics_output(capsys)
    assert output[0]["name"] == metric["name"]
    assert output[0]["value"] == metric["value"]


def test_metrics_class_with_custom_provider(capsys, metric):
    provider = FakeMetricsProvider()
    metrics = FakeMetricsClass(provider=provider)
    metrics.add_metric(**metric)
    metrics.flush_metrics()
    output = capture_metrics_output(capsys)
    assert output[0]["name"] == metric["name"]
    assert output[0]["value"] == metric["value"]


def test_metrics_provider_class_decorate():
    # GIVEN Metrics is initialized
    my_metrics = FakeMetricsClass()

    # WHEN log_metrics is used to serialize metrics
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        return True

    # THEN log_metrics should invoke the function it decorates
    # and return no error if we have a namespace and dimension
    assert lambda_handler({}, {}) is True
