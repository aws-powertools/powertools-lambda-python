import json
from typing import Dict, List

import pytest

from aws_lambda_powertools.metrics import (
    Metrics,
    MetricUnit,
    MetricUnitError,
    MetricValueError,
    SchemaValidationError,
    UniqueNamespaceError,
    single_metric,
)
from aws_lambda_powertools.metrics.base import MetricManager


@pytest.fixture
def metric() -> Dict[str, str]:
    return {"name": "single_metric", "unit": MetricUnit.Count, "value": 1}


@pytest.fixture
def metrics() -> List[Dict[str, str]]:
    return [
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 1},
        {"name": "metric_two", "unit": MetricUnit.Count, "value": 1},
    ]


@pytest.fixture
def dimension() -> Dict[str, str]:
    return {"name": "test_dimension", "value": "test"}


@pytest.fixture
def dimensions() -> List[Dict[str, str]]:
    return [
        {"name": "test_dimension", "value": "test"},
        {"name": "test_dimension_2", "value": "test"},
    ]


@pytest.fixture
def namespace() -> Dict[str, str]:
    return {"name": "test_namespace"}


@pytest.fixture
def a_hundred_metrics() -> List[Dict[str, str]]:
    metrics = []
    for i in range(100):
        metrics.append({"name": f"metric_{i}", "unit": "Count", "value": 1})

    return metrics


def serialize_metrics(metrics: List[Dict], dimensions: List[Dict], namespace: Dict) -> Dict:
    """ Helper function to build EMF object from a list of metrics, dimensions """
    my_metrics = Metrics()
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    my_metrics.add_namespace(**namespace)
    for metric in metrics:
        my_metrics.add_metric(**metric)

    if len(metrics) != 100:
        return my_metrics.serialize_metric_set()


def serialize_single_metric(metric: Dict, dimension: Dict, namespace: Dict) -> Dict:
    """ Helper function to build EMF object from a given metric, dimension and namespace """
    my_metrics = MetricManager()
    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)
    return my_metrics.serialize_metric_set()


def remove_timestamp(metrics: List):
    """ Helper function to remove Timestamp key from EMF objects as they're built at serialization """
    for metric in metrics:
        del metric["_aws"]["Timestamp"]


def test_single_metric(capsys, metric, dimension, namespace):
    with single_metric(**metric) as my_metric:
        my_metric.add_dimension(**dimension)
        my_metric.add_namespace(**namespace)

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]


def test_single_metric_one_metric_only(capsys, metric, dimension, namespace):
    with single_metric(**metric) as my_metric:
        my_metric.add_metric(name="second_metric", unit="Count", value=1)
        my_metric.add_metric(name="third_metric", unit="Seconds", value=1)
        my_metric.add_dimension(**dimension)
        my_metric.add_namespace(**namespace)

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]


def test_multiple_metrics(metrics, dimensions, namespace):
    my_metrics = Metrics()
    for metric in metrics:
        my_metrics.add_metric(**metric)

    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    my_metrics.add_namespace(**namespace)
    output = my_metrics.serialize_metric_set()
    expected = serialize_metrics(metrics=metrics, dimensions=dimensions, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]


def test_multiple_namespaces(metric, dimension, namespace):
    namespace_a = {"name": "OtherNamespace"}
    namespace_b = {"name": "AnotherNamespace"}

    with pytest.raises(UniqueNamespaceError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)
            my_metric.add_namespace(**namespace_a)
            my_metric.add_namespace(**namespace_b)


def test_log_metrics(capsys, metrics, dimensions, namespace):
    my_metrics = Metrics()
    my_metrics.add_namespace(**namespace)
    for metric in metrics:
        my_metrics.add_metric(**metric)
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    @my_metrics.log_metrics
    def lambda_handler(evt, handler):
        return True

    lambda_handler({}, {})
    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_metrics(metrics=metrics, dimensions=dimensions, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]
    for dimension in dimensions:
        assert dimension["name"] in output


def test_namespace_env_var(monkeypatch, capsys, metric, dimension, namespace):
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", namespace["name"])

    with single_metric(**metric) as my_metrics:
        my_metrics.add_dimension(**dimension)
        monkeypatch.delenv("POWERTOOLS_METRICS_NAMESPACE")

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]


def test_metrics_spillover(monkeypatch, capsys, metric, dimension, namespace, a_hundred_metrics):
    my_metrics = Metrics()
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)

    for _metric in a_hundred_metrics:
        my_metrics.add_metric(**_metric)

    @my_metrics.log_metrics
    def lambda_handler(evt, handler):
        my_metrics.add_metric(**metric)
        return True

    lambda_handler({}, {})

    output = capsys.readouterr().out.strip()
    spillover_metrics, single_metric = output.split("\n")
    spillover_metrics = json.loads(spillover_metrics)
    single_metric = json.loads(single_metric)

    expected_single_metric = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    serialize_metrics(metrics=a_hundred_metrics, dimensions=[dimension], namespace=namespace)
    expected_spillover_metrics = json.loads(capsys.readouterr().out.strip())

    remove_timestamp(metrics=[spillover_metrics, expected_spillover_metrics, single_metric, expected_single_metric])

    assert single_metric["_aws"] == expected_single_metric["_aws"]
    assert spillover_metrics["_aws"] == expected_spillover_metrics["_aws"]


def test_log_metrics_schema_error(metrics, dimensions, namespace):
    # It should error out because by default log_metrics doesn't invoke a function
    # so when decorator runs it'll raise an error while trying to serialize metrics
    my_metrics = Metrics()

    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        my_metrics.add_namespace(namespace)
        for metric in metrics:
            my_metrics.add_metric(**metric)
        for dimension in dimensions:
            my_metrics.add_dimension(**dimension)
            return True

    with pytest.raises(SchemaValidationError):
        lambda_handler({}, {})


def test_incorrect_metric_unit(metric, dimension, namespace):
    metric["unit"] = "incorrect_unit"

    with pytest.raises(MetricUnitError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_schema_no_namespace(metric, dimension):
    with pytest.raises(SchemaValidationError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)


def test_schema_incorrect_value(metric, dimension, namespace):
    metric["value"] = "some_value"
    with pytest.raises(MetricValueError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_schema_no_metrics(dimensions, namespace):
    my_metrics = Metrics()
    my_metrics.add_namespace(**namespace)
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)
    with pytest.raises(SchemaValidationError):
        my_metrics.serialize_metric_set()


def test_exceed_number_of_dimensions(metric, namespace):
    dimensions = []
    for i in range(11):
        dimensions.append({"name": f"test_{i}", "value": "test"})

    with pytest.raises(SchemaValidationError):
        with single_metric(**metric) as my_metric:
            my_metric.add_namespace(**namespace)
            for dimension in dimensions:
                my_metric.add_dimension(**dimension)


def test_log_metrics_error_propagation(capsys, metric, dimension, namespace):
    # GIVEN Metrics are serialized after handler execution
    # WHEN If an error occurs and metrics have been added
    # THEN we should log metrics and propagate exception up
    my_metrics = Metrics()

    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)

    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        raise ValueError("Bubble up")

    with pytest.raises(ValueError):
        lambda_handler({}, {})

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    assert expected["_aws"] == output["_aws"]


def test_log_no_metrics_error_propagation(capsys, metric, dimension, namespace):
    # GIVEN Metrics are serialized after handler execution
    # WHEN If an error occurs and no metrics have been added
    # THEN we should propagate exception up and raise SchemaValidationError
    my_metrics = Metrics()

    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        raise ValueError("Bubble up")

    with pytest.raises(SchemaValidationError):
        lambda_handler({}, {})


def test_all_metric_units_string(metric, dimension, namespace):

    # metric unit as MetricUnit key e.g. "Seconds", "BytesPerSecond"
    for unit in MetricUnit:
        metric["unit"] = unit.name
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)

    with pytest.raises(MetricUnitError):
        metric["unit"] = "seconds"
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)

    all_metric_units = [unit.value for unit in MetricUnit]

    # metric unit as MetricUnit value e.g. "Seconds", "Bytes/Second"
    for unit in all_metric_units:
        metric["unit"] = unit
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_metrics_reuse_metric_set(metric, dimension, namespace):
    my_metrics = Metrics()
    my_metrics.add_metric(**metric)
    m = Metrics()

    assert m.metric_set == my_metrics.metric_set
