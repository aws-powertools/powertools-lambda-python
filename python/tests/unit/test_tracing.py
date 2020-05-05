from unittest import mock

import pytest

from aws_lambda_powertools.tracing import Tracer


@pytest.fixture
def dummy_response():
    return {"test": "succeeds"}


@pytest.fixture
def provider_stub(mocker):
    class CustomProvider():
        def __init__(
            self,
            put_metadata_mock: mocker.MagicMock = None,
            put_annotation_mock: mocker.MagicMock = None,
            begin_subsegment: mocker.MagicMock = None,
            end_subsegment_mock: mocker.MagicMock = None,
            patch_mock: mocker.MagicMock = None,
            disable_tracing_provider_mock: mocker.MagicMock = None,
        ):
            self.put_metadata_mock = put_metadata_mock or mocker.MagicMock()
            self.put_annotation_mock = put_annotation_mock or mocker.MagicMock()
            self.begin_subsegment = begin_subsegment or mocker.MagicMock()
            self.end_subsegment_mock = end_subsegment_mock or mocker.MagicMock()
            self.patch_mock = patch_mock or mocker.MagicMock()
            self.disable_tracing_provider_mock = disable_tracing_provider_mock or mocker.MagicMock()

        def put_metadata(self, *args, **kwargs):
            return self.put_metadata_mock(*args, **kwargs)

        def put_annotation(self, *args, **kwargs):
            return self.put_annotation_mock(*args, **kwargs)

        def create_subsegment(self, *args, **kwargs):
            return self.begin_subsegment(*args, **kwargs)

        def end_subsegment(self, *args, **kwargs):
            return self.end_subsegment_mock(*args, **kwargs)

        def patch(self, *args, **kwargs):
            return self.patch_mock(*args, **kwargs)

    return CustomProvider


@pytest.fixture(scope="function", autouse=True)
def reset_tracing_config(mocker):
    Tracer._reset_config()
    # reset global cold start module
    mocker.patch("aws_lambda_powertools.tracing.tracer.is_cold_start", return_value=True)
    yield


def test_tracer_lambda_handler(mocker, dummy_response, provider_stub):
    put_metadata_mock = mocker.MagicMock()
    begin_subsegment = mocker.MagicMock()
    end_subsegment_mock = mocker.MagicMock()

    provider = provider_stub(
        put_metadata_mock=put_metadata_mock,
        begin_subsegment=begin_subsegment,
        end_subsegment_mock=end_subsegment_mock,
    )
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, mocker.MagicMock())

    assert begin_subsegment.call_count == 1
    assert begin_subsegment.call_args == mocker.call(name="## handler")
    assert end_subsegment_mock.call_count == 1
    assert put_metadata_mock.call_args == mocker.call(
        key="lambda handler response", value=dummy_response, namespace="booking"
    )


def test_tracer_method(mocker, dummy_response, provider_stub):
    put_metadata_mock = mocker.MagicMock()
    put_annotation_mock = mocker.MagicMock()
    begin_subsegment = mocker.MagicMock()
    end_subsegment_mock = mocker.MagicMock()

    provider = provider_stub(
        put_metadata_mock=put_metadata_mock,
        put_annotation_mock=put_annotation_mock,
        begin_subsegment=begin_subsegment,
        end_subsegment_mock=end_subsegment_mock,
    )
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")

    assert begin_subsegment.call_count == 1
    assert begin_subsegment.call_args == mocker.call(name="## greeting")
    assert end_subsegment_mock.call_count == 1
    assert put_metadata_mock.call_args == mocker.call(
        key="greeting response", value=dummy_response, namespace="booking"
    )


def test_tracer_custom_metadata(mocker, dummy_response, provider_stub):
    put_metadata_mock = mocker.MagicMock()

    provider = provider_stub(put_metadata_mock=put_metadata_mock)

    tracer = Tracer(provider=provider, service="booking")
    annotation_key = "Booking response"
    annotation_value = {"bookingStatus": "CONFIRMED"}

    @tracer.capture_lambda_handler
    def handler(event, context):
        tracer.put_metadata(annotation_key, annotation_value)
        return dummy_response

    handler({}, mocker.MagicMock())

    assert put_metadata_mock.call_count == 2
    assert put_metadata_mock.call_args_list[0] == mocker.call(
        key=annotation_key, value=annotation_value, namespace="booking"
    )


def test_tracer_custom_annotation(mocker, dummy_response, provider_stub):
    put_annotation_mock = mocker.MagicMock()

    provider = provider_stub(put_annotation_mock=put_annotation_mock)

    tracer = Tracer(provider=provider, service="booking")
    annotation_key = "BookingId"
    annotation_value = "123456"

    @tracer.capture_lambda_handler
    def handler(event, context):
        tracer.put_annotation(annotation_key, annotation_value)
        return dummy_response

    handler({}, mocker.MagicMock())

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

def test_tracer_xray_provider_cold_start(mocker, provider_stub):
    # GIVEN tracer is instantiated
    # WHEN multiple subsegments are created
    # THEN tracer should record cold start only once
    begin_subsegment_mock = mock.MagicMock()
    begin_subsegment_mock.put_annotation = mock.MagicMock()

    provider = provider_stub(
        begin_subsegment=begin_subsegment_mock,
    )
    tracer = Tracer(provider=provider)

    subsegment_mock = tracer.create_subsegment("test subsegment")
    subsegment_mock = tracer.create_subsegment("test subsegment 2")

    assert subsegment_mock.put_annotation.call_count == 1
    assert subsegment_mock.put_annotation.call_args == mocker.call(key="ColdStart", value=True)
