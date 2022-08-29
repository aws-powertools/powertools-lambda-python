import pytest
from requests import Request

from tests.e2e.utils import data_fetcher


@pytest.fixture
def alb_basic_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBBasicListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.fixture
def alb_multi_value_header_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBMultiValueHeaderListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.fixture
def apigw_rest_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayRestUrl", "")


@pytest.fixture
def apigw_http_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayHTTPUrl", "")


@pytest.fixture
def lambda_function_url_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("LambdaFunctionUrl", "")


def test_alb_headers_serializer(alb_basic_listener_endpoint):
    # GIVEN
    url = f"{alb_basic_listener_endpoint}/todos"

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert response.headers["content-type"] == "text/plain"

    # Only the last header for key "Foo" should be set
    assert response.headers["Foo"] == "zbr"

    # Only the last cookie should be set
    assert "MonsterCookie" in response.cookies.keys()
    assert "CookieMonster" not in response.cookies.keys()


def test_alb_multi_value_headers_serializer(alb_multi_value_header_listener_endpoint):
    # GIVEN
    url = f"{alb_multi_value_header_listener_endpoint}/todos"

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert response.headers["content-type"] == "text/plain"

    # Only the last header for key "Foo" should be set
    assert "Foo" in response.headers
    foo_headers = [x.strip() for x in response.headers["Foo"].split(",")]
    assert sorted(foo_headers) == ["bar", "zbr"]

    # Only the last cookie should be set
    assert "MonsterCookie" in response.cookies.keys()
    assert "CookieMonster" in response.cookies.keys()


def test_api_gateway_rest_headers_serializer(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}/todos"

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert response.headers["content-type"] == "text/plain"

    # Only the last header for key "Foo" should be set
    assert "Foo" in response.headers
    foo_headers = [x.strip() for x in response.headers["Foo"].split(",")]
    assert sorted(foo_headers) == ["bar", "zbr"]

    # Only the last cookie should be set
    assert "MonsterCookie" in response.cookies.keys()
    assert "CookieMonster" in response.cookies.keys()


def test_api_gateway_http_headers_serializer(apigw_http_endpoint):
    # GIVEN
    url = f"{apigw_http_endpoint}/todos"

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert response.headers["content-type"] == "text/plain"

    # Only the last header for key "Foo" should be set
    assert "Foo" in response.headers
    foo_headers = [x.strip() for x in response.headers["Foo"].split(",")]
    assert sorted(foo_headers) == ["bar", "zbr"]

    # Only the last cookie should be set
    assert "MonsterCookie" in response.cookies.keys()
    assert "CookieMonster" in response.cookies.keys()


def test_lambda_function_url_headers_serializer(lambda_function_url_endpoint):
    # GIVEN
    url = f"{lambda_function_url_endpoint}todos"  # the function url endpoint already has the trailing /

    # WHEN
    response = data_fetcher.get_http_response(Request(method="GET", url=url))

    # THEN
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert response.headers["content-type"] == "text/plain"

    # Only the last header for key "Foo" should be set
    assert "Foo" in response.headers
    foo_headers = [x.strip() for x in response.headers["Foo"].split(",")]
    assert sorted(foo_headers) == ["bar", "zbr"]

    # Only the last cookie should be set
    assert "MonsterCookie" in response.cookies.keys()
    assert "CookieMonster" in response.cookies.keys()
