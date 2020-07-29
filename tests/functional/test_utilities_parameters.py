import random
import string
from datetime import datetime, timedelta

import pytest
from botocore import stub

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.parameters.base import ExpirableValue


@pytest.fixture(scope="function")
def mock_name():
    # Parameter name must match [a-zA-Z0-9_.-/]+
    return "".join(random.choices(string.ascii_letters + string.digits + "_.-/", k=random.randrange(3, 200)))


@pytest.fixture(scope="function")
def mock_value():
    # Standard parameters can be up to 4 KB
    return "".join(random.choices(string.printable, k=random.randrange(100, 4000)))


@pytest.fixture(scope="function")
def mock_version():
    return random.randrange(1, 1000)


def test_ssm_provider_get(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get() with a non-cached value
    """

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameter": {
            "Name": mock_name,
            "Type": "String",
            "Value": mock_value,
            "Version": mock_version,
            "Selector": f"{mock_name}:{mock_version}",
            "SourceResult": "string",
            "LastModifiedDate": datetime(2015, 1, 1),
            "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}",
        }
    }
    expected_params = {"Name": mock_name}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_cached(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get() with a cached value
    """

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_expired(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get() with a cached but expired value
    """

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() - timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameter": {
            "Name": mock_name,
            "Type": "String",
            "Value": mock_value,
            "Version": mock_version,
            "Selector": f"{mock_name}:{mock_version}",
            "SourceResult": "string",
            "LastModifiedDate": datetime(2015, 1, 1),
            "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}",
        }
    }
    expected_params = {"Name": mock_name}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_secrets_provider_get(monkeypatch, mock_name, mock_value):
    """
    Test SecretsProvider.get() with a non-cached value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(region="us-east-1")

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "ARN": f"arn:aws:secretsmanager:us-east-1:132456789012:secret/{mock_name}",
        "Name": mock_name,
        "VersionId": "7a9155b8-2dc9-466e-b4f6-5bc46516c84d",
        "SecretString": mock_value,
        "CreatedDate": datetime(2015, 1, 1),
    }
    expected_params = {"SecretId": mock_name}
    stubber.add_response("get_secret_value", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_secrets_provider_get_cached(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SecretsProvider.get() with a cached value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(region="us-east-1")

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_secrets_provider_get_expired(monkeypatch, mock_name, mock_value):
    """
    Test SecretsProvider.get() with a cached but expired value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(region="us-east-1")

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() - timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "ARN": f"arn:aws:secretsmanager:us-east-1:132456789012:secret/{mock_name}",
        "Name": mock_name,
        "VersionId": "7a9155b8-2dc9-466e-b4f6-5bc46516c84d",
        "SecretString": mock_value,
        "CreatedDate": datetime(2015, 1, 1),
    }
    expected_params = {"SecretId": mock_name}
    stubber.add_response("get_secret_value", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()
