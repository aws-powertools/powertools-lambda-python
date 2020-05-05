from unittest import mock

import pytest

from aws_lambda_powertools.tracing import Tracer


@pytest.fixture
def dummy_response():
    return {"test": "succeeds"}


@pytest.fixture
def provider_stub(mocker):
    class CustomProvider:
        def __init__(
            self,
            put_metadata_mock: mocker.MagicMock = None,
            put_annotation_mock: mocker.MagicMock = None,
            in_subsegment: mocker.MagicMock = None,
            patch_mock: mocker.MagicMock = None,
            disable_tracing_provider_mock: mocker.MagicMock = None,
        ):
            self.put_metadata_mock = put_metadata_mock or mocker.MagicMock()
            self.put_annotation_mock = put_annotation_mock or mocker.MagicMock()
            self.in_subsegment = in_subsegment or mocker.MagicMock()
            self.patch_mock = patch_mock or mocker.MagicMock()
            self.disable_tracing_provider_mock = disable_tracing_provider_mock or mocker.MagicMock()

        def put_metadata(self, *args, **kwargs):
            return self.put_metadata_mock(*args, **kwargs)

        def put_annotation(self, *args, **kwargs):
            return self.put_annotation_mock(*args, **kwargs)

        def in_subsegment(self, *args, **kwargs):
            return self.in_subsegment(*args, **kwargs)

        def patch(self, *args, **kwargs):
            return self.patch_mock(*args, **kwargs)

    return CustomProvider


@pytest.fixture(scope="function", autouse=True)
def reset_tracing_config(mocker):
    Tracer._reset_config()
    # reset global cold start module
    mocker.patch("aws_lambda_powertools.tracing.tracer.is_cold_start", return_value=True)
    yield


def mock_in_subsegment_annotation_metadata():
    """ Mock context manager in_subsegment, and its put_metadata/annotation methods 

    Returns
    -------
    in_subsegment_mock
        in_subsegment_mock mock
    put_annotation_mock
        in_subsegment.put_annotation mock
    put_metadata_mock
        in_subsegment.put_metadata mock
    """
    in_subsegment_mock = mock.MagicMock()
    put_annotation_mock = mock.MagicMock()
    put_metadata_mock = mock.MagicMock()
    in_subsegment_mock.return_value.__enter__.return_value.put_annotation = put_annotation_mock
    in_subsegment_mock.return_value.__enter__.return_value.put_metadata = put_metadata_mock

    return in_subsegment_mock, put_annotation_mock, put_metadata_mock


def test_tracer_lambda_handler(mocker, dummy_response, provider_stub):
    in_subsegment, put_annotation_mock, put_metadata_mock = mock_in_subsegment_annotation_metadata()

    provider = provider_stub(in_subsegment=in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, mocker.MagicMock())

    assert in_subsegment.call_count == 1
    assert in_subsegment.call_args == mocker.call(name="## handler")
    assert put_metadata_mock.call_args == mocker.call(
        key="lambda handler response", value=dummy_response, namespace="booking"
    )
    assert put_annotation_mock.call_count == 1
    assert put_annotation_mock.call_args == mocker.call(key="ColdStart", value=True)


def test_tracer_method(mocker, dummy_response, provider_stub):
    in_subsegment, _, put_metadata_mock = mock_in_subsegment_annotation_metadata()

    provider = provider_stub(in_subsegment=in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")

    assert in_subsegment.call_count == 1
    assert in_subsegment.call_args == mocker.call(name="## greeting")
    assert put_metadata_mock.call_args == mocker.call(
        key="greeting response", value=dummy_response, namespace="booking"
    )


def test_tracer_custom_metadata(mocker, dummy_response, provider_stub):
    put_metadata_mock = mocker.MagicMock()
    annotation_key = "Booking response"
    annotation_value = {"bookingStatus": "CONFIRMED"}
    
    provider = provider_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=provider, service="booking")
    tracer.put_metadata(annotation_key, annotation_value)

    assert put_metadata_mock.call_count == 1
    assert put_metadata_mock.call_args_list[0] == mocker.call(
        key=annotation_key, value=annotation_value, namespace="booking"
    )


def test_tracer_custom_annotation(mocker, dummy_response, provider_stub):
    put_annotation_mock = mocker.MagicMock()
    annotation_key = "BookingId"
    annotation_value = "123456"

    provider = provider_stub(put_annotation_mock=put_annotation_mock)
    tracer = Tracer(provider=provider, service="booking")

    tracer.put_annotation(annotation_key, annotation_value)

    assert put_annotation_mock.call_count == 1
    assert put_annotation_mock.call_args == mocker.call(key=annotation_key, value=annotation_value)


@mock.patch("aws_lambda_powertools.tracing.Tracer.patch")
def test_tracer_autopatch(patch_mock):
    # GIVEN tracer is instantiated
    # WHEN default options were used, or patch() was called
    # THEN tracer should patch all modules
    Tracer(disabled=True)
    assert patch_mock.call_count == 1


@mock.patch("aws_lambda_powertools.tracing.Tracer.patch")
def test_tracer_no_autopatch(patch_mock):
    # GIVEN tracer is instantiated
    # WHEN auto_patch is disabled
    # THEN tracer should not patch any module
    Tracer(disabled=True, auto_patch=False)
    assert patch_mock.call_count == 0


def test_tracer_lambda_handler_empty_response_metadata(mocker, provider_stub):
    put_metadata_mock = mocker.MagicMock()
    provider = provider_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return

    handler({}, mocker.MagicMock())

    assert put_metadata_mock.call_count == 0


def test_tracer_method_empty_response_metadata(mocker, provider_stub):
    put_metadata_mock = mocker.MagicMock()
    provider = provider_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=provider)

    @tracer.capture_method
    def greeting(name, message):
        return

    greeting(name="Foo", message="Bar")

    assert put_metadata_mock.call_count == 0


@mock.patch("aws_lambda_powertools.tracing.tracer.aws_xray_sdk.core.patch")
@mock.patch("aws_lambda_powertools.tracing.tracer.aws_xray_sdk.core.patch_all")
def test_tracer_patch(xray_patch_all_mock, xray_patch_mock, mocker):
    # GIVEN tracer is instantiated
    # WHEN default X-Ray provider client is mocked
    # THEN tracer should run just fine

    Tracer()
    assert xray_patch_all_mock.call_count == 1

    modules = ["boto3"]
    tracer = Tracer(service="booking", patch_modules=modules)

    assert xray_patch_mock.call_count == 1
    assert xray_patch_mock.call_args == mocker.call(modules)


def test_tracer_method_exception_metadata(mocker, provider_stub):
    put_metadata_mock = mocker.MagicMock()

    provider = provider_stub(put_metadata_mock=put_metadata_mock,)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        raise ValueError("test")

    with pytest.raises(ValueError):
        greeting(name="Foo", message="Bar")
        assert put_metadata_mock.call_args == mocker.call(
            key="greeting error", value=ValueError("test"), namespace="booking"
        )


def test_tracer_lambda_handler_exception_metadata(mocker, provider_stub):
    put_metadata_mock = mocker.MagicMock()

    provider = provider_stub(put_metadata_mock=put_metadata_mock,)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        raise ValueError("test")

    with pytest.raises(ValueError):
        handler({}, mocker.MagicMock())
        assert put_metadata_mock.call_args == mocker.call(
            key="booking error", value=ValueError("test"), namespace="booking"
        )
