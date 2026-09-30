import base64
import time
from collections import deque
from urllib.parse import parse_qs, unquote_plus

import pytest

from aws_lambda_powertools.utilities.auth_alpha import OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import TokenExchangeError

TOKEN_URL = "https://idp.example.com/token?tenant=inventory"
TOKEN_RESPONSE = {"access_token": "test-token", "token_type": "Bearer", "expires_in": 600}


@pytest.mark.parametrize(
    "options",
    [{}, {"auth_method": "client_secret_basic"}, {"auth_method": "client_secret_post"}],
    ids=["default-basic", "explicit-basic", "post"],
)
@pytest.mark.parametrize("selection", [{}, {"audience": "inventory"}, {"resource": "urn:example:inventory"}])
@pytest.mark.parametrize(
    ("client_id", "secret"),
    [
        ("client:id", "secret:value with space+&=%25"),
        ("clïent:日本語", "sécret/日本語&scope=admin\r\ninjected"),
    ],
)
def test_credentials_use_only_the_selected_location_and_are_encoded_once(http, options, selection, client_id, secret):
    http.serve(TOKEN_URL, TOKEN_RESPONSE, method="POST")
    subject = OAuth2Client(
        token_url=TOKEN_URL,
        client_id=client_id,
        client_secret=secret,
        scopes=["inventory:read", "inventory:write"],
        **selection,
        **options,
    )

    assert subject.auth_headers() == {"Authorization": "Bearer test-token"}
    assert subject.auth_headers() == {"Authorization": "Bearer test-token"}

    assert len(http.requests) == 1
    method, url, request = http.requests[0]
    assert method == "POST"
    assert url == TOKEN_URL
    assert request["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    expected = {
        "grant_type": ["client_credentials"],
        "scope": ["inventory:read inventory:write"],
        **{key: [value] for key, value in selection.items()},
    }
    if options.get("auth_method") == "client_secret_post":
        expected.update(client_id=[client_id], client_secret=[secret])
        assert "Authorization" not in request["headers"]
    else:
        scheme, authorization = request["headers"]["Authorization"].split(" ", 1)
        assert scheme == "Basic"
        encoded_id, encoded_secret = base64.b64decode(authorization, validate=True).decode().split(":")
        assert unquote_plus(encoded_id) == client_id
        assert unquote_plus(encoded_secret) == secret
    assert parse_qs(request["body"].decode("ascii"), keep_blank_values=True) == expected


@pytest.mark.parametrize(
    "auth_method",
    [None, "", "basic", "post", "CLIENT_SECRET_POST", "client_secret_jwt", "private_key_jwt", "none", [], {}, 1],
)
def test_invalid_auth_method_is_rejected_before_loading_credentials(http, mocker, auth_method):
    load_secret = mocker.Mock(return_value="private-test-secret")
    with pytest.raises(ValueError, match="auth_method"):
        OAuth2Client(
            token_url=TOKEN_URL,
            client_id="client",
            client_secret=load_secret,
            auth_method=auth_method,
        )

    load_secret.assert_not_called()
    assert http.requests == []


@pytest.mark.parametrize("status", [429, 503])
def test_post_rebuilds_the_form_with_the_current_secret_on_retry(http, clock, monkeypatch, status):
    secrets = deque(["initial secret+&=", "rotated secret+&="])
    http.responses[("POST", TOKEN_URL)] = deque([(status, {}), (200, TOKEN_RESPONSE)])
    monkeypatch.setattr(time, "sleep", clock.advance)
    subject = OAuth2Client(
        token_url=TOKEN_URL,
        client_id="orders",
        client_secret=secrets.popleft,
        auth_method="client_secret_post",
        scopes=["inventory:read"],
        resource="urn:example:inventory",
    )

    assert subject.auth_headers() == {"Authorization": "Bearer test-token"}
    assert not secrets
    assert len(http.requests) == 2
    for request, secret in zip(http.requests, ["initial secret+&=", "rotated secret+&="], strict=True):
        assert request[1] == TOKEN_URL
        assert request[2]["headers"] == {"Content-Type": "application/x-www-form-urlencoded"}
        assert parse_qs(request[2]["body"].decode()) == {
            "grant_type": ["client_credentials"],
            "scope": ["inventory:read"],
            "resource": ["urn:example:inventory"],
            "client_id": ["orders"],
            "client_secret": [secret],
        }


@pytest.mark.parametrize("auth_method", ["client_secret_basic", "client_secret_post"])
def test_authentication_rejection_does_not_fall_back_to_another_method(http, auth_method):
    http.serve(TOKEN_URL, {"error": "invalid_client"}, method="POST", status=401)
    subject = OAuth2Client(
        token_url=TOKEN_URL,
        client_id="client",
        client_secret="test-secret",
        auth_method=auth_method,
    )

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert not error.value.retryable
    assert len(http.requests) == 1
