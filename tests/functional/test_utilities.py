import random
import string
from datetime import datetime, timedelta

import pytest
from botocore import stub

from aws_lambda_powertools import utilities
from aws_lambda_powertools.utilities import parameters


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


def test_get_parameter_new(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test get_parameter() with a new parameter name
    """

    # Patch the parameter value store
    monkeypatch.setattr(parameters, "PARAMETER_VALUES", {})

    # Stub boto3
    stubber = stub.Stubber(parameters.ssm)
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

    # Get the parameter value
    try:
        value = utilities.get_parameter(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_get_parameter_cached(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test get_parameter() with a cached value for parameter name
    """

    # Patch the parameter value store
    monkeypatch.setattr(
        parameters,
        "PARAMETER_VALUES",
        {mock_name: parameters.ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))},
    )

    # Stub boto3
    stubber = stub.Stubber(parameters.ssm)
    stubber.activate()

    # Get the parameter value
    try:
        value = utilities.get_parameter(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_get_parameter_expired(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test get_parameter() with a cached, but expired value for parameter name
    """

    # Patch the parameter value store
    monkeypatch.setattr(
        parameters,
        "PARAMETER_VALUES",
        {mock_name: parameters.ExpirableValue(mock_value, datetime.now() - timedelta(seconds=60))},
    )

    # Stub boto3
    stubber = stub.Stubber(parameters.ssm)
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

    # Get the parameter value
    try:
        value = utilities.get_parameter(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()
