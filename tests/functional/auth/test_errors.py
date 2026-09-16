import io
import json
import traceback
from functools import partial
from uuid import uuid4

import pytest
import urllib3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.auth import JWTVerifier, OAuth2Client
from aws_lambda_powertools.utilities.auth.exceptions import (
    AuthError,
    InvalidClaimsError,
    InvalidSignatureError,
    InvalidTokenError,
    JWKSFetchError,
    TokenExchangeError,
)

ISSUER = "https://idp.example.com/"
TOKEN_URL = ISSUER + "token"
RESOURCE_URL = "https://api.example.com"
PRIVATE_DATA = "test-only-sensitive-provider-data"


def assert_sanitized(operation, expected_error):
    stream = io.StringIO()
    logger = Logger(service=f"auth-error-test-{uuid4()}", stream=stream)
    try:
        operation()
    except expected_error as error:
        logger.exception("Auth failed")
        assert error.__context__ is None
        assert error.__cause__ is None
        assert PRIVATE_DATA not in str(error)
        assert PRIVATE_DATA not in repr(error)
        assert PRIVATE_DATA not in "".join(traceback.format_exception(type(error), error, error.__traceback__))
    else:
        pytest.fail("Expected a sanitized Auth error")
    log = json.loads(stream.getvalue())
    assert log["exception_name"] == expected_error.__name__
    assert PRIVATE_DATA not in stream.getvalue()


@pytest.mark.parametrize("method", ["auth_headers", "request"])
def test_secret_loader_errors_have_no_chain_even_inside_a_callers_exception_handler(method):
    def load_secret():
        raise RuntimeError(PRIVATE_DATA)

    client = OAuth2Client(token_url=TOKEN_URL, client_id="orders", client_secret=load_secret)
    operation = client.auth_headers if method == "auth_headers" else lambda: client.request("GET", RESOURCE_URL)
    try:
        raise LookupError(PRIVATE_DATA)
    except LookupError:
        assert_sanitized(operation, TokenExchangeError)


@pytest.mark.parametrize("method", ["verify", "prefetch", "group_verify", "group_prefetch", "authorize"])
@pytest.mark.parametrize("failure", ["transport", "json"])
def test_remote_key_failures_detach_provider_exceptions(http, issue_token, method, failure):
    keys_url = ISSUER + f"keys/{uuid4()}"
    response = urllib3.exceptions.SSLError(PRIVATE_DATA) if failure == "transport" else PRIVATE_DATA.encode()
    http.serve(keys_url, response)
    verifier = JWTVerifier(issuer=ISSUER, audience=RESOURCE_URL, algorithms=["RS256"], jwks_uri=keys_url)
    subject = JWTVerifier.any_of(verifier) if method.startswith("group_") else verifier
    token = issue_token()
    event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:123456789012:api123/prod/GET/orders",
        "authorizationToken": "Bearer " + token,
    }
    if method.endswith("prefetch"):
        operation = subject.prefetch
    elif method == "authorize":
        operation = partial(subject.authorize, event)
    else:
        operation = partial(subject.verify, token)
    assert_sanitized(operation, JWKSFetchError)


@pytest.mark.parametrize("group", [False, True])
@pytest.mark.parametrize("failure", ["header", "claims", "signature"])
def test_verification_errors_detach_parser_and_crypto_exceptions(jwks, issue_token, claims, group, failure):
    subject = JWTVerifier(issuer=ISSUER, audience=RESOURCE_URL, algorithms=["RS256"], jwks=jwks)
    if group:
        subject = JWTVerifier.any_of(subject)
    if failure == "header":
        token, expected_error = PRIVATE_DATA, InvalidTokenError
    elif failure == "claims":
        claims["aud"] = PRIVATE_DATA
        token, expected_error = issue_token(claims), InvalidClaimsError
    else:
        encoded, _ = issue_token().rsplit(".", 1)
        token, expected_error = encoded + ".AAAA", InvalidSignatureError
    assert_sanitized(lambda: subject.verify(token), expected_error)


@pytest.mark.parametrize("failure", ["transport", "json", "expires_in", "downstream"])
def test_oauth_errors_detach_transport_and_response_exceptions(http, failure):
    client = OAuth2Client(token_url=TOKEN_URL, client_id="orders", client_secret="test-secret")
    payload = {"access_token": "test-token", "token_type": "Bearer", "expires_in": 600}
    if failure == "transport":
        response = urllib3.exceptions.SSLError(PRIVATE_DATA)
    elif failure == "json":
        response = PRIVATE_DATA.encode()
    elif failure == "expires_in":
        response = {**payload, "expires_in": PRIVATE_DATA}
    else:
        response = payload
    http.serve(TOKEN_URL, response, method="POST")
    http.serve(RESOURCE_URL, urllib3.exceptions.SSLError(PRIVATE_DATA))
    operation = (lambda: client.request("GET", RESOURCE_URL)) if failure == "downstream" else client.auth_headers
    assert_sanitized(operation, AuthError if failure == "downstream" else TokenExchangeError)
