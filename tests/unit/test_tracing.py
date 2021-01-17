import contextlib
import sys
from typing import NamedTuple
from unittest import mock

import pytest

from aws_lambda_powertools import Tracer


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
    class AsyncContextManager(mock.MagicMock):
        async def __aenter__(self, *args, **kwargs):
            return self.__enter__()

        async def __aexit__(self, *args, **kwargs):
            return self.__exit__(*args, **kwargs)

    class InSubsegment(NamedTuple):
        in_subsegment: mock.MagicMock = AsyncContextManager()
        put_annotation: mock.MagicMock = mock.MagicMock()
        put_metadata: mock.MagicMock = mock.MagicMock()

    in_subsegment = InSubsegment()
    in_subsegment.in_subsegment.return_value.__enter__.return_value.put_annotation = in_subsegment.put_annotation
    in_subsegment.in_subsegment.return_value.__enter__.return_value.put_metadata = in_subsegment.put_metadata

    if sys.version_info >= (3, 8):  # 3.8 introduced AsyncMock
        in_subsegment.in_subsegment.return_value.__aenter__.return_value.put_metadata = in_subsegment.put_metadata

    yield in_subsegment


def test_tracer_lambda_handler(mocker, dummy_response, provider_stub, in_subsegment_mock):
    # GIVEN Tracer is initialized with booking as the service name
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN lambda_handler decorator is used
    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, mocker.MagicMock())

    # THEN we should have a subsegment named handler
    # annotate cold start, and add its response as trace metadata
    # and use service name as a metadata namespace
    assert in_subsegment_mock.in_subsegment.call_count == 1
    assert in_subsegment_mock.in_subsegment.call_args == mocker.call(name="## handler")
    assert in_subsegment_mock.put_metadata.call_args == mocker.call(
        key="handler response", value=dummy_response, namespace="booking"
    )
    assert in_subsegment_mock.put_annotation.call_count == 1
    assert in_subsegment_mock.put_annotation.call_args == mocker.call(key="ColdStart", value=True)


def test_tracer_method(mocker, dummy_response, provider_stub, in_subsegment_mock):
    # GIVEN Tracer is initialized with booking as the service name
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used
    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")

    # THEN we should have a subsegment named after the method name
    # and add its response as trace metadata
    # and use service name as a metadata namespace
    assert in_subsegment_mock.in_subsegment.call_count == 1
    assert in_subsegment_mock.in_subsegment.call_args == mocker.call(name="## greeting")
    assert in_subsegment_mock.put_metadata.call_args == mocker.call(
        key="greeting response", value=dummy_response, namespace="booking"
    )


def test_tracer_custom_metadata(mocker, dummy_response, provider_stub):
    # GIVEN Tracer is initialized with booking as the service name
    put_metadata_mock = mocker.MagicMock()
    provider = provider_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN put_metadata is used
    annotation_key = "Booking response"
    annotation_value = {"bookingStatus": "CONFIRMED"}
    tracer.put_metadata(annotation_key, annotation_value)

    # THEN we should have metadata expected and booking as namespace
    assert put_metadata_mock.call_count == 1
    assert put_metadata_mock.call_args_list[0] == mocker.call(
        key=annotation_key, value=annotation_value, namespace="booking"
    )


def test_tracer_custom_annotation(mocker, dummy_response, provider_stub):
    # GIVEN Tracer is initialized
    put_annotation_mock = mocker.MagicMock()
    provider = provider_stub(put_annotation_mock=put_annotation_mock)
    tracer = Tracer(provider=provider)

    # WHEN put_metadata is used
    annotation_key = "BookingId"
    annotation_value = "123456"
    tracer.put_annotation(annotation_key, annotation_value)

    # THEN we should have an annotation as expected
    assert put_annotation_mock.call_count == 1
    assert put_annotation_mock.call_args == mocker.call(key=annotation_key, value=annotation_value)


@mock.patch("aws_lambda_powertools.tracing.Tracer.patch")
def test_tracer_autopatch(patch_mock):
    # GIVEN tracer is initialized
    # WHEN auto_patch hasn't been explicitly disabled
    Tracer(disabled=True)

    # THEN tracer should patch all modules
    assert patch_mock.call_count == 1


@mock.patch("aws_lambda_powertools.tracing.Tracer.patch")
def test_tracer_no_autopatch(patch_mock):
    # GIVEN tracer is initialized
    # WHEN auto_patch is disabled
    Tracer(disabled=True, auto_patch=False)

    # THEN tracer should not patch any module
    assert patch_mock.call_count == 0


def test_tracer_lambda_handler_does_not_add_empty_response_as_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider)

    # WHEN capture_lambda_handler decorator is used
    # and the handler response is empty
    @tracer.capture_lambda_handler
    def handler(event, context):
        return

    handler({}, mocker.MagicMock())

    # THEN we should not add empty metadata
    assert in_subsegment_mock.put_metadata.call_count == 0


def test_tracer_method_does_not_add_empty_response_as_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider)

    # WHEN capture_method decorator is used
    # and the method response is empty
    @tracer.capture_method
    def greeting(name, message):
        return

    greeting(name="Foo", message="Bar")

    # THEN we should not add empty metadata
    assert in_subsegment_mock.put_metadata.call_count == 0


@mock.patch("aws_lambda_powertools.tracing.tracer.aws_xray_sdk.core.patch")
def test_tracer_patch_modules(xray_patch_mock, mocker):
    # GIVEN tracer is initialized with a list of modules to patch
    modules = ["boto3"]

    # WHEN modules are supported by X-Ray
    Tracer(service="booking", patch_modules=modules)

    # THEN tracer should run just fine
    assert xray_patch_mock.call_count == 1
    assert xray_patch_mock.call_args == mocker.call(modules)


def test_tracer_method_exception_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used
    # and the method raises an exception
    @tracer.capture_method
    def greeting(name, message):
        raise ValueError("test")

    with pytest.raises(ValueError):
        greeting(name="Foo", message="Bar")

    # THEN we should add the exception using method name as key plus error
    # and their service name as the namespace
    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "greeting error"
    assert put_metadata_mock_args["namespace"] == "booking"


def test_tracer_lambda_handler_exception_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_lambda_handler decorator is used
    # and the method raises an exception
    @tracer.capture_lambda_handler
    def handler(event, context):
        raise ValueError("test")

    with pytest.raises(ValueError):
        handler({}, mocker.MagicMock())

    # THEN we should add the exception using handler name as key plus error
    # and their service name as the namespace
    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "handler error"

    assert put_metadata_mock_args["namespace"] == "booking"


@pytest.mark.asyncio
async def test_tracer_method_nested_async(mocker, dummy_response, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment_async=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used for nested async methods
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

    # THEN we should add metadata for each response like we would for a sync decorated method
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
    # GIVEN tracer is initialized and explicitly disabled
    tracer = Tracer(service="booking", disabled=True)

    # WHEN capture_method decorator is used
    @tracer.capture_method
    async def greeting_2(name, message):
        return dummy_response

    @tracer.capture_method
    async def greeting(name, message):
        await greeting_2(name, message)
        return dummy_response

    # THEN we should run the decorator methods without side effects
    ret = await greeting(name="Foo", message="Bar")
    assert ret == dummy_response


@pytest.mark.asyncio
async def test_tracer_method_exception_metadata_async(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment_async=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used in an async method
    # and the method raises an exception
    @tracer.capture_method
    async def greeting(name, message):
        raise ValueError("test")

    with pytest.raises(ValueError):
        await greeting(name="Foo", message="Bar")

    # THEN we should add the exception using method name as key plus error
    # and their service name as the namespace
    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "greeting error"
    assert put_metadata_mock_args["namespace"] == "booking"


def test_tracer_yield_from_context_manager(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used on a context manager
    @tracer.capture_method
    @contextlib.contextmanager
    def yield_with_capture():
        yield "test result"

    @tracer.capture_lambda_handler
    def handler(event, context):
        response = []
        with yield_with_capture() as yielded_value:
            response.append(yielded_value)

        return response

    result = handler({}, {})

    # THEN we should have a subsegment named after the method name
    # and add its response as trace metadata
    handler_trace, yield_function_trace = in_subsegment_mock.in_subsegment.call_args_list

    assert "test result" in in_subsegment_mock.put_metadata.call_args[1]["value"]
    assert in_subsegment_mock.in_subsegment.call_count == 2
    assert handler_trace == mocker.call(name="## handler")
    assert yield_function_trace == mocker.call(name="## yield_with_capture")
    assert "test result" in result


def test_tracer_yield_from_context_manager_exception_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used on a context manager
    # and the method raises an exception
    @tracer.capture_method
    @contextlib.contextmanager
    def yield_with_capture():
        yield "partial"
        raise ValueError("test")

    with pytest.raises(ValueError):
        with yield_with_capture() as partial_val:
            assert partial_val == "partial"

    # THEN we should add the exception using method name as key plus error
    # and their service name as the namespace
    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "yield_with_capture error"
    assert isinstance(put_metadata_mock_args["value"], ValueError)
    assert put_metadata_mock_args["namespace"] == "booking"


def test_tracer_yield_from_nested_context_manager(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used on a context manager nesting another context manager
    class NestedContextManager(object):
        def __enter__(self):
            self._value = {"result": "test result"}
            return self._value

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._value["result"] = "exit was called before yielding"

    @tracer.capture_method
    @contextlib.contextmanager
    def yield_with_capture():
        with NestedContextManager() as nested_context:
            yield nested_context

    @tracer.capture_lambda_handler
    def handler(event, context):
        response = []
        with yield_with_capture() as yielded_value:
            response.append(yielded_value["result"])

        return response

    result = handler({}, {})

    # THEN we should have a subsegment named after the method name
    # and add its response as trace metadata
    handler_trace, yield_function_trace = in_subsegment_mock.in_subsegment.call_args_list

    assert "test result" in in_subsegment_mock.put_metadata.call_args[1]["value"]
    assert in_subsegment_mock.in_subsegment.call_count == 2
    assert handler_trace == mocker.call(name="## handler")
    assert yield_function_trace == mocker.call(name="## yield_with_capture")
    assert "test result" in result


def test_tracer_yield_from_generator(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used on a generator function
    @tracer.capture_method
    def generator_fn():
        yield "test result"

    @tracer.capture_lambda_handler
    def handler(event, context):
        gen = generator_fn()
        response = list(gen)

        return response

    result = handler({}, {})

    # THEN we should have a subsegment named after the method name
    # and add its response as trace metadata
    handler_trace, generator_fn_trace = in_subsegment_mock.in_subsegment.call_args_list

    assert "test result" in in_subsegment_mock.put_metadata.call_args[1]["value"]
    assert in_subsegment_mock.in_subsegment.call_count == 2
    assert handler_trace == mocker.call(name="## handler")
    assert generator_fn_trace == mocker.call(name="## generator_fn")
    assert "test result" in result


def test_tracer_yield_from_generator_exception_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, service="booking")

    # WHEN capture_method decorator is used on a generator function
    # and the method raises an exception
    @tracer.capture_method
    def generator_fn():
        yield "partial"
        raise ValueError("test")

    with pytest.raises(ValueError):
        gen = generator_fn()
        list(gen)

    # THEN we should add the exception using method name as key plus error
    # and their service name as the namespace
    put_metadata_mock_args = in_subsegment_mock.put_metadata.call_args[1]
    assert put_metadata_mock_args["key"] == "generator_fn error"
    assert put_metadata_mock_args["namespace"] == "booking"
    assert isinstance(put_metadata_mock_args["value"], ValueError)
    assert str(put_metadata_mock_args["value"]) == "test"


def test_tracer_lambda_handler_override_response_as_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)

    tracer = Tracer(provider=provider, auto_patch=False)

    # WHEN capture_lambda_handler decorator is used with capture_response set to False
    @tracer.capture_lambda_handler(capture_response=False)
    def handler(event, context):
        return "response"

    handler({}, mocker.MagicMock())

    # THEN we should not add any metadata
    assert in_subsegment_mock.put_metadata.call_count == 0


def test_tracer_method_override_response_as_metadata(provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, auto_patch=False)

    # WHEN capture_method decorator is used with capture_response set to False
    @tracer.capture_method(capture_response=False)
    def greeting(name, message):
        return "response"

    greeting(name="Foo", message="Bar")

    # THEN we should not add any metadata
    assert in_subsegment_mock.put_metadata.call_count == 0


def test_tracer_lambda_handler_override_error_as_metadata(mocker, provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, auto_patch=False)

    # WHEN capture_lambda_handler decorator is used with capture_error set to False
    @tracer.capture_lambda_handler(capture_error=False)
    def handler(event, context):
        raise ValueError("error")

    with pytest.raises(ValueError):
        handler({}, mocker.MagicMock())

    # THEN we should not add any metadata
    assert in_subsegment_mock.put_metadata.call_count == 0


def test_tracer_method_override_error_as_metadata(provider_stub, in_subsegment_mock):
    # GIVEN tracer is initialized
    provider = provider_stub(in_subsegment=in_subsegment_mock.in_subsegment)
    tracer = Tracer(provider=provider, auto_patch=False)

    # WHEN capture_method decorator is used with capture_error set to False
    @tracer.capture_method(capture_error=False)
    def greeting(name, message):
        raise ValueError("error")

    with pytest.raises(ValueError):
        greeting(name="Foo", message="Bar")

    # THEN we should not add any metadata
    assert in_subsegment_mock.put_metadata.call_count == 0
