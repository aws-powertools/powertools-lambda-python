import pytest

from aws_lambda_powertools.tracing import Tracer


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
        ):
            self.put_metadata_mock = put_metadata_mock or mocker.MagicMock()
            self.put_annotation_mock = put_annotation_mock or mocker.MagicMock()
            self.begin_subsegment_mock = begin_subsegment_mock or mocker.MagicMock()
            self.end_subsegment_mock = end_subsegment_mock or mocker.MagicMock()

        def put_metadata(self, *args, **kwargs):
            return self.put_metadata_mock(*args, **kwargs)

        def put_annotation(self, *args, **kwargs):
            return self.put_annotation_mock(*args, **kwargs)

        def begin_subsegment(self, *args, **kwargs):
            return self.begin_subsegment_mock(*args, **kwargs)

        def end_subsegment(self, *args, **kwargs):
            return self.end_subsegment_mock(*args, **kwargs)

    return XRayStub


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

    xray_provider = xray_stub(put_metadata_mock, put_annotation_mock, begin_subsegment_mock, end_subsegment_mock)
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
