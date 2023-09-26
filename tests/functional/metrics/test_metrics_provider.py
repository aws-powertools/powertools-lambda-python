from __future__ import annotations

import json
from typing import Any, List

from aws_lambda_powertools.metrics import (
    SchemaValidationError,
)
from aws_lambda_powertools.metrics.metrics import Metrics
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
        self.metric_store.clear()

    def add_cold_start_metric(self, context: LambdaContext) -> Any:
        self.metric_store.append({"name": "ColdStart", "value": 1, "function_name": context.function_name})


def test_metrics_class_with_custom_provider(capsys, metric):
    provider = FakeMetricsProvider()
    metrics = Metrics(provider=provider)
    metrics.add_metric(**metric)
    metrics.flush_metrics()
    output = capture_metrics_output(capsys)
    assert output[0]["name"] == metric["name"]
    assert output[0]["value"] == metric["value"]


def test_metrics_provider_class_decorate():
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    # WHEN log_metrics is used to serialize metrics
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        return True

    # THEN log_metrics should invoke the function it decorates
    # and return no error if we have a namespace and dimension
    assert lambda_handler({}, {}) is True


def test_metrics_provider_class_decorator_with_additional_handler_args():
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    # WHEN log_metrics is used to serialize metrics
    # AND the wrapped function uses additional parameters
    @my_metrics.log_metrics
    def lambda_handler(evt, context, additional_arg, additional_kw_arg="default_value"):
        return additional_arg, additional_kw_arg

    # THEN the decorator should not raise any errors when
    # the wrapped function is passed additional arguments
    assert lambda_handler({}, {}, "arg_value", additional_kw_arg="kw_arg_value") == ("arg_value", "kw_arg_value")
    assert lambda_handler({}, {}, "arg_value") == ("arg_value", "default_value")
