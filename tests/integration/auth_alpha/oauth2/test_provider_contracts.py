"""Documented provider contracts simulated over local TLS, not live provider tests.

Profiles cover client_secret_basic and client_secret_post with client_credentials,
given the corresponding server-side permissions and application configuration.
Tokens and credentials are synthetic. These tests do not validate tenant
configuration or provider availability.

Auth0 (select Client Secret (Basic/Post) and authorize the M2M app for the API):
https://auth0.com/docs/get-started/applications/credentials
https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow/call-your-api-using-the-client-credentials-flow
Entra ID (application permissions, /.default scope, Basic authentication supported):
https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow
Okta (custom authorization server for your API, not Okta management API scopes):
https://developer.okta.com/docs/guides/implement-grant-type/clientcreds/main/
https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth/
https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/
Keycloak (client authentication and service account roles enabled):
https://www.keycloak.org/docs/latest/server_admin/index.html#_service_accounts
"""

import base64
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs

import pytest

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import TokenExchangeError

PROFILES = {
    "auth0": {
        "path": "/oauth/token",
        "options": {"audience": "https://inventory.example.com"},
        "form": {"grant_type": ["client_credentials"], "audience": ["https://inventory.example.com"]},
        "response": {"token_type": "Bearer", "expires_in": 86400},
        "error_status": 403,
        "error": {"error": "access_denied", "error_description": "Unauthorized: private-auth0-detail"},
    },
    "entra": {
        "path": "/test-tenant/oauth2/v2.0/token",
        "options": {"scopes": ["https://graph.microsoft.com/.default"]},
        "form": {"grant_type": ["client_credentials"], "scope": ["https://graph.microsoft.com/.default"]},
        "response": {"token_type": "Bearer", "expires_in": 3599, "ext_expires_in": 3599},
        "error_status": 401,
        "error": {
            "error": "invalid_client",
            "error_description": "AADSTS7000215: private-entra-detail",
            "error_codes": [7000215],
            "trace_id": "test-trace-id",
            "correlation_id": "test-correlation-id",
        },
    },
    "okta": {
        "path": "/oauth2/default/v1/token",
        "options": {"scopes": ["inventory.read", "inventory.write"]},
        "form": {"grant_type": ["client_credentials"], "scope": ["inventory.read inventory.write"]},
        "response": {"token_type": "Bearer", "expires_in": 3600, "scope": "inventory.read inventory.write"},
        "error_status": 401,
        "error": {"error": "invalid_client", "error_description": "private-okta-detail"},
    },
    "keycloak": {
        "path": "/realms/inventory/protocol/openid-connect/token",
        "options": {},
        "form": {"grant_type": ["client_credentials"]},
        "response": {
            "token_type": "Bearer",
            "expires_in": 60,
            "scope": "email profile",
            "refresh_expires_in": 0,
            "not-before-policy": 0,
        },
        "error_status": 401,
        "error": {"error": "invalid_client", "error_description": "private-keycloak-detail"},
    },
}


class Provider:
    """Reject unexpected credentials or form fields before issuing a fake token."""

    def __init__(self, endpoint, name, auth_method="client_secret_basic"):
        self.name = name
        self.auth_method = auth_method
        self.profile = PROFILES[name]
        self.url = endpoint.url + self.profile["path"]
        # Reuse the ID across providers to expose accidental cache sharing.
        self.client_id = "shared-client"
        self.secret = f"{name}-test-secret"
        self.generation = 1
        self.forced_error = None
        self.accepted = 0
        endpoint.serve(self.profile["path"], {}, responder=self.respond)

    @property
    def token(self):
        return f"{self.name}-token-{self.generation}"

    def client(self, **overrides):
        return OAuth2Client(
            **{
                "token_url": self.url,
                "client_id": self.client_id,
                "client_secret": self.secret,
                "auth_method": self.auth_method,
                **self.profile["options"],
                **overrides,
            },
        )

    def respond(self, method, headers, body):
        fields = parse_qs(body.decode(), keep_blank_values=True)
        if self.auth_method == "client_secret_basic":
            expected_basic = base64.b64encode(f"{self.client_id}:{self.secret}".encode()).decode()
            if headers.get("Authorization") != f"Basic {expected_basic}":
                return self.profile["error_status"], self.profile["error"]
        elif (
            "Authorization" in headers
            or fields.pop("client_id", None) != [self.client_id]
            or fields.pop("client_secret", None) != [self.secret]
        ):
            return self.profile["error_status"], self.profile["error"]
        if (
            method != "POST"
            or headers.get("Content-Type") != "application/x-www-form-urlencoded"
            or fields != self.profile["form"]
        ):
            return 400, {"error": "invalid_request", "error_description": "Unexpected token request"}
        if self.forced_error is not None:
            return self.forced_error
        self.accepted += 1
        return 200, {"access_token": self.token, **self.profile["response"]}


@pytest.fixture(params=["client_secret_basic", "client_secret_post"])
def auth_method(request):
    return request.param


@pytest.fixture(params=PROFILES)
def provider(https_server, request, auth_method):
    return Provider(https_server, request.param, auth_method=auth_method)


def test_provider_contract_acquires_caches_and_uses_token(provider, https_server):
    https_server.serve("/inventory", {"items": [123]})
    subject = provider.client()

    assert subject.auth_headers() == {"Authorization": f"Bearer {provider.token}"}
    assert subject.request("GET", https_server.url + "/inventory").json() == {"items": [123]}
    assert subject.auth_headers() == {"Authorization": f"Bearer {provider.token}"}

    assert provider.accepted == 1
    exchange, resource = https_server.requests
    assert exchange[1] == provider.profile["path"]
    assert resource[2]["Authorization"] == f"Bearer {provider.token}"
    assert provider.secret not in str(resource)
    assert "Basic " not in str(resource)


def test_provider_contract_renews_with_rotated_credentials(provider, https_server, monkeypatch):
    current_secret = [provider.secret]
    loaded = []
    original_monotonic = time.monotonic
    elapsed = [0]
    monkeypatch.setattr(time, "monotonic", lambda: original_monotonic() + elapsed[0])

    def load_secret():
        loaded.append(current_secret[0])
        return current_secret[0]

    subject = provider.client(client_secret=load_secret)
    first_headers = subject.auth_headers()
    lifetime = provider.profile["response"]["expires_in"]
    elapsed[0] = lifetime - 31
    assert subject.auth_headers() == first_headers
    assert len(loaded) == 1

    provider.secret += "-rotated"
    current_secret[0] = provider.secret
    provider.generation += 1
    elapsed[0] = lifetime - 29

    assert subject.auth_headers() == {"Authorization": f"Bearer {provider.token}"}
    assert subject.auth_headers() != first_headers
    assert len(loaded) == 2
    assert loaded[0] != loaded[1]
    assert provider.accepted == 2
    assert len(https_server.requests) == 2


def test_provider_contract_rejects_credentials_without_retry_or_leaking_details(provider, https_server, caplog):
    subject = provider.client(client_secret="incorrect-test-secret")

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()

    assert not error.value.retryable
    assert error.value.__context__ is None
    assert error.value.__cause__ is None
    assert provider.accepted == 0
    assert len(https_server.requests) == 1
    diagnostic = "".join(traceback.format_exception(error.type, error.value, error.tb)) + caplog.text
    for private in (provider.secret, "incorrect-test-secret", provider.profile["error"]["error_description"]):
        assert private not in diagnostic


def test_provider_contract_rejects_wrong_resource_or_scope(provider, https_server):
    # Keycloak has no explicit scope here; an unassigned scope is rejected by this fixture.
    subject = provider.client(scopes=["wrong-scope"], audience=None)

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()

    assert not error.value.retryable
    assert provider.accepted == 0
    assert len(https_server.requests) == 1


def test_provider_contract_rejects_wrong_authentication_method_without_fallback(provider, https_server):
    other_method = "client_secret_post" if provider.auth_method == "client_secret_basic" else "client_secret_basic"

    with pytest.raises(TokenExchangeError) as error:
        provider.client(auth_method=other_method).auth_headers()

    assert not error.value.retryable
    assert provider.accepted == 0
    assert len(https_server.requests) == 1


@pytest.mark.parametrize("post_providers", [(), tuple(PROFILES), ("entra", "keycloak")], ids=["basic", "post", "mixed"])
def test_provider_contracts_keep_concurrent_clients_and_failures_isolated(https_server, post_providers):
    providers = [
        Provider(
            https_server,
            name,
            auth_method="client_secret_post" if name in post_providers else "client_secret_basic",
        )
        for name in PROFILES
    ]
    clients = [provider.client() for provider in providers]
    barrier = threading.Barrier(8)

    def acquire(index):
        barrier.wait(timeout=5)
        return index, clients[index].auth_headers()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(acquire, [0, 1, 2, 3] * 2))

    for index, headers in results:
        assert headers == {"Authorization": f"Bearer {providers[index].token}"}
    assert all(provider.accepted == 1 for provider in providers)
    assert Counter(request[1] for request in https_server.requests) == {
        provider.profile["path"]: 1 for provider in providers
    }

    providers[0].forced_error = 403, {"error": "access_denied"}
    with pytest.raises(TokenExchangeError):
        providers[0].client().auth_headers()
    for index in range(1, 4):
        assert clients[index].auth_headers() == {"Authorization": f"Bearer {providers[index].token}"}
    assert len(https_server.requests) == 5


def test_okta_management_scope_requires_an_unsupported_authentication_method(https_server):
    # The Okta org authorization server requires private_key_jwt for these scopes.
    # A synthetic rejection ensures the client does not retry or switch auth methods.
    path = "/oauth2/v1/token"
    https_server.serve(
        path,
        {"error": "invalid_client", "error_description": "private_key_jwt is required for this client"},
        status=401,
    )
    subject = OAuth2Client(
        token_url=https_server.url + path,
        client_id="service-client",
        client_secret="test-secret",
        scopes=["okta.users.read"],
    )

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()

    assert not error.value.retryable
    assert len(https_server.requests) == 1
    request = https_server.requests[0]
    assert request[2]["Authorization"].startswith("Basic ")
    assert parse_qs(request[3].decode()) == {
        "grant_type": ["client_credentials"],
        "scope": ["okta.users.read"],
    }
