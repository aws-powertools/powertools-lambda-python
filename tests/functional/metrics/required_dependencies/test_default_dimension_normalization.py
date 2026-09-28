from __future__ import annotations

import json
import warnings
from typing import Any

import pytest

from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_DIMENSIONS
from tests.functional.metrics.required_dependencies.test_metrics_provider import FakeMetricsProvider


@pytest.fixture(autouse=True)
def isolate_metrics_state(reset_metric_set):
    shared_state = (Metrics._metrics, Metrics._dimensions, Metrics._metadata, Metrics._default_dimensions)
    for state in shared_state:
        state.clear()
    yield
    for state in shared_state:
        state.clear()


@pytest.mark.parametrize("value", [2, False, 1.5, None])
@pytest.mark.parametrize("flush_first", [False, True])
def test_default_dimensions_remain_strings_across_instances(capsys, namespace, metric, value, flush_first):
    first = Metrics(namespace=namespace)
    first.set_default_dimensions(version=value)

    if flush_first:
        first.add_metric(**metric)
        first.flush_metrics()

    # Construct and flush more instances to cover both shared state and warm invocations.
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        for _ in range(2):
            another = Metrics(namespace=namespace)
            another.add_metric(**metric)
            another.flush_metrics()

    assert not records
    outputs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(outputs) == 2 + int(flush_first)
    assert all(output["version"] == str(value) for output in outputs)
    assert another.default_dimensions is first.default_dimensions


def test_another_metrics_instance_accepts_29_default_dimensions(namespace):
    first = Metrics(namespace=namespace)
    defaults = {f"dimension_{index}": index for index in range(MAX_DIMENSIONS)}
    first.set_default_dimensions(**defaults)

    # Reusing existing dimensions must not warn or consume additional dimension slots.
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        another = Metrics(namespace=namespace)

    assert not records
    assert another.dimension_set == {name: str(value) for name, value in defaults.items()}
    assert another.dimension_set is first.dimension_set


@pytest.mark.parametrize("dimension_count", [1, MAX_DIMENSIONS])
def test_provider_normalizes_shared_defaults_without_adding_dimensions(namespace, metric, dimension_count):
    defaults = {f"dimension_{index}": index for index in range(dimension_count)}
    expected = {name: str(value) for name, value in defaults.items()}
    shared_dimensions = expected.copy()

    class CustomProvider(AmazonCloudWatchEMFProvider):
        def add_dimension(self, name: str, value: str) -> None:
            pytest.fail("Initializing a provider must not call an overridden add_dimension method")

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        provider = CustomProvider(
            namespace=namespace,
            dimension_set=shared_dimensions,
            default_dimensions=defaults,
        )

    assert not records
    assert provider.dimension_set is shared_dimensions
    assert provider.default_dimensions is defaults
    assert shared_dimensions == expected

    provider.add_metric(**metric)
    output = provider.serialize_metric_set()
    assert all(output[name] == value for name, value in expected.items())


def test_default_dimension_normalization_preserves_custom_provider(capsys, namespace, metric):
    first = Metrics(namespace=namespace)
    first.set_default_dimensions(version=2)
    provider = FakeMetricsProvider()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        another = Metrics(provider=provider)
        another.add_metric(**metric)
        another.flush_metrics()

    assert not records
    assert json.loads(capsys.readouterr().out) == [{"name": metric["name"], "value": metric["value"]}]
    assert another.provider is provider
    assert another.metric_set is first.metric_set
    assert another.metadata_set is first.metadata_set
    assert another.dimension_set is first.dimension_set
    assert another.default_dimensions is first.default_dimensions
    assert another.dimension_set["version"] == "2"


def test_default_dimension_normalization_preserves_subclass_state(namespace, metric):
    class IsolatedMetrics(Metrics):
        _metrics: dict[str, Any] = {}
        _dimensions: dict[str, str] = {}
        _metadata: dict[str, Any] = {}
        _default_dimensions: dict[str, Any] = {}

    base = Metrics(namespace=namespace)
    base.set_default_dimensions(environment="base")
    first = IsolatedMetrics(namespace=namespace)
    first.set_default_dimensions(version=2)
    first.add_metadata(key="source", value="subclass")
    first.add_metric(**metric)

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        another = IsolatedMetrics(namespace=namespace)
        output = another.serialize_metric_set()

    assert not records
    assert output["version"] == "2"
    assert output["source"] == "subclass"
    assert "environment" not in output
    assert another.metric_set is first.metric_set is IsolatedMetrics._metrics
    assert another.dimension_set is first.dimension_set is IsolatedMetrics._dimensions
    assert another.metadata_set is first.metadata_set is IsolatedMetrics._metadata
    assert another.default_dimensions is first.default_dimensions is IsolatedMetrics._default_dimensions
    assert base.dimension_set == {"environment": "base"}
    assert not base.metric_set
    assert not base.metadata_set


def test_metrics_public_state_attributes_remain_writable(namespace):
    metrics = Metrics(namespace=namespace)

    for attribute in ("metric_set", "dimension_set", "metadata_set", "default_dimensions"):
        provider_state = getattr(metrics.provider, attribute)
        replacement = {}
        setattr(metrics, attribute, replacement)

        assert getattr(metrics, attribute) is replacement
        assert getattr(metrics.provider, attribute) is provider_state
