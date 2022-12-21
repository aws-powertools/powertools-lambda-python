from collections import defaultdict

import pytest

from aws_lambda_powertools.shared.headers_serializer import (
    HttpApiHeadersSerializer,
    MultiValueHeadersSerializer,
    SingleValueHeadersSerializer,
)


def test_http_api_headers_serializer():
    cookies = ["UUID=12345", "SSID=0xdeadbeef"]
    header_values = ["bar", "zbr"]
    headers = {"Foo": header_values}

    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers=headers, cookies=cookies)

    assert payload["cookies"] == cookies
    assert payload["headers"]["Foo"] == ", ".join(header_values)


def test_http_api_headers_serializer_with_empty_values():
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[])
    assert payload == {"headers": {}, "cookies": []}


def test_http_api_headers_serializer_with_headers_only():
    content_type = "text/html"
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": [content_type]}, cookies=[])
    assert payload["headers"]["Content-Type"] == content_type


def test_http_api_headers_serializer_with_single_headers_only():
    content_type = "text/html"
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": content_type}, cookies=[])
    assert payload["headers"]["Content-Type"] == content_type


def test_http_api_headers_serializer_with_cookies_only():
    cookies = ["UUID=12345", "SSID=0xdeadbeef"]
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=cookies)
    assert payload["cookies"] == cookies


def test_multi_value_headers_serializer():
    cookies = ["UUID=12345", "SSID=0xdeadbeef"]
    header_values = ["bar", "zbr"]
    headers = {"Foo": header_values}

    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers=headers, cookies=cookies)

    assert payload["multiValueHeaders"]["Set-Cookie"] == cookies
    assert payload["multiValueHeaders"]["Foo"] == header_values


def test_multi_value_headers_serializer_with_headers_only():
    content_type = "text/html"
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": [content_type]}, cookies=[])
    assert payload["multiValueHeaders"]["Content-Type"] == [content_type]


def test_multi_value_headers_serializer_with_single_headers_only():
    content_type = "text/html"
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": content_type}, cookies=[])
    assert payload["multiValueHeaders"]["Content-Type"] == [content_type]


def test_multi_value_headers_serializer_with_cookies_only():
    cookie = "UUID=12345"
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[cookie])
    assert payload["multiValueHeaders"]["Set-Cookie"] == [cookie]


def test_multi_value_headers_serializer_with_empty_values():
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[])
    assert payload["multiValueHeaders"] == defaultdict(list)


def test_single_value_headers_serializer():
    cookie = "UUID=12345"
    content_type = "text/html"
    headers = {"Content-Type": [content_type]}

    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers=headers, cookies=[cookie])
    assert payload["headers"]["Content-Type"] == content_type
    assert payload["headers"]["Set-Cookie"] == cookie


def test_single_value_headers_serializer_with_headers_only():
    content_type = "text/html"
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": [content_type]}, cookies=[])
    assert payload["headers"]["Content-Type"] == content_type


def test_single_value_headers_serializer_with_single_headers_only():
    content_type = "text/html"
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": content_type}, cookies=[])
    assert payload["headers"]["Content-Type"] == content_type


def test_single_value_headers_serializer_with_cookies_only():
    cookie = "UUID=12345"
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[cookie])
    assert payload["headers"] == {"Set-Cookie": cookie}


def test_single_value_headers_serializer_with_empty_values():
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[])
    assert payload["headers"] == {}


def test_single_value_headers_with_multiple_cookies_warning():
    cookies = ["UUID=12345", "SSID=0xdeadbeef"]
    warning_message = "Can't encode more than one cookie in the response. Sending the last cookie only."
    serializer = SingleValueHeadersSerializer()

    with pytest.warns(match=warning_message):
        payload = serializer.serialize(cookies=cookies, headers={})

    assert payload["headers"]["Set-Cookie"] == cookies[-1]


def test_single_value_headers_with_multiple_header_values_warning():
    headers = {"Foo": ["bar", "zbr"]}
    warning_message = "Can't encode more than one header value for the same key."
    serializer = SingleValueHeadersSerializer()

    with pytest.warns(match=warning_message):
        payload = serializer.serialize(cookies=[], headers=headers)

    assert payload["headers"]["Foo"] == headers["Foo"][-1]


def test_http_api_headers_serializer_with_null_values():
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers={"Foo": None}, cookies=[])
    assert payload == {"headers": {}, "cookies": []}


def test_multi_value_headers_serializer_with_null_values():
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers={"Foo": None}, cookies=[])
    assert payload == {"multiValueHeaders": {}}


def test_single_value_headers_serializer_with_null_values():
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={"Foo": None}, cookies=[])
    assert payload["headers"] == {}
