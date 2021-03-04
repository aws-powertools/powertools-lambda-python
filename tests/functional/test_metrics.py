import json
import warnings
from collections import namedtuple
from typing import Any, Dict, List

import pytest

from aws_lambda_powertools import Metrics, single_metric
from aws_lambda_powertools.metrics import MetricUnit, MetricUnitError, MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics import metrics as metrics_global
from aws_lambda_powertools.metrics.base import MetricManager


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    metrics = Metrics()
    metrics.clear_metrics()
    metrics_global.is_cold_start = True  # ensure each test has cold start
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
def metrics_same_name() -> List[Dict[str, str]]:
    return [
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 1},
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 5},
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
def non_str_dimensions() -> List[Dict[str, Any]]:
    return [
        {"name": "test_dimension", "value": True},
        {"name": "test_dimension_2", "value": 3},
    ]


@pytest.fixture
def namespace() -> str:
    return "test_namespace"


@pytest.fixture
def service() -> str:
    return "test_service"


@pytest.fixture
def metadata() -> Dict[str, str]:
    return {"key": "username", "value": "test"}


@pytest.fixture
def a_hundred_metrics() -> List[Dict[str, str]]:
    return [{"name": f"metric_{i}", "unit": "Count", "value": 1} for i in range(100)]


def serialize_metrics(
    metrics: List[Dict], dimensions: List[Dict], namespace: str, metadatas: List[Dict] = None
) -> Dict:
    """ Helper function to build EMF object from a list of metrics, dimensions """
    my_metrics = MetricManager(namespace=namespace)
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    for metric in metrics:
        my_metrics.add_metric(**metric)

    if metadatas is not None:
        for metadata in metadatas:
            my_metrics.add_metadata(**metadata)

    if len(metrics) != 100:
        return my_metrics.serialize_metric_set()


def serialize_single_metric(metric: Dict, dimension: Dict, namespace: str, metadata: Dict = None) -> Dict:
    """ Helper function to build EMF object from a given metric, dimension and namespace """
    my_metrics = MetricManager(namespace=namespace)
    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)

    if metadata is not None:
        my_metrics.add_metadata(**metadata)

    return my_metrics.serialize_metric_set()


def remove_timestamp(metrics: List):
    """ Helper function to remove Timestamp key from EMF objects as they're built at serialization """
    for metric in metrics:
        del metric["_aws"]["Timestamp"]


def capture_metrics_output(capsys):
    return json.loads(capsys.readouterr().out.strip())


def capture_metrics_output_multiple_emf_objects(capsys):
    return [json.loads(line.strip()) for line in capsys.readouterr().out.split("\n") if line]


def test_single_metric_logs_one_metric_only(capsys, metric, dimension, namespace):
    # GIVEN we try adding more than one metric
    # WHEN using single_metric context manager
    with single_metric(namespace=namespace, **metric) as my_metric:
        my_metric.add_metric(name="second_metric", unit="Count", value=1)
        my_metric.add_dimension(**dimension)

    output = capture_metrics_output(capsys)
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    # THEN we should only have the first metric added
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_log_metrics(capsys, metrics, dimensions, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)
    for metric in metrics:
        my_metrics.add_metric(**metric)
    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    # WHEN we utilize log_metrics to serialize
    # and flush all metrics at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        pass

    lambda_handler({}, {})
    output = capture_metrics_output(capsys)
    expected = serialize_metrics(metrics=metrics, dimensions=dimensions, namespace=namespace)

    # THEN we should have no exceptions
    # and a valid EMF object should be flushed correctly
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_namespace_env_var(monkeypatch, capsys, metric, dimension, namespace):
    # GIVEN POWERTOOLS_METRICS_NAMESPACE is set
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", namespace)

    # WHEN creating a metric without explicitly adding a namespace
    with single_metric(**metric) as my_metric:
        my_metric.add_dimension(**dimension)

    output = capture_metrics_output(capsys)
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    # THEN we should add a namespace using POWERTOOLS_METRICS_NAMESPACE env var value
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_service_env_var(monkeypatch, capsys, metric, namespace):
    # GIVEN we use POWERTOOLS_SERVICE_NAME
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "test_service")

    # WHEN creating a metric without explicitly adding a dimension
    with single_metric(**metric, namespace=namespace):
        pass

    output = capture_metrics_output(capsys)
    expected_dimension = {"name": "service", "value": "test_service"}
    expected = serialize_single_metric(metric=metric, dimension=expected_dimension, namespace=namespace)

    # THEN a metric should be logged using the implicitly created "service" dimension
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_metrics_spillover(monkeypatch, capsys, metric, dimension, namespace, a_hundred_metrics):
    # GIVEN Metrics is initialized and we have over a hundred metrics to add
    my_metrics = Metrics(namespace=namespace)
    my_metrics.add_dimension(**dimension)

    # WHEN we add more than 100 metrics
    for _metric in a_hundred_metrics:
        my_metrics.add_metric(**_metric)

    # THEN it should serialize and flush all metrics at the 100th
    # and clear all metrics and dimensions from memory
    output = capture_metrics_output(capsys)
    spillover_metrics = output["_aws"]["CloudWatchMetrics"][0]["Metrics"]
    assert my_metrics.metric_set == {}
    assert len(spillover_metrics) == 100

    # GIVEN we add the 101th metric
    # WHEN we already had a Metric class instance
    # with an existing dimension set from the previous 100th metric batch
    my_metrics.add_metric(**metric)

    # THEN serializing the 101th metric should
    # create a new EMF object with a single metric in it (101th)
    # and contain the same dimension we previously added
    serialized_101th_metric = my_metrics.serialize_metric_set()
    expected_101th_metric = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)
    remove_timestamp(metrics=[serialized_101th_metric, expected_101th_metric])
    assert serialized_101th_metric == expected_101th_metric


def test_log_metrics_decorator_call_decorated_function(metric, namespace, service):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics is used to serialize metrics
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        return True

    # THEN log_metrics should invoke the function it decorates
    # and return no error if we have a namespace and dimension
    assert lambda_handler({}, {}) is True


def test_schema_validation_incorrect_metric_unit(metric, dimension, namespace):
    # GIVEN we pass a metric unit that is not supported by CloudWatch
    metric["unit"] = "incorrect_unit"

    # WHEN we try adding a new metric
    # THEN it should fail metric unit validation
    with pytest.raises(MetricUnitError):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)


def test_schema_validation_no_namespace(metric, dimension):
    # GIVEN we don't add any namespace
    # WHEN we attempt to serialize a valid EMF object
    # THEN it should fail namespace validation
    with pytest.raises(SchemaValidationError, match="Must contain a metric namespace."):
        with single_metric(**metric) as my_metric:
            my_metric.add_dimension(**dimension)


def test_schema_validation_incorrect_metric_value(metric, dimension, namespace):
    # GIVEN we pass an incorrect metric value (non-numeric)
    metric["value"] = "some_value"

    # WHEN we attempt to serialize a valid EMF object
    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(MetricValueError, match=".*is not a valid number"):
        with single_metric(**metric):
            pass


def test_schema_no_metrics(service, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Must contain at least one metric."):
        my_metrics.serialize_metric_set()


def test_exceed_number_of_dimensions(metric, namespace):
    # GIVEN we we have more dimensions than CloudWatch supports
    dimensions = [{"name": f"test_{i}", "value": "test"} for i in range(11)]

    # WHEN we attempt to serialize them into a valid EMF object
    # THEN it should fail validation and raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Maximum number of dimensions exceeded.*"):
        with single_metric(**metric, namespace=namespace) as my_metric:
            for dimension in dimensions:
                my_metric.add_dimension(**dimension)


def test_log_metrics_during_exception(capsys, metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_metric(**metric)

    # WHEN log_metrics is used to serialize metrics
    # but an error has been raised during handler execution
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        raise ValueError("Bubble up")

    with pytest.raises(ValueError):
        lambda_handler({}, {})

    output = capture_metrics_output(capsys)
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace)

    # THEN we should log metrics either way
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_log_metrics_raise_on_empty_metrics(capsys, metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service="test_service", namespace=namespace)

    # WHEN log_metrics is used with raise_on_empty_metrics param and has no metrics
    @my_metrics.log_metrics(raise_on_empty_metrics=True)
    def lambda_handler(evt, context):
        pass

    # THEN the raised exception should be SchemaValidationError
    # and specifically about the lack of Metrics
    with pytest.raises(SchemaValidationError, match="Must contain at least one metric."):
        lambda_handler({}, {})


def test_all_possible_metric_units(metric, dimension, namespace):
    # GIVEN we add a metric for each metric unit supported by CloudWatch
    # where metric unit as MetricUnit key e.g. "Seconds", "BytesPerSecond"
    for unit in MetricUnit:
        metric["unit"] = unit.name
        # WHEN we iterate over all available metric unit keys from MetricUnit enum
        # THEN we raise no MetricUnitError nor SchemaValidationError
        with single_metric(namespace=namespace, **metric) as my_metric:
            my_metric.add_dimension(**dimension)

    # WHEN we iterate over all available metric unit keys from MetricUnit enum
    all_metric_units = [unit.value for unit in MetricUnit]

    for unit in all_metric_units:
        metric["unit"] = unit  # e.g. "Seconds", "Bytes/Second"
        # THEN we raise no MetricUnitError nor SchemaValidationError
        with single_metric(namespace=namespace, **metric) as my_metric:
            my_metric.add_dimension(**dimension)


def test_metrics_reuse_metric_set(metric, dimension, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN Metrics is initialized one more time
    my_metrics_2 = Metrics(namespace=namespace)

    # THEN Both class instances should have the same metric set
    assert my_metrics_2.metric_set == my_metrics.metric_set


def test_log_metrics_clear_metrics_after_invocation(metric, service, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN log_metrics is used to flush metrics from memory
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        pass

    lambda_handler({}, {})

    # THEN metric set should be empty after function has been run
    assert my_metrics.metric_set == {}


def test_log_metrics_non_string_dimension_values(capsys, service, metric, non_str_dimensions, namespace):
    # GIVEN Metrics is initialized and dimensions with non-string values are added
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)
    for dimension in non_str_dimensions:
        my_metrics.add_dimension(**dimension)

    # WHEN we utilize log_metrics to serialize
    # and flush all metrics at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        pass

    lambda_handler({}, {})
    output = capture_metrics_output(capsys)

    # THEN we should have no exceptions
    # and dimension values should be serialized as strings
    for dimension in non_str_dimensions:
        assert isinstance(output[dimension["name"]], str)


def test_log_metrics_with_explicit_namespace(capsys, metric, service, namespace):
    # GIVEN Metrics is initialized with explicit namespace
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN we utilize log_metrics to serialize
    # and flush all metrics at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        pass

    lambda_handler({}, {})

    output = capture_metrics_output(capsys)

    # THEN we should have no exceptions and the namespace should be set
    # using the service value passed to Metrics constructor
    assert namespace == output["_aws"]["CloudWatchMetrics"][0]["Namespace"]


def test_log_metrics_with_implicit_dimensions(capsys, metric, namespace, service):
    # GIVEN Metrics is initialized with service specified
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN we utilize log_metrics to serialize and don't explicitly add any dimensions
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        pass

    lambda_handler({}, {})

    output = capture_metrics_output(capsys)

    # THEN we should have no exceptions and the dimensions should be set to the name provided in the
    # service passed to Metrics constructor
    assert service == output["service"]


def test_log_metrics_with_renamed_service(capsys, metric, service):
    # GIVEN Metrics is initialized with service specified
    my_metrics = Metrics(service=service, namespace="test_application")
    another_service_dimension = {"name": "service", "value": "another_test_service"}

    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        # WHEN we manually call add_dimension to change the value of the service dimension
        my_metrics.add_dimension(**another_service_dimension)
        my_metrics.add_metric(**metric)

    lambda_handler({}, {})
    output = capture_metrics_output(capsys)

    lambda_handler({}, {})
    second_output = capture_metrics_output(capsys)

    # THEN we should have no exceptions and the dimensions should be set to the name provided in the
    # add_dimension call
    assert output["service"] == another_service_dimension["value"]
    assert second_output["service"] == another_service_dimension["value"]


def test_namespace_var_precedence(monkeypatch, capsys, metric, dimension, namespace):
    # GIVEN we use POWERTOOLS_METRICS_NAMESPACE
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", "a_namespace")

    # WHEN creating a metric and explicitly set a namespace
    with single_metric(namespace=namespace, **metric) as my_metrics:
        my_metrics.add_dimension(**dimension)

    output = capture_metrics_output(capsys)

    # THEN namespace should match the explicitly passed variable and not the env var
    assert namespace == output["_aws"]["CloudWatchMetrics"][0]["Namespace"]


def test_log_metrics_capture_cold_start_metric(capsys, namespace, service):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))

    output = capture_metrics_output(capsys)

    # THEN ColdStart metric and function_name dimension should be logged
    assert output["ColdStart"] == [1.0]
    assert output["function_name"] == "example_fn"


def test_emit_cold_start_metric_only_once(capsys, namespace, service, metric):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics is used with capture_cold_start_metric
    # and handler is called more than once
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        my_metrics.add_metric(**metric)

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))
    _, _ = capture_metrics_output_multiple_emf_objects(capsys)  # ignore first stdout captured

    # THEN ColdStart metric and function_name dimension should be logged once
    lambda_handler({}, LambdaContext("example_fn"))
    output = capture_metrics_output(capsys)

    assert "ColdStart" not in output
    assert "function_name" not in output


def test_log_metrics_decorator_no_metrics_warning(dimensions, namespace, service):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace, service=service)

    # WHEN using the log_metrics decorator and no metrics have been added
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        pass

    # THEN it should raise a warning instead of throwing an exception
    with warnings.catch_warnings(record=True) as w:
        lambda_handler({}, {})
        assert len(w) == 1
        assert str(w[-1].message) == "No metrics to publish, skipping"


def test_log_metrics_with_implicit_dimensions_called_twice(capsys, metric, namespace, service):
    # GIVEN Metrics is initialized with service specified
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN we utilize log_metrics to serialize and don't explicitly add any dimensions,
    # and the lambda function is called more than once
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        my_metrics.add_metric(**metric)
        return True

    lambda_handler({}, {})
    output = capture_metrics_output(capsys)

    lambda_handler({}, {})
    second_output = capture_metrics_output(capsys)

    # THEN we should have no exceptions and the dimensions should be set to the name provided in the
    # service passed to Metrics constructor
    assert output["service"] == "test_service"
    assert second_output["service"] == "test_service"

    for metric_record in output["_aws"]["CloudWatchMetrics"]:
        assert ["service"] in metric_record["Dimensions"]

    for metric_record in second_output["_aws"]["CloudWatchMetrics"]:
        assert ["service"] in metric_record["Dimensions"]


def test_add_metadata_non_string_dimension_keys(service, metric, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN we utilize add_metadata with non-string keys
    my_metrics.add_metadata(key=10, value="number_ten")

    # THEN we should have no exceptions
    # and dimension values should be serialized as strings
    expected_metadata = {"10": "number_ten"}
    assert my_metrics.metadata_set == expected_metadata


def test_add_metadata(service, metric, namespace, metadata):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)

    # WHEN we utilize add_metadata with non-string keys
    my_metrics.add_metadata(**metadata)

    # THEN we should have no exceptions
    # and dimension values should be serialized as strings
    assert my_metrics.metadata_set == {metadata["key"]: metadata["value"]}


def test_log_metrics_with_metadata(capsys, metric, dimension, namespace, service, metadata):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)
    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)

    # WHEN we utilize log_metrics to serialize and add metadata
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        my_metrics.add_metadata(**metadata)
        pass

    lambda_handler({}, {})

    output = capture_metrics_output(capsys)
    expected = serialize_single_metric(metric=metric, dimension=dimension, namespace=namespace, metadata=metadata)

    # THEN we should have no exceptions and metadata
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_serialize_metric_set_metric_definition(metric, dimension, namespace, service, metadata):
    expected_metric_definition = {
        "single_metric": [1.0],
        "_aws": {
            "Timestamp": 1592237875494,
            "CloudWatchMetrics": [
                {
                    "Namespace": "test_namespace",
                    "Dimensions": [["test_dimension", "service"]],
                    "Metrics": [{"Name": "single_metric", "Unit": "Count"}],
                }
            ],
        },
        "service": "test_service",
        "username": "test",
        "test_dimension": "test",
    }

    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)
    my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_metadata(**metadata)

    # WHEN metrics are serialized manually
    metric_definition_output = my_metrics.serialize_metric_set()

    # THEN we should emit a valid embedded metric definition object
    assert "Timestamp" in metric_definition_output["_aws"]
    remove_timestamp(metrics=[metric_definition_output, expected_metric_definition])
    assert metric_definition_output == expected_metric_definition


def test_log_metrics_capture_cold_start_metric_separately(capsys, namespace, service, metric, dimension):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        my_metrics.add_metric(**metric)
        my_metrics.add_dimension(**dimension)

    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))

    cold_start_blob, custom_metrics_blob = capture_metrics_output_multiple_emf_objects(capsys)

    # THEN ColdStart metric and function_name dimension should be logged
    # in a separate EMF blob than the application metrics
    assert cold_start_blob["ColdStart"] == [1.0]
    assert cold_start_blob["function_name"] == "example_fn"
    assert cold_start_blob["service"] == service

    # and that application metrics dimensions are not part of ColdStart EMF blob
    assert "test_dimension" not in cold_start_blob

    # THEN application metrics EMF blob should not have
    # ColdStart metric nor function_name dimension
    assert "function_name" not in custom_metrics_blob
    assert "ColdStart" not in custom_metrics_blob

    # and that application metrics are recorded as normal
    assert custom_metrics_blob["service"] == service
    assert custom_metrics_blob["single_metric"] == [float(metric["value"])]
    assert custom_metrics_blob["test_dimension"] == dimension["value"]


def test_log_multiple_metrics(capsys, metrics_same_name, dimensions, namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)

    for dimension in dimensions:
        my_metrics.add_dimension(**dimension)

    # WHEN we utilize log_metrics to serialize
    # and flush multiple metrics with the same name at the end of a function execution
    @my_metrics.log_metrics
    def lambda_handler(evt, ctx):
        for metric in metrics_same_name:
            my_metrics.add_metric(**metric)

    lambda_handler({}, {})
    output = capture_metrics_output(capsys)
    expected = serialize_metrics(metrics=metrics_same_name, dimensions=dimensions, namespace=namespace)

    # THEN we should have no exceptions
    # and a valid EMF object should be flushed correctly
    remove_timestamp(metrics=[output, expected])
    assert expected == output


def test_serialize_metric_set_metric_definition_multiple_values(
    metrics_same_name, dimension, namespace, service, metadata
):
    expected_metric_definition = {
        "metric_one": [1.0, 5.0],
        "_aws": {
            "Timestamp": 1592237875494,
            "CloudWatchMetrics": [
                {
                    "Namespace": "test_namespace",
                    "Dimensions": [["test_dimension", "service"]],
                    "Metrics": [{"Name": "metric_one", "Unit": "Count"}],
                }
            ],
        },
        "service": "test_service",
        "username": "test",
        "test_dimension": "test",
    }

    # GIVEN Metrics is initialized and multiple metrics are added with the same name
    my_metrics = Metrics(service=service, namespace=namespace)
    for metric in metrics_same_name:
        my_metrics.add_metric(**metric)
    my_metrics.add_dimension(**dimension)
    my_metrics.add_metadata(**metadata)

    # WHEN metrics are serialized manually
    metric_definition_output = my_metrics.serialize_metric_set()

    # THEN we should emit a valid embedded metric definition object
    assert "Timestamp" in metric_definition_output["_aws"]
    remove_timestamp(metrics=[metric_definition_output, expected_metric_definition])
    assert metric_definition_output == expected_metric_definition
