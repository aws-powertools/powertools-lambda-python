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


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    metrics = Metrics()
    metrics.clear_metrics()
    yield


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
    my_metrics = MetricManager()
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


def test_single_metric_one_metric_only(capsys, metric, dimension, namespace):
    # GIVEN we attempt to add more than one metric
    # WHEN using single_metric context manager
    with single_metric(**metric) as my_metric:
        my_metric.add_metric(name="second_metric", unit="Count", value=1)
        my_metric.add_metric(name="third_metric", unit="Seconds", value=1)
        my_metric.add_dimension(**dimension)
        my_metric.add_namespace(**namespace)

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different

    # THEN we should only have the first metric added
    assert expected["_aws"] == output["_aws"]


def test_multiple_namespaces_exception(metric, dimension, namespace):
    # GIVEN we attempt to add multiple namespaces
    namespace_a = {"name": "OtherNamespace"}
    namespace_b = {"name": "AnotherNamespace"}

    # WHEN an EMF object can only have one
    # THEN we should raise UniqueNamespaceError exception
    with pytest.raises(UniqueNamespaceError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)
            my_metric.add_namespace(**namespace_a)
            my_metric.add_namespace(**namespace_b)


def test_log_metrics(capsys, metrics, dimensions, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()
    my_metrics.add_namespace(**namespace)
    for metric in metrics:
        my_metrics.add_metric(**metric)
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    # WHEN we utilize log_metrics to serialize
    # and flush all metrics at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_metrics(metrics=metrics, dimensions=dimensions, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different

    # THEN we should have no exceptions
    # and a valid EMF object should've been flushed correctly
    assert expected["_aws"] == output["_aws"]
    for dimension in dimensions:
        assert dimension["name"] in output


def test_namespace_env_var(monkeypatch, capsys, metric, dimension, namespace):
    # GIVEN we use POWERTOOLS_METRICS_NAMESPACE
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", namespace["name"])

    # WHEN creating a metric but don't explicitly
    # add a namespace
    with single_metric(**metric) as my_metrics:
        my_metrics.add_dimension(**dimension)
        monkeypatch.delenv("POWERTOOLS_METRICS_NAMESPACE")

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different

    # THEN we should add a namespace implicitly
    # with the value of POWERTOOLS_METRICS_NAMESPACE env var
    assert expected["_aws"] == output["_aws"]


def test_metrics_spillover(monkeypatch, capsys, metric, dimension, namespace, a_hundred_metrics):
    # GIVEN Metrics is initialized and we have over a hundred metrics to add
    my_metrics = Metrics()
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)

    # WHEN we add more than 100 metrics
    for _metric in a_hundred_metrics:
        my_metrics.add_metric(**_metric)

    # THEN it should serialize and flush all metrics at the 100th
    # and clear all metrics and dimensions from memory
    output = json.loads(capsys.readouterr().out.strip())
    spillover_metrics = output["_aws"]["CloudWatchMetrics"][0]["Metrics"]
    assert my_metrics.metric_set == {}
    assert len(spillover_metrics) == 100

    # GIVEN we add the 101th metric
    # WHEN we already had a Metric class instance
    # with an existing dimension set from the previous 100th metric batch
    my_metrics.add_metric(**metric)

    # THEN serializing the 101th metric should
    # create a new EMF object with a single metric in it (101th)
    # and contain have the same dimension we previously added
    serialized_101th_metric = my_metrics.serialize_metric_set()
    expected_101th_metric = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)
    remove_timestamp(metrics=[serialized_101th_metric, expected_101th_metric])

    assert serialized_101th_metric["_aws"] == expected_101th_metric["_aws"]


def test_log_metrics_should_invoke_function(metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    # WHEN log_metrics is used to serialize metrics
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        my_metrics.add_namespace(**namespace)
        my_metrics.add_metric(**metric)
        my_metrics.add_dimension(**dimension)
        return True

    # THEN log_metrics should invoke the function it decorates
    # and return no error if we have a metric, namespace, and a dimension
    lambda_handler({}, {})


def test_incorrect_metric_unit(metric, dimension, namespace):
    # GIVEN we pass a metric unit not supported by CloudWatch
    metric["unit"] = "incorrect_unit"

    # WHEN we attempt to add a new metric
    # THEN it should fail validation and raise MetricUnitError
    with pytest.raises(MetricUnitError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_schema_no_namespace(metric, dimension):
    # GIVEN we don't add any metric or dimension
    # but a namespace

    # WHEN we attempt to serialize a valid EMF object
    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(SchemaValidationError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)


def test_schema_incorrect_value(metric, dimension, namespace):
    # GIVEN we pass an incorrect metric value (non-number/float)
    metric["value"] = "some_value"

    # WHEN we attempt to serialize a valid EMF object
    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(MetricValueError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_schema_no_metrics(dimensions, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()
    my_metrics.add_namespace(**namespace)

    # WHEN no metrics have been added
    # but a namespace and dimensions only
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(SchemaValidationError):
        my_metrics.serialize_metric_set()


def test_exceed_number_of_dimensions(metric, namespace):
    # GIVEN we we have more dimensions than CloudWatch supports
    dimensions = []
    for i in range(11):
        dimensions.append({"name": f"test_{i}", "value": "test"})

    # WHEN we attempt to serialize them into a valid EMF object
    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(SchemaValidationError):
        with single_metric(**metric) as my_metric:
            my_metric.add_namespace(**namespace)
            for dimension in dimensions:
                my_metric.add_dimension(**dimension)


def test_log_metrics_during_exception(capsys, metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)

    # WHEN log_metrics is used to serialize metrics
    # but an error has been raised during handler execution
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        raise ValueError("Bubble up")

    with pytest.raises(ValueError):
        lambda_handler({}, {})

    output = json.loads(capsys.readouterr().out.strip())
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    remove_timestamp(metrics=[output, expected])  # Timestamp will always be different
    # THEN we should log metrics and propagate the exception up
    assert expected["_aws"] == output["_aws"]


def test_log_no_metrics_error_propagation(capsys, metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        # WHEN log_metrics is used despite having no metrics
        # and the function decorated also raised an exception
        raise ValueError("Bubble up")

    # THEN we should first raise SchemaValidationError as the main exception
    with pytest.raises(SchemaValidationError):
        lambda_handler({}, {})


def test_all_possible_metric_units(metric, dimension, namespace):

    # GIVEN we add a metric for each metric unit supported by CloudWatch
    # where metric unit as MetricUnit key e.g. "Seconds", "BytesPerSecond"
    for unit in MetricUnit:
        metric["unit"] = unit.name
        # WHEN we iterate over all available metric unit keys from MetricUnit enum
        # THEN we raise no MetricUnitError nor SchemaValidationError
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)

    # WHEN we iterate over all available metric unit keys from MetricUnit enum
    all_metric_units = [unit.value for unit in MetricUnit]

    # metric unit as MetricUnit value e.g. "Seconds", "Bytes/Second"
    for unit in all_metric_units:
        metric["unit"] = unit
        # THEN we raise no MetricUnitError nor SchemaValidationError
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)
            my_metric.add_namespace(**namespace)


def test_metrics_reuse_metric_set(metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()
    my_metrics.add_metric(**metric)

    # WHEN Metrics is initialized one more time
    my_metrics_2 = Metrics()

    # THEN Both class instances should have the same metric set
    assert my_metrics_2.metric_set == my_metrics.metric_set


def test_log_metrics_clear_metrics_after_invocation(metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics()

    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_namespace(**namespace)

    # WHEN log_metrics is used to flush metrics from memory
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        return True

    lambda_handler({}, {})

    # THEN metric set should be empty after function has been run
    assert my_metrics.metric_set == {}
