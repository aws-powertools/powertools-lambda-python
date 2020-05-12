import sys
from typing import NamedTuple
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
            in_subsegment_async: mocker.MagicMock = None,
            patch_mock: mocker.MagicMock = None,
            disable_tracing_provider_mock: mocker.MagicMock = None,
        ):
            self.put_metadata_mock = put_metadata_mock or mocker.MagicMock()
            self.put_annotation_mock = put_annotation_mock or mocker.MagicMock()
            self.in_subsegment = in_subsegment or mocker.MagicMock()
            self.patch_mock = patch_mock or mocker.MagicMock()
            self.disable_tracing_provider_mock = disable_tracing_provider_mock or mocker.MagicMock()
            self.in_subsegment_async = in_subsegment_async or mocker.MagicMock(spec=True)

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


@pytest.fixture
def in_subsegment_mock():
    class Async_context_manager(mock.MagicMock):
        async def __aenter__(self, *args, **kwargs):
            return self.__enter__()

        async def __aexit__(self, *args, **kwargs):
            return self.__exit__(*args, **kwargs)

    class In_subsegment(NamedTuple):
        in_subsegment: mock.MagicMock = Async_context_manager()
        put_annotation: mock.MagicMock = mock.MagicMock()
        put_metadata: mock.MagicMock = mock.MagicMock()

    in_subsegment = In_subsegment()
    in_subsegment.in_subsegment.return_value.__enter__.return_value.put_annotation = in_subsegment.put_annotation
    in_subsegment.in_subsegment.return_value.__enter__.return_value.put_metadata = in_subsegment.put_metadata

    if sys.version_info >= (3, 8):  # 3.8 introduced AsyncMock
        in_subsegment.in_subsegment.return_value.__aenter__.return_value.put_metadata = in_subsegment.put_metadata

    yield in_subsegment


def test_tracer_lambda_handler(mocker, dummy_response, provider_stub, in_subsegment_mock):
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, mocker.MagicMock())

    assert in_subsegment_mock.in_subsegment.call_count == 1
    assert in_subsegment_mock.in_subsegment.call_args == mocker.call(name="## handler")
    assert in_subsegment_mock.put_metadata.call_args == mocker.call(
        key="lambda handler response", value=dummy_response, namespace="booking"
    )
    assert in_subsegment_mock.put_annotation.call_count == 1
    assert in_subsegment_mock.put_annotation.call_args == mocker.call(key="ColdStart", value=True)


def test_tracer_method(mocker, dummy_response, provider_stub, in_subsegment_mock):
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")

    assert in_subsegment_mock.in_subsegment.call_count == 1
    assert in_subsegment_mock.in_subsegment.call_args == mocker.call(name="## greeting")
    assert in_subsegment_mock.put_metadata.call_args == mocker.call(
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
    Tracer(service="booking", patch_modules=modules)

    assert xray_patch_mock.call_count == 1
    assert xray_patch_mock.call_args == mocker.call(modules)


def test_tracer_method_exception_metadata(mocker, provider_stub, in_subsegment_mock):

    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        raise ValueError("test")

    with pytest.raises(ValueError):
        greeting(name="Foo", message="Bar")

    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "greeting error"
    assert put_metadata_mock_args["namespace"] == "booking"


def test_tracer_lambda_handler_exception_metadata(mocker, provider_stub, in_subsegment_mock):

    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        raise ValueError("test")

    with pytest.raises(ValueError):
        handler({}, mocker.MagicMock())

    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "booking error"
    assert put_metadata_mock_args["namespace"] == "booking"


@pytest.mark.asyncio
async def test_tracer_method_nested_async(mocker, dummy_response, provider_stub, in_subsegment_mock):
    provider = provider_stub(in_subsegment_async=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    async def greeting_2(name, message):
        return dummy_response

    @tracer.capture_method
    async def greeting(name, message):
        await greeting_2(name, message)
        return dummy_response

    await greeting(name="Foo", message="Bar")

    (
        in_subsegment_greeting_call_args,
        in_subsegment_greeting2_call_args,
    ) = in_subsegment_mock.in_subsegment.call_args_list
    put_metadata_greeting2_call_args, put_metadata_greeting_call_args = in_subsegment_mock.put_metadata.call_args_list

    assert in_subsegment_mock.in_subsegment.call_count == 2
    assert in_subsegment_greeting_call_args == mocker.call(name="## greeting")
    assert in_subsegment_greeting2_call_args == mocker.call(name="## greeting_2")

    assert in_subsegment_mock.put_metadata.call_count == 2
    assert put_metadata_greeting2_call_args == mocker.call(
        key="greeting_2 response", value=dummy_response, namespace="booking"
    )
    assert put_metadata_greeting_call_args == mocker.call(
        key="greeting response", value=dummy_response, namespace="booking"
    )


@pytest.mark.asyncio
async def test_tracer_method_nested_async_disabled(dummy_response):

    tracer = Tracer(service="booking", disabled=True)

    @tracer.capture_method
    async def greeting_2(name, message):
        return dummy_response

    @tracer.capture_method
    async def greeting(name, message):
        await greeting_2(name, message)
        return dummy_response

    ret = await greeting(name="Foo", message="Bar")

    assert ret == dummy_response


@pytest.mark.asyncio
async def test_tracer_method_exception_metadata_async(mocker, provider_stub, in_subsegment_mock):
    provider = provider_stub(in_subsegment_async=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    @tracer.capture_method
    async def greeting(name, message):
        raise ValueError("test")

    with pytest.raises(ValueError):
        await greeting(name="Foo", message="Bar")

    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "greeting error"
    assert put_metadata_mock_args["namespace"] == "booking"
