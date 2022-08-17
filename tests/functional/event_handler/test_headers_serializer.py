import warnings

from aws_lambda_powertools.shared.headers_serializer import (
    HttpApiSerializer,
    MultiValueHeadersSerializer,
    SingleValueHeadersSerializer,
)


def test_headers_serializer_http_api():
    serializer = HttpApiSerializer()

    payload = serializer.serialize(cookies=[], headers={})
    assert payload == {"cookies": [], "headers": {}}

    payload = serializer.serialize(cookies=[], headers={"Content-Type": "text/html"})
    assert payload == {"cookies": [], "headers": {"Content-Type": "text/html"}}

    payload = serializer.serialize(cookies=["UUID=12345"], headers={})
    assert payload == {"cookies": ["UUID=12345"], "headers": {}}

    payload = serializer.serialize(cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert payload == {"cookies": ["UUID=12345", "SSID=0xdeadbeef"], "headers": {"Foo": "bar,zbr"}}


def test_headers_serializer_multi_value_headers():
    serializer = MultiValueHeadersSerializer()

    payload = serializer.serialize(cookies=[], headers={})
    assert payload == {"multiValueHeaders": {}}

    payload = serializer.serialize(cookies=[], headers={"Content-Type": "text/html"})
    assert payload == {"multiValueHeaders": {"Content-Type": ["text/html"]}}

    payload = serializer.serialize(cookies=["UUID=12345"], headers={})
    assert payload == {"multiValueHeaders": {"Set-Cookie": ["UUID=12345"]}}

    payload = serializer.serialize(cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
    assert payload == {"multiValueHeaders": {"Set-Cookie": ["UUID=12345", "SSID=0xdeadbeef"], "Foo": ["bar,zbr"]}}


def test_headers_serializer_single_value_headers():
    serializer = SingleValueHeadersSerializer()

    payload = serializer.serialize(cookies=[], headers={})
    assert payload == {"headers": {}}

    payload = serializer.serialize(cookies=[], headers={"Content-Type": "text/html"})
    assert payload == {"headers": {"Content-Type": "text/html"}}

    payload = serializer.serialize(cookies=["UUID=12345"], headers={})
    assert payload == {"headers": {"Set-Cookie": "UUID=12345"}}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")

        payload = serializer.serialize(cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": "bar,zbr"})
        assert payload == {"headers": {"Set-Cookie": "SSID=0xdeadbeef", "Foo": "bar,zbr"}}

        assert len(w) == 1
        assert str(w[-1].message) == (
            "Can't encode more than one cookie in the response. "
            "Did you enable multiValueHeaders on the ALB Target Group?"
        )
