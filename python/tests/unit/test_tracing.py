from unittest import mock

import pytest

from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.tracing.base import TracerProvider


@pytest.fixture
def dummy_response():
    return {"test": "succeeds"}


@pytest.fixture
def xray_stub(mocker):
    class XRayStub:
        def __init__(
            self,
            put_metadata_mock: mocker.MagicMock = None,
            put_annotation_mock: mocker.MagicMock = None,
            begin_subsegment_mock: mocker.MagicMock = None,
            end_subsegment_mock: mocker.MagicMock = None,
            patch_mock: mocker.MagicMock = None,
            disable_tracing_provider_mock: mocker.MagicMock = None,
        ):
            self.put_metadata_mock = put_metadata_mock or mocker.MagicMock()
            self.put_annotation_mock = put_annotation_mock or mocker.MagicMock()
            self.begin_subsegment_mock = begin_subsegment_mock or mocker.MagicMock()
            self.end_subsegment_mock = end_subsegment_mock or mocker.MagicMock()
            self.patch_mock = patch_mock or mocker.MagicMock()
            self.disable_tracing_provider_mock = disable_tracing_provider_mock or mocker.MagicMock()

        def put_metadata(self, *args, **kwargs):
            return self.put_metadata_mock(*args, **kwargs)

        def put_annotation(self, *args, **kwargs):
            return self.put_annotation_mock(*args, **kwargs)

        def begin_subsegment(self, *args, **kwargs):
            return self.begin_subsegment_mock(*args, **kwargs)

        def end_subsegment(self, *args, **kwargs):
            return self.end_subsegment_mock(*args, **kwargs)

        def patch(self, *args, **kwargs):
            return self.patch_mock(*args, **kwargs)

        def disable_tracing_provider(self):
            self.disable_tracing_provider_mock()

    return XRayStub


@pytest.fixture(scope="function", autouse=True)
def reset_tracing_config():
    Tracer._reset_config()
    yield


@pytest.fixture
def tracer_provider_stub(mocker):
    class CustomTracerProvider(TracerProvider):
        def create_subsegment(self, name):
            pass

        def end_subsegment(self, name=None):
            pass

        def patch(self):
            pass

        def put_annotation(self, key, value):
            pass

        def put_metadata(self, key, value, namespace=None):
            pass

        def disable_tracing_provider(self):
            pass

    return CustomTracerProvider


def test_tracer_lambda_handler(mocker, dummy_response, xray_stub):
    put_metadata_mock = mocker.MagicMock()
    begin_subsegment_mock = mocker.MagicMock()
    end_subsegment_mock = mocker.MagicMock()

    xray_provider = xray_stub(
        put_metadata_mock=put_metadata_mock,
        begin_subsegment_mock=begin_subsegment_mock,
        end_subsegment_mock=end_subsegment_mock,
    )
    tracer = Tracer(provider=xray_provider, service="booking")

    @tracer.capture_lambda_handler
    def handler(event, context):
        return dummy_response

    handler({}, mocker.MagicMock())

    assert begin_subsegment_mock.call_count == 1
    assert begin_subsegment_mock.call_args == mocker.call(name="## handler")
    assert end_subsegment_mock.call_count == 1
    assert put_metadata_mock.call_args == mocker.call(
        key="lambda handler response", value=dummy_response, namespace="booking"
    )


def test_tracer_method(mocker, dummy_response, xray_stub):
    put_metadata_mock = mocker.MagicMock()
    put_annotation_mock = mocker.MagicMock()
    begin_subsegment_mock = mocker.MagicMock()
    end_subsegment_mock = mocker.MagicMock()

    xray_provider = xray_stub(
        put_metadata_mock=put_metadata_mock,
        put_annotation_mock=put_annotation_mock,
        begin_subsegment_mock=begin_subsegment_mock,
        end_subsegment_mock=end_subsegment_mock,
    )
    tracer = Tracer(provider=xray_provider, service="booking")

    @tracer.capture_method
    def greeting(name, message):
        return dummy_response

    greeting(name="Foo", message="Bar")

    assert begin_subsegment_mock.call_count == 1
    assert begin_subsegment_mock.call_args == mocker.call(name="## greeting")
    assert end_subsegment_mock.call_count == 1
    assert put_metadata_mock.call_args == mocker.call(
        key="greeting response", value=dummy_response, namespace="booking"
    )


def test_tracer_custom_metadata(mocker, dummy_response, xray_stub):
    put_metadata_mock = mocker.MagicMock()

    xray_provider = xray_stub(put_metadata_mock=put_metadata_mock)

    tracer = Tracer(provider=xray_provider, service="booking")
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


def test_tracer_custom_annotation(mocker, dummy_response, xray_stub):
    put_annotation_mock = mocker.MagicMock()

    xray_provider = xray_stub(put_annotation_mock=put_annotation_mock)

    tracer = Tracer(provider=xray_provider, service="booking")
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


def test_tracer_lambda_handler_empty_response_metadata(mocker, xray_stub):
    put_metadata_mock = mocker.MagicMock()
    xray_provider = xray_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=xray_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return

    handler({}, mocker.MagicMock())

    assert put_metadata_mock.call_count == 0


def test_tracer_method_empty_response_metadata(mocker, xray_stub):
    put_metadata_mock = mocker.MagicMock()
    xray_provider = xray_stub(put_metadata_mock=put_metadata_mock)
    tracer = Tracer(provider=xray_provider)

    @tracer.capture_method
    def greeting(name, message):
        return

    greeting(name="Foo", message="Bar")

    assert put_metadata_mock.call_count == 0


def test_trace_provider_abc_init(mocker, xray_stub):
    # GIVEN tracer is instantiated
    # WHEN a custom provider that implements TracerProvider methods
    # THEN it should run successfully
    class XrayTracer(TracerProvider):
        def create_subsegment(self, name):
            pass

        def end_subsegment(self, name=None):
            pass

        def patch(self):
            pass

        def put_annotation(self, key, value):
            pass

        def put_metadata(self, key, value, namespace=None):
            pass

        def disable_tracing_provider(self):
            pass

    with mock.patch.object(Tracer, "patch") as patch_mock:
        tracer = Tracer(service="booking", provider=XrayTracer)
        tracer2 = Tracer(auto_patch=False)
        assert patch_mock.call_count == 1
        assert tracer.service == "booking"
        assert tracer2.service == "booking"  # inherited from tracer1
        assert tracer2.auto_patch == False  # overriden in tracer2


# def test_trace_provider_abc_decorators(mocker, dummy_response, xray_stub):
#     # GIVEN tracer is instantiated
#     # WHEN a new tracer provider implements TracerProvider methods
#     # THEN it should inherit default decorators
#     class XrayTracer(TracerProvider):

#         def create_subsegment(self, name):
#             pass

#         def end_subsegment(self, name=None):
#             pass

#         def patch(self):
#             pass

#         def put_annotation(self, key, value):
#             pass

#         def put_metadata(self, key, value, namespace=None):
#                 pass

#     put_metadata_mock = mocker.MagicMock()
#     put_annotation_mock = mocker.MagicMock()
#     begin_subsegment_mock = mocker.MagicMock()
#     end_subsegment_mock = mocker.MagicMock()

#     xray_provider = xray_stub(
#         put_metadata_mock=put_metadata_mock,
#         put_annotation_mock=put_annotation_mock,
#         begin_subsegment_mock=begin_subsegment_mock,
#         end_subsegment_mock=end_subsegment_mock,
#     )

#     tracer = XrayTracer(provider=xray_provider, service="booking")
#     annotation_key = "BookingId"
#     annotation_value = "123456"

#     @tracer.capture_lambda_handler
#     def handler(event, context):
#         tracer.put_metadata(annotation_key, annotation_value)
#         return dummy_response

#     handler({}, mocker.MagicMock())

#     # It's 0 because it's calling base class method
#     # and base class provider is different from ours
#     # base class is calling ours methods though

#     # TODO - Create X-Ray Tracer class, and implement decorators there
#     # TODO - Leave only docstring for Trace Provider
#     # TODO - Update tests
#     # FIXME - Create provider abc only, reuse Tracer class, optionally initialize

#     assert put_metadata_mock.call_count == 2
#     assert put_metadata_mock.call_args_list[0] == mocker.call(
#         key=annotation_key, value=annotation_value, namespace="booking"
#     )

# @tracer.capture_method
# def greeting(name, message):
#     return dummy_response

# greeting(name="Foo", message="Bar")

# assert begin_subsegment_mock.call_count == 1
# assert begin_subsegment_mock.call_args == mocker.call(name="## greeting")
# assert end_subsegment_mock.call_count == 1
# assert put_metadata_mock.call_args == mocker.call(
#     key="greeting response", value=dummy_response, namespace="booking"
# )
