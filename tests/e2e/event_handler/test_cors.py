import pytest
from requests import Request

from tests.e2e.utils import data_fetcher
from tests.e2e.utils.auth import build_iam_auth


@pytest.fixture
def alb_basic_listener_endpoint(infrastructure: dict) -> str:
    dns_name = infrastructure.get("ALBDnsName")
    port = infrastructure.get("ALBBasicListenerPort", "")
    return f"http://{dns_name}:{port}"


@pytest.fixture
def apigw_http_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayHTTPUrl", "")


@pytest.fixture
def apigw_rest_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayRestUrl", "")


@pytest.fixture
def lambda_function_url_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("LambdaFunctionUrl", "")


@pytest.mark.xdist_group(name="event_handler")
def test_alb_cors_with_correct_origin(alb_basic_listener_endpoint):
    # GIVEN
    url = f"{alb_basic_listener_endpoint}/todos"
    headers = {"Origin": "https://www.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(Request(method="POST", url=url, headers=headers, json={}))

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://www.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_alb_cors_with_correct_alternative_origin(alb_basic_listener_endpoint):
    # GIVEN
    url = f"{alb_basic_listener_endpoint}/todos"
    headers = {"Origin": "https://dev.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(Request(method="POST", url=url, headers=headers, json={}))

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://dev.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_alb_cors_with_unknown_origin(alb_basic_listener_endpoint):
    # GIVEN
    url = f"{alb_basic_listener_endpoint}/todos"
    headers = {"Origin": "https://www.google.com"}

    # WHEN
    response = data_fetcher.get_http_response(Request(method="POST", url=url, headers=headers, json={}))

    # THEN response does NOT have CORS headers
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_http_cors_with_correct_origin(apigw_http_endpoint):
    # GIVEN
    url = f"{apigw_http_endpoint}todos"
    headers = {"Origin": "https://www.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="execute-api"),
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://www.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_http_cors_with_correct_alternative_origin(apigw_http_endpoint):
    # GIVEN
    url = f"{apigw_http_endpoint}todos"
    headers = {"Origin": "https://dev.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="execute-api"),
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://dev.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_http_cors_with_unknown_origin(apigw_http_endpoint):
    # GIVEN
    url = f"{apigw_http_endpoint}todos"
    headers = {"Origin": "https://www.google.com"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="execute-api"),
        ),
    )

    # THEN response does NOT have CORS headers
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_rest_cors_with_correct_origin(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}todos"
    headers = {"Origin": "https://www.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://www.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_rest_cors_with_correct_alternative_origin(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}todos"
    headers = {"Origin": "https://dev.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://dev.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_api_gateway_rest_cors_with_unknown_origin(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}todos"
    headers = {"Origin": "https://www.google.com"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
        ),
    )

    # THEN response does NOT have CORS headers
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.xdist_group(name="event_handler")
def test_lambda_function_url_cors_with_correct_origin(lambda_function_url_endpoint):
    # GIVEN
    url = f"{lambda_function_url_endpoint}todos"
    headers = {"Origin": "https://www.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="lambda"),
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://www.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_lambda_function_url_cors_with_correct_alternative_origin(lambda_function_url_endpoint):
    # GIVEN
    url = f"{lambda_function_url_endpoint}todos"
    headers = {"Origin": "https://dev.example.org"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="lambda"),
        ),
    )

    # THEN response has CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "https://dev.example.org"


@pytest.mark.xdist_group(name="event_handler")
def test_lambda_function_url_cors_with_unknown_origin(lambda_function_url_endpoint):
    # GIVEN
    url = f"{lambda_function_url_endpoint}todos"
    headers = {"Origin": "https://www.google.com"}

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            headers=headers,
            json={},
            auth=build_iam_auth(url=url, aws_service="lambda"),
        ),
    )

    # THEN response does NOT have CORS headers
    assert "Access-Control-Allow-Origin" not in response.headers
