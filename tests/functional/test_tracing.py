import contextlib

import pytest

from aws_lambda_powertools import Tracer


@pytest.fixture
def dummy_response():
    return {"test": "succeeds"}


@pytest.fixture(scope="function", autouse=True)
def reset_tracing_config():
    Tracer._reset_config()
    yield


@pytest.fixture
def service_name():
    return "booking"


def test_capture_lambda_handler(dummy_response):
    # GIVEN tracer lambda handler decorator is used
    tracer = Tracer(disabled=True)

    # WHEN a lambda handler is run
    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    # THEN tracer should not raise an Exception
    handler({}, {})


def test_capture_lambda_handler_with_additional_kwargs(dummy_response):
    # GIVEN tracer lambda handler decorator is used
    tracer = Tracer(disabled=True)

    # WHEN a lambda handler signature has additional keyword arguments
    @tracer.capture_lambda_handler
    def handler(event, context, my_extra_option=None, **kwargs):
        return dummy_response

    # THEN tracer should not raise an Exception
    handler({}, {}, blah="blah")


def test_capture_method(dummy_response):
    # GIVEN tracer method decorator is used
    tracer = Tracer(disabled=True)

    # WHEN a function is run
    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    # THEN tracer should not raise an Exception
    greeting(name="Foo", message="Bar")


def test_tracer_lambda_emulator(monkeypatch, dummy_response):
    # GIVEN tracer runs locally
    monkeypatch.setenv("AWS_SAM_LOCAL", "true")
    tracer = Tracer()

    # WHEN a lambda function is run through SAM CLI
    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    # THEN tracer should run in disabled mode, and not raise an Exception
    handler({}, {})


def test_tracer_chalice_cli_mode(monkeypatch, dummy_response):
    # GIVEN tracer runs locally
    monkeypatch.setenv("AWS_CHALICE_CLI_MODE", "true")
    tracer = Tracer()

    # WHEN a lambda function is run through the Chalice CLI.
    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    # THEN tracer should run in disabled mode, and not raise an Exception
    handler({}, {})


def test_tracer_metadata_disabled(dummy_response):
    # GIVEN tracer is disabled, and annotations/metadata are used
    tracer = Tracer(disabled=True)

    # WHEN a lambda handler is run
    @tracer.capture_lambda_handler
    def handler(event, context):
        tracer.put_annotation("PaymentStatus", "SUCCESS")
        tracer.put_metadata("PaymentMetadata", "Metadata")
        return dummy_response

    # THEN tracer should not raise any Exception
    handler({}, {})


def test_tracer_service_env_var(monkeypatch, service_name):
    # GIVEN tracer is run without parameters
    # WHEN service is implicitly defined via env var
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)
    tracer = Tracer(disabled=True)

    # THEN tracer should have use that service name
    assert tracer.service == service_name


def test_tracer_explicit_service(monkeypatch, service_name):
    # GIVEN tracer is disabled
    # WHEN service is explicitly defined
    tracer_explicit = Tracer(disabled=True, service=service_name)
    assert tracer_explicit.service == service_name

    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")
    tracer = Tracer()

    # THEN tracer should have use that service name
    assert tracer.service == service_name


def test_tracer_propagate_exception(mocker):
    # GIVEN tracer decorator is used
    class CustomException(Exception):
        pass

    tracer = Tracer(disabled=True)

    # WHEN a lambda handler or method returns an Exception
    @tracer.capture_lambda_handler
    def handler(event, context):
        raise CustomException("test")

    @tracer.capture_method
    def greeting():
        raise CustomException("test")

    # THEN tracer should reraise the same Exception
    with pytest.raises(CustomException):
        handler({}, {})

    with pytest.raises(CustomException):
        greeting()


def test_tracer_reuse_configuration(service_name):
    # GIVEN tracer A is initialized
    tracer_a = Tracer(disabled=True, service=service_name)
    # WHEN tracer B is initialized afterwards
    tracer_b = Tracer()

    # THEN tracer B attributes should be equal to tracer A
    assert tracer_a.__dict__.items() == tracer_b.__dict__.items()


def test_tracer_method_nested_sync(mocker):
    # GIVEN tracer decorator is used
    # WHEN multiple sync functions are nested
    # THEN tracer should not raise a Runtime Error
    tracer = Tracer(disabled=True)

    @tracer.capture_method
    def func_1():
        return 1

    @tracer.capture_method
    def func_2():
        return 2

    @tracer.capture_method
    def sums_values():
        return func_1() + func_2()

    sums_values()


def test_tracer_yield_with_capture():
    # GIVEN tracer method decorator is used
    tracer = Tracer(disabled=True)

    # WHEN capture_method decorator is applied to a context manager
    @tracer.capture_method
    @contextlib.contextmanager
    def yield_with_capture():
        yield "testresult"

    # Or WHEN capture_method decorator is applied to a generator function
    @tracer.capture_method
    def generator_func():
        yield "testresult2"

    @tracer.capture_lambda_handler
    def handler(event, context):
        result = []
        with yield_with_capture() as yielded_value:
            result.append(yielded_value)

        gen = generator_func()

        result.append(next(gen))

        return result

    # THEN no exception is thrown, and the functions properly return values
    result = handler({}, {})
    assert "testresult" in result
    assert "testresult2" in result
