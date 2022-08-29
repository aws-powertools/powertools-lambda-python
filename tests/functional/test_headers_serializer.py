import warnings
from collections import defaultdict
from typing import Dict, List

import pytest

from aws_lambda_powertools.shared.headers_serializer import (
    HttpApiHeadersSerializer,
    MultiValueHeadersSerializer,
    SingleValueHeadersSerializer,
)


@pytest.mark.parametrize(
    "cookies,headers,result",
    [
        ([], {}, {"cookies": [], "headers": {}}),
        ([], {"Content-Type": ["text/html"]}, {"cookies": [], "headers": {"Content-Type": "text/html"}}),
        (["UUID=12345"], {}, {"cookies": ["UUID=12345"], "headers": {}}),
        (
            ["UUID=12345", "SSID=0xdeadbeef"],
            {"Foo": ["bar", "zbr"]},
            {"cookies": ["UUID=12345", "SSID=0xdeadbeef"], "headers": {"Foo": "bar, zbr"}},
        ),
    ],
    ids=["no_cookies", "just_headers", "just_cookies", "multiple_headers_and_cookies"],
)
def test_headers_serializer_http_api(cookies: List[str], headers: Dict[str, List[str]], result: Dict):
    serializer = HttpApiHeadersSerializer()
    payload = serializer.serialize(headers=headers, cookies=cookies)
    assert payload == result


@pytest.mark.parametrize(
    "cookies,headers,result",
    [
        ([], {}, {"multiValueHeaders": defaultdict(list, **{})}),
        (
            [],
            {"Content-Type": ["text/html"]},
            {"multiValueHeaders": defaultdict(list, **{"Content-Type": ["text/html"]})},
        ),
        (["UUID=12345"], {}, {"multiValueHeaders": defaultdict(list, **{"Set-Cookie": ["UUID=12345"]})}),
        (
            ["UUID=12345", "SSID=0xdeadbeef"],
            {"Foo": ["bar", "zbr"]},
            {
                "multiValueHeaders": defaultdict(
                    list, **{"Set-Cookie": ["UUID=12345", "SSID=0xdeadbeef"], "Foo": ["bar", "zbr"]}
                )
            },
        ),
    ],
    ids=["no_cookies", "just_headers", "just_cookies", "multiple_headers_and_cookies"],
)
def test_headers_serializer_multi_value_headers(cookies: List[str], headers: Dict[str, List[str]], result: Dict):
    serializer = MultiValueHeadersSerializer()
    payload = serializer.serialize(headers=headers, cookies=cookies)
    assert payload == result


def single_value_headers_serializer_with_cookies_only():
    content_type = "text/html"
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={"Content-Type": [content_type]}, cookies=[])
    assert payload["headers"]["Content-Type"] == content_type


def single_value_headers_serializer_with_headers_only():
    cookie = "UUID=12345"
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[cookie])
    assert payload["headers"] == {"Set-Cookie": cookie}


def single_value_headers_serializer_with_empty_values():
    serializer = SingleValueHeadersSerializer()
    payload = serializer.serialize(headers={}, cookies=[])
    assert payload == {"headers": {}}


def test_multiple_cookies_with_single_value_headers_serializer():
    serializer = SingleValueHeadersSerializer()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")

        payload = serializer.serialize(cookies=["UUID=12345", "SSID=0xdeadbeef"], headers={"Foo": ["bar", "zbr"]})
        assert payload == {"headers": {"Set-Cookie": "SSID=0xdeadbeef", "Foo": "zbr"}}

        assert len(w) == 2
        assert str(w[-2].message) == (
            "Can't encode more than one cookie in the response. Sending the last cookie only. "
            "Did you enable multiValueHeaders on the ALB Target Group?"
        )
        assert str(w[-1].message) == (
            "Can't encode more than one header value for the same key ('Foo') in the response. "
            "Did you enable multiValueHeaders on the ALB Target Group?"
        )
