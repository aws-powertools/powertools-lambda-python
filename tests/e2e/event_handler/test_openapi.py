from __future__ import annotations

import pytest
from requests import Request

from tests.e2e.utils import data_fetcher


@pytest.fixture
def apigw_rest_endpoint(infrastructure: dict) -> str:
    return infrastructure.get("APIGatewayRestUrl", "")


@pytest.mark.xdist_group(name="event_handler")
def test_get_openapi_schema(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}openapi_schema"

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="GET",
            url=url,
        ),
    )

    assert "Powertools e2e API" in response.text
    assert "x-amazon-apigateway-gateway-responses" in response.text
    assert response.status_code == 200


def test_get_openapi_schema_with_pep563(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}openapi_schema_with_pep563"

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="GET",
            url=url,
        ),
    )

    assert "Powertools e2e API" in response.text
    assert "x-amazon-apigateway-gateway-responses" in response.text
    assert response.status_code == 200


def test_get_openapi_validation_and_middleware(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}data_validation_middleware"

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="GET",
            url=url,
        ),
    )

    assert response.status_code == 202


def test_openapi_with_fields_discriminator(apigw_rest_endpoint):
    # GIVEN
    url = f"{apigw_rest_endpoint}data_validation_with_fields"

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=url,
            json={"action": "foo", "foo_data": "foo data working"},
        ),
    )

    assert "Powertools e2e API" in response.text
    assert response.status_code == 200
