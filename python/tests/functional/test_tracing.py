import pytest

from aws_lambda_powertools.tracing import Tracer


@pytest.fixture
def dummy_response():
    return {"test": "succeeds"}


@pytest.fixture(scope="function", autouse=True)
def reset_tracing_config():
    Tracer._reset_config()
    yield


def test_capture_lambda_handler(dummy_response):
    # GIVEN tracer is disabled, and decorator is used
    # WHEN a lambda handler is run
    # THEN tracer should not raise an Exception
    tracer = Tracer(disabled=True)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, {})


def test_capture_method(dummy_response):
    # GIVEN tracer is disabled, and method decorator is used
    # WHEN a function is run
    # THEN tracer should not raise an Exception

    tracer = Tracer(disabled=True)

    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")


def test_tracer_lambda_emulator(monkeypatch, dummy_response):
    # GIVEN tracer is run locally
    # WHEN a lambda function is run through SAM CLI
    # THEN tracer should not raise an Exception
    monkeypatch.setenv("AWS_SAM_LOCAL", "true")
    tracer = Tracer()

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, {})
    monkeypatch.delenv("AWS_SAM_LOCAL")


def test_tracer_metadata_disabled(dummy_response):
    # GIVEN tracer is disabled, and annotations/metadata are used
    # WHEN a lambda handler is run
    # THEN tracer should not raise an Exception and simply ignore
    tracer = Tracer(disabled=True)

    @tracer.capture_lambda_handler
    def handler(event, context):
        tracer.put_annotation("PaymentStatus", "SUCCESS")
        tracer.put_metadata("PaymentMetadata", "Metadata")
        return dummy_response

    handler({}, {})


def test_tracer_env_vars(monkeypatch):
    # GIVEN tracer disabled, is run without parameters
    # WHEN service is explicitly defined
    # THEN tracer should have use that service name
    service_name = "booking"
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)
    tracer_env_var = Tracer(disabled=True)

    assert tracer_env_var.service == service_name

    tracer_explicit = Tracer(disabled=True, service=service_name)
    assert tracer_explicit.service == service_name

    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")
    tracer = Tracer()

    assert bool(tracer.disabled) is True


def test_tracer_with_exception(mocker):
    # GIVEN tracer is disabled, decorator is used
    # WHEN a lambda handler or method returns an Exception
    # THEN tracer should reraise the same Exception
    class CustomException(Exception):
        pass

    tracer = Tracer(disabled=True)

    @tracer.capture_lambda_handler
    def handler(event, context):
        raise CustomException("test")

    @tracer.capture_method
    def greeting(name, message):
        raise CustomException("test")

    with pytest.raises(CustomException):
        handler({}, {})

    with pytest.raises(CustomException):
        greeting(name="Foo", message="Bar")


def test_tracer_reuse():
    # GIVEN tracer A, B were initialized
    # WHEN tracer B explicitly reuses A config
    # THEN tracer B attributes should be equal to tracer A
    service_name = "booking"
    tracer_a = Tracer(disabled=True, service=service_name)
    tracer_b = Tracer()

    assert id(tracer_a) != id(tracer_b)
    assert tracer_a.__dict__.items() == tracer_b.__dict__.items()
