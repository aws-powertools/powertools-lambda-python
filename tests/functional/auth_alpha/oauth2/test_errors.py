import io
import json
import traceback
from uuid import uuid4

import pytest
import urllib3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.auth_alpha import AuthFailureReason, OAuth2Client
from aws_lambda_powertools.utilities.auth_alpha.exceptions import AuthError
from aws_lambda_powertools.utilities.auth_alpha.oauth2.exceptions import DownstreamRequestError, TokenExchangeError

TOKEN_URL = "https://idp.example.com/token"
RESOURCE_URL = "https://api.example.com/orders"
PRIVATE_DATA = "test-only-sensitive-provider-data"


@pytest.mark.parametrize("operation", ["auth_headers", "request"])
@pytest.mark.parametrize("failure", ["secret", "transport", "json", "expires_in", "downstream"])
def test_errors_never_expose_credentials_or_active_exception_chains(http, operation, failure, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    def load_secret():
        if failure == "secret":
            raise RuntimeError(PRIVATE_DATA)
        return PRIVATE_DATA

    subject = OAuth2Client(token_url=TOKEN_URL, client_id="orders", client_secret=load_secret)
    payload = {"access_token": "test-token", "token_type": "Bearer", "expires_in": 600}
    if failure == "transport":
        payload = urllib3.exceptions.SSLError(PRIVATE_DATA)
    elif failure == "json":
        payload = PRIVATE_DATA.encode()
    elif failure == "expires_in":
        payload["expires_in"] = PRIVATE_DATA
    elif operation == "auth_headers" and failure == "downstream":
        # This operation has no downstream request, so exercise a bad token instead.
        payload["access_token"] = PRIVATE_DATA + "\r\ninvalid"
    http.serve(TOKEN_URL, payload, method="POST")
    http.serve(RESOURCE_URL, urllib3.exceptions.SSLError(PRIVATE_DATA))
    stream = io.StringIO()
    logger = Logger(service=f"oauth-error-test-{uuid4()}", stream=stream)
    expected = DownstreamRequestError if operation == "request" and failure == "downstream" else TokenExchangeError
    invoke = subject.request if operation == "request" else subject.auth_headers
    args = ("GET", RESOURCE_URL) if operation == "request" else ()

    try:
        raise LookupError(PRIVATE_DATA)
    except LookupError:
        with pytest.raises(expected) as captured:
            invoke(*args)
        error = captured.value
        logger.exception("Authentication failed", exc_info=(type(error), error, error.__traceback__))
    assert isinstance(error, AuthError)
    assert error.__context__ is None
    assert error.__cause__ is None
    assert PRIVATE_DATA not in str(error)
    assert PRIVATE_DATA not in repr(error)
    assert PRIVATE_DATA not in "".join(traceback.format_exception(error))
    assert PRIVATE_DATA not in stream.getvalue()
    assert json.loads(stream.getvalue())["exception_name"] == expected.__name__


@pytest.mark.parametrize(
    "status,retryable,attempts",
    [(400, False, 1), (401, False, 1), (429, True, 3), (503, True, 3)],
)
def test_exchange_errors_expose_fixed_reason_and_retryability(http, clock, monkeypatch, status, retryable, attempts):
    monkeypatch.setattr("time.sleep", clock.advance)
    subject = OAuth2Client(token_url=TOKEN_URL, client_id="orders", client_secret="test-secret")
    http.serve(TOKEN_URL, {"error_description": PRIVATE_DATA}, method="POST", status=status)

    with pytest.raises(TokenExchangeError) as error:
        subject.auth_headers()
    assert error.value.reason is AuthFailureReason.TOKEN_EXCHANGE_FAILED
    assert error.value.retryable is retryable
    assert len(http.requests) == attempts


def test_outbound_and_jwt_errors_share_the_public_base():
    from aws_lambda_powertools.utilities.auth_alpha.jwt.exceptions import AuthError as JWTAuthError
    from aws_lambda_powertools.utilities.auth_alpha.jwt.exceptions import AuthFailureReason as JWTFailureReason

    assert JWTAuthError is AuthError
    assert JWTFailureReason is AuthFailureReason
    assert issubclass(TokenExchangeError, AuthError)
    assert DownstreamRequestError().reason is AuthFailureReason.DOWNSTREAM_REQUEST_FAILED
    assert not DownstreamRequestError().retryable
