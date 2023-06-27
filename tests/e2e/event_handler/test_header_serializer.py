from uuid import uuid4

import pytest
from requests import Request

from aws_lambda_powertools.shared.cookies import Cookie
from tests.e2e.utils import data_fetcher
from tests.e2e.utils.auth import build_iam_auth


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


@pytest.mark.xdist_group(name="event_handler")
def test_alb_headers_serializer(alb_basic_listener_endpoint):
    # GIVEN
    url = f"{alb_basic_listener_endpoint}/todos"
    body = "Hello World"
    status_code = 200
    headers = {"Content-Type": "text/plain", "Vary": ["Accept-Encoding", "User-Agent"]}
    cookies = [
        Cookie(name="session_id", value=str(uuid4()), secure=True, http_only=True),
        Cookie(name="ab_experiment", value="3"),
    ]
    last_cookie = cookies[-1]

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body, "status_code": status_code, "headers": headers, "cookies": list(map(str, cookies))},
        ),
    )

    # THEN
    assert response.status_code == status_code
    # response.content is a binary string, needs to be decoded to compare with the real string
    assert response.content.decode("ascii") == body

    # Only the last header should be set
    for key, value in headers.items():
        assert key in response.headers
        new_value = value if isinstance(value, str) else sorted(value)[-1]
        assert response.headers[key] == new_value

    # Only the last cookie should be set
    assert len(response.cookies.items()) == 1
    assert last_cookie.name in response.cookies
    assert response.cookies.get(last_cookie.name) == last_cookie.value


@pytest.mark.xdist_group(name="event_handler")
def test_alb_multi_value_headers_serializer(alb_multi_value_header_listener_endpoint):
    # GIVEN
    url = f"{alb_multi_value_header_listener_endpoint}/todos"
    body = "Hello World"
    status_code = 200
    headers = {"Content-Type": "text/plain", "Vary": ["Accept-Encoding", "User-Agent"]}
    cookies = [
        Cookie(name="session_id", value=str(uuid4()), secure=True, http_only=True),
        Cookie(name="ab_experiment", value="3"),
    ]

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body, "status_code": status_code, "headers": headers, "cookies": list(map(str, cookies))},
        ),
    )

    # THEN
    assert response.status_code == status_code
    # response.content is a binary string, needs to be decoded to compare with the real string
    assert response.content.decode("ascii") == body

    for key, value in headers.items():
        assert key in response.headers
        new_value = value if isinstance(value, str) else ", ".join(sorted(value))

        # ALB sorts the header values randomly, so we have to re-order them for comparison here
        returned_value = ", ".join(sorted(response.headers[key].split(", ")))
        assert returned_value == new_value

    for cookie in cookies:
        assert cookie.name in response.cookies
        assert response.cookies.get(cookie.name) == cookie.value


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_rest_headers_serializer(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}todos"
    body = "Hello World"
    status_code = 200
    headers = {"Content-Type": "text/plain", "Vary": ["Accept-Encoding", "User-Agent"]}
    cookies = [
        Cookie(name="session_id", value=str(uuid4()), secure=True, http_only=True),
        Cookie(name="ab_experiment", value="3"),
    ]

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body, "status_code": status_code, "headers": headers, "cookies": list(map(str, cookies))},
        ),
    )

    # THEN
    assert response.status_code == status_code
    # response.content is a binary string, needs to be decoded to compare with the real string
    assert response.content.decode("ascii") == body

    for key, value in headers.items():
        assert key in response.headers
        new_value = value if isinstance(value, str) else ", ".join(sorted(value))
        assert response.headers[key] == new_value

    for cookie in cookies:
        assert cookie.name in response.cookies
        assert response.cookies.get(cookie.name) == cookie.value


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_http_headers_serializer(apigw_http_endpoint):
    # GIVEN
    url = f"{apigw_http_endpoint}todos"
    body = "Hello World"
    status_code = 200
    headers = {"Content-Type": "text/plain", "Vary": ["Accept-Encoding", "User-Agent"]}
    cookies = [
        Cookie(name="session_id", value=str(uuid4()), secure=True, http_only=True),
        Cookie(name="ab_experiment", value="3"),
    ]

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body, "status_code": status_code, "headers": headers, "cookies": list(map(str, cookies))},
            auth=build_iam_auth(url=url, aws_service="execute-api"),
        ),
    )

    # THEN
    assert response.status_code == status_code
    # response.content is a binary string, needs to be decoded to compare with the real string
    assert response.content.decode("ascii") == body

    for key, value in headers.items():
        assert key in response.headers
        new_value = value if isinstance(value, str) else ", ".join(sorted(value))
        assert response.headers[key] == new_value

    for cookie in cookies:
        assert cookie.name in response.cookies
        assert response.cookies.get(cookie.name) == cookie.value


@pytest.mark.xdist_group(name="event_handler")
def test_lambda_function_url_headers_serializer(lambda_function_url_endpoint):
    # GIVEN
    url = f"{lambda_function_url_endpoint}todos"  # the function url endpoint already has the trailing /
    body = "Hello World"
    status_code = 200
    headers = {"Content-Type": "text/plain", "Vary": ["Accept-Encoding", "User-Agent"]}
    cookies = [
        Cookie(name="session_id", value=str(uuid4()), secure=True, http_only=True),
        Cookie(name="ab_experiment", value="3"),
    ]

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"body": body, "status_code": status_code, "headers": headers, "cookies": list(map(str, cookies))},
            auth=build_iam_auth(url=url, aws_service="lambda"),
        ),
    )

    # THEN
    assert response.status_code == status_code
    # response.content is a binary string, needs to be decoded to compare with the real string
    assert response.content.decode("ascii") == body

    for key, value in headers.items():
        assert key in response.headers
        new_value = value if isinstance(value, str) else ", ".join(sorted(value))
        assert response.headers[key] == new_value

    for cookie in cookies:
        assert cookie.name in response.cookies
        assert response.cookies.get(cookie.name) == cookie.value
