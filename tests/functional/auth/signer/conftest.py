import datetime as dt

import pytest

FROZEN = dt.datetime(2026, 11, 15, 12, 0, 0, tzinfo=dt.timezone.utc)


@pytest.fixture
def lambda_env(monkeypatch):
    """Credentials and region the way the Lambda runtime sets them."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secretexample")  # noqa: S105 test value
    monkeypatch.setenv("AWS_SESSION_TOKEN", "tokenexample")  # noqa: S105 test value
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)


@pytest.fixture
def frozen_clock(monkeypatch):
    """Pin botocore's signing clock so signatures are reproducible."""
    import botocore.auth

    monkeypatch.setattr(botocore.auth, "get_current_datetime", lambda: FROZEN)
    return FROZEN


def reference_signature(method, url, headers, body, service, region, *, s3=False):
    """Sign with botocore directly, the way the AWS SDK does, to compare against the utility."""
    from botocore.auth import S3SigV4Auth, SigV4Auth
    from botocore.awsrequest import AWSRequest
    from botocore.credentials import Credentials

    request = AWSRequest(method=method, url=url, headers=dict(headers), data=body)
    auth_class = S3SigV4Auth if s3 else SigV4Auth
    auth_class(Credentials("AKIAEXAMPLE", "secretexample", "tokenexample"), service, region).add_auth(request)
    return dict(request.headers)
