from __future__ import annotations

from io import BytesIO

import boto3
import pytest
from botocore.config import Config
from botocore.response import StreamingBody
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.parameters import AppConfigProvider
from aws_lambda_powertools.utilities.parameters.exceptions import GetParameterError


@pytest.fixture
def provider_and_stubber():
    client = boto3.client(
        "appconfigdata",
        config=Config(region_name="us-east-1", proxies={}),
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )
    provider = AppConfigProvider(environment="dev", application="app", boto3_client=client)
    with Stubber(client) as stubber:
        yield provider, stubber
        stubber.assert_no_pending_responses()


def add_session(stubber, token, name="cfg", **sdk_options):
    stubber.add_response(
        "start_configuration_session",
        {"InitialConfigurationToken": token},
        {
            "ConfigurationProfileIdentifier": name,
            "ApplicationIdentifier": "app",
            "EnvironmentIdentifier": "dev",
            **sdk_options,
        },
    )


def add_poll(stubber, token, next_token, value, declared_length=None):
    stubber.add_response(
        "get_latest_configuration",
        {
            "NextPollConfigurationToken": next_token,
            "Configuration": StreamingBody(BytesIO(value), len(value) if declared_length is None else declared_length),
        },
        {"ConfigurationToken": token},
    )


def add_rejected_token(stubber, token, problem="Expired"):
    stubber.add_client_error(
        "get_latest_configuration",
        "BadRequestException",
        "Token expired",
        expected_params={"ConfigurationToken": token},
        modeled_fields={
            "Reason": "InvalidParameters",
            "Details": {"InvalidParameters": {"ConfigurationToken": {"Problem": problem}}},
        },
    )


@pytest.mark.parametrize("problem", ["Expired", "Corrupted"])
def test_appconfig_recovers_rejected_poll_token_and_caches_new_value(provider_and_stubber, problem):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_poll(stubber, "initial", "expired", b"old")
    add_rejected_token(stubber, "expired", problem)
    add_session(stubber, "fresh")
    add_poll(stubber, "fresh", "next", b"new")

    assert provider.get("cfg", max_age=300) == b"old"
    assert provider.get("cfg", force_fetch=True, max_age=300) == b"new"
    assert provider.get("cfg", max_age=300) == b"new"
    assert provider._next_token["cfg"] == "next"


@pytest.mark.parametrize("problem", ["Expired", "Corrupted"])
@pytest.mark.parametrize("replacement_problem", ["Expired", "Corrupted"])
def test_appconfig_retries_once_then_allows_recovery_on_a_later_call(
    provider_and_stubber,
    problem,
    replacement_problem,
):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_rejected_token(stubber, "initial", problem)
    add_session(stubber, "retry")
    add_rejected_token(stubber, "retry", replacement_problem)

    with pytest.raises(GetParameterError, match="Token expired"):
        provider.get("cfg")
    stubber.assert_no_pending_responses()
    assert "cfg" not in provider._next_token

    add_session(stubber, "fresh")
    add_poll(stubber, "fresh", "next", b"recovered")
    assert provider.get("cfg") == b"recovered"


@pytest.mark.parametrize("recovery_problem", [None, "Expired", "Corrupted"])
def test_appconfig_preserves_token_and_last_value_for_poll_interval_errors(provider_and_stubber, recovery_problem):
    provider, stubber = provider_and_stubber
    options = {"RequiredMinimumPollIntervalInSeconds": 30}
    add_session(stubber, "initial", **options)
    add_poll(stubber, "initial", "next", b"old")
    token = "next"
    if recovery_problem:
        add_rejected_token(stubber, token, recovery_problem)
        add_session(stubber, "replacement", **options)
        token = "replacement"
    add_rejected_token(stubber, token, "PollIntervalNotSatisfied")
    add_rejected_token(stubber, token, "PollIntervalNotSatisfied")
    add_poll(stubber, token, "last", b"")

    assert provider.get("cfg", max_age=300, **options) == b"old"
    for _ in range(2):
        with pytest.raises(GetParameterError, match="BadRequestException"):
            provider.get("cfg", force_fetch=True, **options)
        assert provider._next_token["cfg"] == token
        assert provider.last_returned_value["cfg"] == b"old"
        assert provider.get("cfg", max_age=300) == b"old"

    assert provider.get("cfg", force_fetch=True) == b"old"
    assert provider._next_token["cfg"] == "last"


@pytest.mark.parametrize("recovery_problem", [None, "Expired", "Corrupted"])
def test_appconfig_preserves_token_for_poll_interval_errors_before_first_value(provider_and_stubber, recovery_problem):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    token = "initial"
    if recovery_problem:
        add_rejected_token(stubber, token, recovery_problem)
        add_session(stubber, "replacement")
        token = "replacement"
    add_rejected_token(stubber, token, "PollIntervalNotSatisfied")
    add_poll(stubber, token, "next", b"new")

    with pytest.raises(GetParameterError, match="BadRequestException"):
        provider.get("cfg")
    assert provider._next_token["cfg"] == token
    assert "cfg" not in provider.last_returned_value
    assert provider.get("cfg") == b"new"


@pytest.mark.parametrize(
    "modeled_fields",
    [
        None,
        {"Reason": "InvalidParameters"},
        {"Details": {"InvalidParameters": {}}},
        {"Details": {"InvalidParameters": {"ConfigurationToken": {}}}},
        {"Details": {"InvalidParameters": {"ConfigurationToken": {"Problem": "Unknown"}}}},
        {"Details": {"InvalidParameters": {"OtherParameter": {"Problem": "Expired"}}}},
    ],
)
def test_appconfig_preserves_token_for_unrecognized_bad_requests(provider_and_stubber, modeled_fields):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_poll(stubber, "initial", "next", b"old")
    stubber.add_client_error(
        "get_latest_configuration",
        "BadRequestException",
        "unrecognized bad request",
        expected_params={"ConfigurationToken": "next"},
        modeled_fields=modeled_fields,
    )
    add_poll(stubber, "next", "last", b"")

    assert provider.get("cfg", max_age=300) == b"old"
    with pytest.raises(GetParameterError, match="unrecognized bad request"):
        provider.get("cfg", force_fetch=True)
    assert provider._next_token["cfg"] == "next"
    assert provider.last_returned_value["cfg"] == b"old"
    assert provider.get("cfg", force_fetch=True) == b"old"


def test_appconfig_starts_new_session_after_response_body_read_fails(provider_and_stubber):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_poll(stubber, "initial", "consumed", b"old")
    # A truncated response consumed the token but did not deliver usable configuration.
    add_poll(stubber, "consumed", "unread", b"partial", declared_length=100)

    assert provider.get("cfg", max_age=300) == b"old"
    with pytest.raises(GetParameterError, match="read, but total bytes expected"):
        provider.get("cfg", force_fetch=True)
    assert "cfg" not in provider._next_token
    assert provider.last_returned_value["cfg"] == b"old"

    add_session(stubber, "fresh")
    add_poll(stubber, "fresh", "next", b"complete")
    assert provider.get("cfg", force_fetch=True) == b"complete"


@pytest.mark.parametrize("error_code", ["ThrottlingException", "InternalServerException", "ResourceNotFoundException"])
def test_appconfig_does_not_restart_for_unrelated_service_errors(provider_and_stubber, error_code):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    stubber.add_client_error(
        "get_latest_configuration",
        error_code,
        "service failure",
        expected_params={"ConfigurationToken": "initial"},
    )
    with pytest.raises(GetParameterError, match="service failure"):
        provider.get("cfg")
    assert provider._next_token["cfg"] == "initial"
    stubber.assert_no_pending_responses()


def test_appconfig_preserves_session_options_and_configuration_isolation(provider_and_stubber):
    provider, stubber = provider_and_stubber
    options = {"RequiredMinimumPollIntervalInSeconds": 30}
    add_session(stubber, "other-initial", name="other")
    add_poll(stubber, "other-initial", "other-next", b"other-value")
    add_session(stubber, "initial", **options)
    add_rejected_token(stubber, "initial")
    add_session(stubber, "fresh", **options)
    add_poll(stubber, "fresh", "next", b'{"enabled":true}')
    add_poll(stubber, "next", "next-empty", b"")
    add_poll(stubber, "other-next", "other-last", b"")

    assert provider.get("other", max_age=0) == b"other-value"
    assert provider.get("cfg", transform="json", max_age=0, **options) == {"enabled": True}
    assert provider.get("cfg", transform="json", max_age=0) == {"enabled": True}
    assert provider.get("other", max_age=0) == b"other-value"
    assert provider._next_token == {"other": "other-last", "cfg": "next-empty"}
    assert options == {"RequiredMinimumPollIntervalInSeconds": 30}


def test_appconfig_can_recover_after_restart_session_fails(provider_and_stubber):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_rejected_token(stubber, "initial")
    stubber.add_client_error("start_configuration_session", "ResourceNotFoundException", "session unavailable")

    with pytest.raises(GetParameterError, match="session unavailable"):
        provider.get("cfg")
    assert "cfg" not in provider._next_token

    add_session(stubber, "fresh")
    add_poll(stubber, "fresh", "next", b"recovered")
    assert provider.get("cfg") == b"recovered"


def test_appconfig_does_not_retry_initial_session_errors(provider_and_stubber):
    provider, stubber = provider_and_stubber
    stubber.add_client_error("start_configuration_session", "BadRequestException", "invalid session options")
    with pytest.raises(GetParameterError, match="invalid session options"):
        provider.get("cfg")
    assert "cfg" not in provider._next_token


def test_appconfig_does_not_retry_replacement_token_throttling(provider_and_stubber):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_rejected_token(stubber, "initial")
    add_session(stubber, "fresh")
    stubber.add_client_error(
        "get_latest_configuration",
        "ThrottlingException",
        "slow down",
        expected_params={"ConfigurationToken": "fresh"},
    )
    with pytest.raises(GetParameterError, match="slow down"):
        provider.get("cfg")
    assert provider._next_token["cfg"] == "fresh"


def test_appconfig_discards_replacement_token_if_its_response_is_truncated(provider_and_stubber):
    provider, stubber = provider_and_stubber
    add_session(stubber, "initial")
    add_rejected_token(stubber, "initial")
    add_session(stubber, "fresh")
    add_poll(stubber, "fresh", "unread", b"partial", declared_length=100)
    with pytest.raises(GetParameterError, match="read, but total bytes expected"):
        provider.get("cfg")
    assert "cfg" not in provider._next_token
    assert "cfg" not in provider.last_returned_value
