import warnings

from aws_lambda_powertools.event_handler.headers_serializer import HeadersSerializer
from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    LambdaFunctionUrlEvent,
)
from tests.utils import load_event


def test_headers_serializer_apigatewayv2():
    event = APIGatewayProxyEventV2(load_event("apiGatewayProxyV2Event.json"))

    builder = HeadersSerializer(event=event, cookies=[], headers={})
    assert builder.serialize() == {"cookies": [], "headers": {}}

    builder = HeadersSerializer(event=event, cookies=[], headers={"Content-Type": "text/html"})
    assert builder.serialize() == {"cookies": [], "headers": {"Content-Type": "text/html"}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345"], headers={})
    assert builder.serialize() == {"cookies": ["UUID=12345"], "headers": {}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert builder.serialize() == {"cookies": ["UUID=12345", "SSID=0xdeadbeef"], "headers": {"Foo": "bar,zbr"}}


def test_headers_serializer_lambdafunctionurl():
    event = LambdaFunctionUrlEvent(load_event("lambdaFunctionUrlEvent.json"))

    builder = HeadersSerializer(event=event, cookies=[], headers={})
    assert builder.serialize() == {"cookies": [], "headers": {}}

    builder = HeadersSerializer(event=event, cookies=[], headers={"Content-Type": "text/html"})
    assert builder.serialize() == {"cookies": [], "headers": {"Content-Type": "text/html"}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345"], headers={})
    assert builder.serialize() == {"cookies": ["UUID=12345"], "headers": {}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert builder.serialize() == {"cookies": ["UUID=12345", "SSID=0xdeadbeef"], "headers": {"Foo": "bar,zbr"}}


def test_headers_serializer_apigateway():
    event = APIGatewayProxyEvent(load_event("apiGatewayProxyEvent.json"))

    builder = HeadersSerializer(event=event, cookies=[], headers={})
    assert builder.serialize() == {"multiValueHeaders": {}}

    builder = HeadersSerializer(event=event, cookies=[], headers={"Content-Type": "text/html"})
    assert builder.serialize() == {"multiValueHeaders": {"Content-Type": ["text/html"]}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345"], headers={})
    assert builder.serialize() == {"multiValueHeaders": {"Set-Cookie": ["UUID=12345"]}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert builder.serialize() == {
        "multiValueHeaders": {"Set-Cookie": ["UUID=12345", "SSID=0xdeadbeef"], "Foo": ["bar", "zbr"]}
    }


def test_headers_serializer_alb_without_multi_headers_noop():
    event = ALBEvent(load_event("albEvent.json"))

    builder = HeadersSerializer(event=event, cookies=[], headers={})
    assert builder.serialize() == {"headers": {}}

    builder = HeadersSerializer(event=event, cookies=[], headers={"Content-Type": "text/html"})
    assert builder.serialize() == {"headers": {"Content-Type": "text/html"}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345"], headers={})
    assert builder.serialize() == {"headers": {"Set-Cookie": "UUID=12345"}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        assert builder.serialize() == {"headers": {"Set-Cookie": "SSID=0xdeadbeef", "Foo": "zbr"}}

        assert len(w) == 2
        assert str(w[-2].message) == (
            "Can't encode more than one cookie in the response. "
            "Did you enable multiValueHeaders on the ALB Target Group?"
        )
        assert str(w[-1].message) == (
            "Can't encode more than on header with the same key in the response. "
            "Did you enable multiValueHeaders on the ALB Target Group?"
        )


def test_headers_serializer_alb_with_multi_headers_noop():
    event = ALBEvent(load_event("albMultiValueHeadersEvent.json"))

    builder = HeadersSerializer(event=event, cookies=[], headers={})
    assert builder.serialize() == {"multiValueHeaders": {}}

    builder = HeadersSerializer(event=event, cookies=[], headers={"Content-Type": "text/html"})
    assert builder.serialize() == {"multiValueHeaders": {"Content-Type": ["text/html"]}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345"], headers={})
    assert builder.serialize() == {"multiValueHeaders": {"Set-Cookie": ["UUID=12345"]}}

    builder = HeadersSerializer(event=event, cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert builder.serialize() == {
        "multiValueHeaders": {"Set-Cookie": ["UUID=12345", "SSID=0xdeadbeef"], "Foo": ["bar", "zbr"]}
    }
