import json

from aws_lambda_powertools.utilities.auth_alpha.jwt.testing import mock_claims


def test_list_orders(monkeypatch):
    monkeypatch.setenv("ISSUER_URL", "https://idp.example.com/")
    monkeypatch.setenv("RESOURCE_URL", "https://api.example.com")

    from middleware import lambda_handler, verifier

    event = {
        "version": "2.0",
        "routeKey": "GET /orders",
        "rawPath": "/orders",
        "rawQueryString": "",
        "headers": {"authorization": "Bearer test-token"},
        "requestContext": {
            "http": {"method": "GET", "path": "/orders"},
            "stage": "$default",
        },
        "isBase64Encoded": False,
    }
    claims = {"sub": "test-user", "scope": "orders:read"}

    with mock_claims(verifier, claims):
        response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"subject": "test-user", "orders": []}
