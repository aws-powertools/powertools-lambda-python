import base64
import json
import runpy
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import urllib3

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import DownstreamRequestError, TokenExchangeError

EXAMPLES = Path(__file__).parents[1] / "src"


@pytest.fixture
def deployment(monkeypatch, mocker):
    for name, value in {
        "TOKEN_URL": "https://idp.example.com/token",
        "CLIENT_ID": "orders",
        "CLIENT_SECRET": "test-secret",
        "CLIENT_SECRET_NAME": "orders/oauth-secret",
        "INVENTORY_URL": "https://inventory.example.com",
    }.items():
        monkeypatch.setenv(name, value)
    for name in ("SCOPES", "AUDIENCE", "RESOURCE"):
        monkeypatch.delenv(name, raising=False)
    provider = mocker.patch("aws_lambda_powertools.utilities.parameters.SecretsProvider")
    provider.return_value.get.return_value = "test-secret"
    return provider


@pytest.mark.parametrize("filename", ["client_credentials.py", "client_secret_post.py", "headers.py", "diagnostics.py"])
@pytest.mark.parametrize(
    "configuration",
    [
        {},
        {"SCOPES": "inventory/read"},
        {"SCOPES": "inventory:read inventory:write", "AUDIENCE": "inventory-api"},
        {"SCOPES": "https://graph.microsoft.com/.default"},
        {"SCOPES": "inventory:read", "RESOURCE": "urn:example:inventory"},
    ],
    ids=["no-scopes", "cognito-scopes", "auth0-audience", "entra-default-scope", "resource-uri"],
)
def test_examples_send_the_configured_scopes_and_resource(deployment, monkeypatch, filename, configuration):
    for name, value in configuration.items():
        monkeypatch.setenv(name, value)
    calls = []
    expected_fields = {"grant_type": ["client_credentials"]}
    for variable, field in (("SCOPES", "scope"), ("AUDIENCE", "audience"), ("RESOURCE", "resource")):
        if variable in configuration:
            expected_fields[field] = [configuration[variable]]

    def request(self, method, url, **options):
        calls.append((method, url))
        if url == "https://idp.example.com/token":
            assert method == "POST"
            assert options["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
            fields = parse_qs(options["body"].decode())
            if filename == "client_secret_post.py":
                assert "Authorization" not in options["headers"]
                assert fields.pop("client_id") == ["orders"]
                assert fields.pop("client_secret") == ["test-secret"]
            else:
                basic = options["headers"]["Authorization"].removeprefix("Basic ")
                assert base64.b64decode(basic).decode() == "orders:test-secret"
            assert fields == expected_fields
            return urllib3.HTTPResponse(
                body=BytesIO(b'{"access_token":"test-token","token_type":"Bearer","expires_in":600}'),
                status=200,
                preload_content=False,
            )
        assert method == "GET"
        suffix = "" if filename == "client_secret_post.py" else "/stock/item%2F123"
        assert url == f"https://inventory.example.com{suffix}"
        assert options["headers"] == {"Authorization": "Bearer test-token"}
        assert "test-secret" not in str(options)
        return urllib3.HTTPResponse(body=BytesIO(b'{"stock":12}'), status=200, preload_content=False)

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    example = runpy.run_path(str(EXAMPLES / filename))
    assert calls == []

    for _ in range(2):
        response = example["lambda_handler"]({"sku": "item/123"}, {})
        if filename == "diagnostics.py":
            assert response["statusCode"] == 200
            assert json.loads(response["body"]) == {"stock": 12}
        else:
            assert response == {"stock": 12}
    assert len(calls) == 3
    if filename == "client_credentials.py":
        provider = deployment
        provider.return_value.get.assert_called_once_with("orders/oauth-secret", max_age=300)
        config = provider.call_args.kwargs["boto_config"]
        assert config.connect_timeout == 1
        assert config.read_timeout == 2
        assert config.retries == {"total_max_attempts": 1}


@pytest.mark.parametrize(
    "failure",
    [TokenExchangeError(retryable=True), DownstreamRequestError(), 403],
    ids=["token-unavailable", "downstream-unavailable", "api-forbidden"],
)
def test_diagnostics_returns_an_http_error_without_replaying_the_request(deployment, monkeypatch, failure, mocker):
    if isinstance(failure, Exception):
        request = mocker.Mock(side_effect=failure)
    else:
        request = mocker.Mock(return_value=urllib3.HTTPResponse(status=failure))
    monkeypatch.setattr(OAuth2Client, "request", request)
    example = runpy.run_path(str(EXAMPLES / "diagnostics.py"))

    response = example["lambda_handler"]({"sku": "item/123"}, {})

    assert response == {"statusCode": 502, "body": "Inventory request unavailable"}
    request.assert_called_once_with("GET", "https://inventory.example.com/stock/item%2F123", timeout=5)
