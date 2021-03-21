import base64
import json
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict

import pytest
from boto3.dynamodb.conditions import Key
from botocore import stub
from botocore.config import Config
from botocore.response import StreamingBody

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.parameters.base import BaseProvider, ExpirableValue


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


@pytest.fixture(scope="module")
def config():
    return Config(region_name="us-east-1")


def test_dynamodb_provider_get(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with a non-cached value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_default_config(monkeypatch, mock_name, mock_value):
    """
    Test DynamoDBProvider.get() without setting a config
    """

    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_cached(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with a cached value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_expired(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with a cached but expired value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Inject value in the internal store
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() - timedelta(seconds=60))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_sdk_options(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with SDK options
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}, "ConsistentRead": True}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name, ConsistentRead=True)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_sdk_options_overwrite(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with SDK options that should be overwritten
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name, Key="THIS_SHOULD_BE_OVERWRITTEN")

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_multiple(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": f"{mock_value}/{name}"}}
            for name in mock_param_names
        ]
    }
    expected_params = {"TableName": table_name, "KeyConditionExpression": Key("id").eq(mock_name)}
    stubber.add_response("query", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_multiple_auto(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get_multiple() with transform = "auto"
    """
    mock_binary = mock_value.encode()
    mock_binary_data = base64.b64encode(mock_binary).decode()
    mock_json_data = json.dumps({mock_name: mock_value})
    mock_params = {"D.json": mock_json_data, "E.binary": mock_binary_data, "F": mock_value}
    table_name = "TEST_TABLE_AUTO"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": value}} for (name, value) in mock_params.items()
        ]
    }
    expected_params = {"TableName": table_name, "KeyConditionExpression": Key("id").eq(mock_name)}
    stubber.add_response("query", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name, transform="auto")

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_params)
        for key in mock_params.keys():
            assert key in values
            if key.endswith(".json"):
                assert values[key][mock_name] == mock_value
            elif key.endswith(".binary"):
                assert values[key] == mock_binary
            else:
                assert values[key] == mock_value
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_multiple_next_token(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)

    # First call
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": f"{mock_value}/{name}"}}
            for name in mock_param_names[:1]
        ],
        "LastEvaluatedKey": {"id": {"S": mock_name}, "sk": {"S": mock_param_names[0]}},
    }
    expected_params = {"TableName": table_name, "KeyConditionExpression": Key("id").eq(mock_name)}
    stubber.add_response("query", response, expected_params)

    # Second call
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": f"{mock_value}/{name}"}}
            for name in mock_param_names[1:]
        ]
    }
    expected_params = {
        "TableName": table_name,
        "KeyConditionExpression": Key("id").eq(mock_name),
        "ExclusiveStartKey": {"id": mock_name, "sk": mock_param_names[0]},
    }
    stubber.add_response("query", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_multiple_sdk_options(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get_multiple() with custom SDK options
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": f"{mock_value}/{name}"}}
            for name in mock_param_names
        ]
    }
    expected_params = {
        "TableName": table_name,
        "KeyConditionExpression": Key("id").eq(mock_name),
        "ConsistentRead": True,
    }
    stubber.add_response("query", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name, ConsistentRead=True)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_dynamodb_provider_get_multiple_sdk_options_overwrite(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get_multiple() with custom SDK options that should be overwritten
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {
        "Items": [
            {"id": {"S": mock_name}, "sk": {"S": name}, "value": {"S": f"{mock_value}/{name}"}}
            for name in mock_param_names
        ]
    }
    expected_params = {
        "TableName": table_name,
        "KeyConditionExpression": Key("id").eq(mock_name),
    }
    stubber.add_response("query", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name, KeyConditionExpression="THIS_SHOULD_BE_OVERWRITTEN")

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_ssm_provider_get(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get() with a non-cached value
    """

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_default_config(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get() without specifying the config
    """

    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    # Create a new provider
    provider = parameters.SSMProvider()

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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_cached(mock_name, mock_value, config):
    """
    Test SSMProvider.get() with a cached value
    """

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

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


def test_ssm_provider_get_expired(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get() with a cached but expired value
    """

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_sdk_options_overwrite(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get() with custom SDK options overwritten
    """

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name, Name="THIS_SHOULD_BE_OVERWRITTEN", WithDecryption=True)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameters": [
            {
                "Name": f"{mock_name}/{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names
        ]
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple_different_path(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get_multiple() with a non-cached path and names that don't start with the path
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameters": [
            {
                "Name": f"{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names
        ]
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple_next_token(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get_multiple() with a non-cached path with multiple calls
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)

    # First call
    response = {
        "Parameters": [
            {
                "Name": f"{mock_name}/{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names[:1]
        ],
        "NextToken": "next_token",
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False}
    stubber.add_response("get_parameters_by_path", response, expected_params)

    # Second call
    response = {
        "Parameters": [
            {
                "Name": f"{mock_name}/{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names[1:]
        ]
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False, "NextToken": "next_token"}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple_sdk_options(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get_multiple() with SDK options
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameters": [
            {
                "Name": f"{mock_name}/{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names
        ]
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False, "MaxResults": 10}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(mock_name, MaxResults=10)

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple_sdk_options_overwrite(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get_multiple() with SDK options overwritten
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "Parameters": [
            {
                "Name": f"{mock_name}/{name}",
                "Type": "String",
                "Value": f"{mock_value}/{name}",
                "Version": mock_version,
                "Selector": f"{mock_name}/{name}:{mock_version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{mock_name}/{name}",
            }
            for name in mock_param_names
        ]
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(
            mock_name, Path="THIS_SHOULD_BE_OVERWRITTEN", Recursive=False, WithDecryption=True
        )

        stubber.assert_no_pending_responses()

        assert len(values) == len(mock_param_names)
        for name in mock_param_names:
            assert name in values
            assert values[name] == f"{mock_value}/{name}"
    finally:
        stubber.deactivate()


def test_secrets_provider_get(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with a non-cached value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(config=config)

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


def test_secrets_provider_get_default_config(monkeypatch, mock_name, mock_value):
    """
    Test SecretsProvider.get() without specifying a config
    """

    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    # Create a new provider
    provider = parameters.SecretsProvider()

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


def test_secrets_provider_get_cached(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with a cached value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(config=config)

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


def test_secrets_provider_get_expired(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with a cached but expired value
    """

    # Create a new provider
    provider = parameters.SecretsProvider(config=config)

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


def test_secrets_provider_get_sdk_options(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with custom SDK options
    """

    # Create a new provider
    provider = parameters.SecretsProvider(config=config)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {
        "ARN": f"arn:aws:secretsmanager:us-east-1:132456789012:secret/{mock_name}",
        "Name": mock_name,
        "VersionId": "7a9155b8-2dc9-466e-b4f6-5bc46516c84d",
        "SecretString": mock_value,
        "CreatedDate": datetime(2015, 1, 1),
    }
    expected_params = {"SecretId": mock_name, "VersionId": "7a9155b8-2dc9-466e-b4f6-5bc46516c84d"}
    stubber.add_response("get_secret_value", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name, VersionId="7a9155b8-2dc9-466e-b4f6-5bc46516c84d")

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_secrets_provider_get_sdk_options_overwrite(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with custom SDK options overwritten
    """

    # Create a new provider
    provider = parameters.SecretsProvider(config=config)

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
        value = provider.get(mock_name, SecretId="THIS_SHOULD_BE_OVERWRITTEN")

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_base_provider_get_exception(mock_name):
    """
    Test BaseProvider.get() that raises an exception
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            raise Exception("test exception raised")

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    with pytest.raises(parameters.GetParameterError) as excinfo:
        provider.get(mock_name)

    assert "test exception raised" in str(excinfo)


def test_base_provider_get_multiple_exception(mock_name):
    """
    Test BaseProvider.get_multiple() that raises an exception
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            raise Exception("test exception raised")

    provider = TestProvider()

    with pytest.raises(parameters.GetParameterError) as excinfo:
        provider.get_multiple(mock_name)

    assert "test exception raised" in str(excinfo)


def test_base_provider_get_transform_json(mock_name, mock_value):
    """
    Test BaseProvider.get() with a json transform
    """

    mock_data = json.dumps({mock_name: mock_value})

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_data

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    value = provider.get(mock_name, transform="json")

    assert isinstance(value, dict)
    assert mock_name in value
    assert value[mock_name] == mock_value


def test_base_provider_get_transform_json_exception(mock_name, mock_value):
    """
    Test BaseProvider.get() with a json transform that raises an exception
    """

    mock_data = json.dumps({mock_name: mock_value}) + "{"

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_data

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        provider.get(mock_name, transform="json")

    assert "Extra data" in str(excinfo)


def test_base_provider_get_transform_binary(mock_name, mock_value):
    """
    Test BaseProvider.get() with a binary transform
    """

    mock_binary = mock_value.encode()
    mock_data = base64.b64encode(mock_binary).decode()

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_data

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    value = provider.get(mock_name, transform="binary")

    assert isinstance(value, bytes)
    assert value == mock_binary


def test_base_provider_get_transform_binary_exception(mock_name):
    """
    Test BaseProvider.get() with a binary transform that raises an exception
    """

    mock_data = "qw"
    print(mock_data)

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_data

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        provider.get(mock_name, transform="binary")

    assert "Incorrect padding" in str(excinfo)


def test_base_provider_get_multiple_transform_json(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with a json transform
    """

    mock_data = json.dumps({mock_name: mock_value})

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data}

    provider = TestProvider()

    value = provider.get_multiple(mock_name, transform="json")

    assert isinstance(value, dict)
    assert value["A"][mock_name] == mock_value


def test_base_provider_get_multiple_transform_json_partial_failure(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with a json transform that contains a partial failure
    """

    mock_data = json.dumps({mock_name: mock_value})

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data, "B": mock_data + "{"}

    provider = TestProvider()

    value = provider.get_multiple(mock_name, transform="json")

    assert isinstance(value, dict)
    assert value["A"][mock_name] == mock_value
    assert value["B"] is None


def test_base_provider_get_multiple_transform_json_exception(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with a json transform that raises an exception
    """

    mock_data = json.dumps({mock_name: mock_value}) + "{"

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data}

    provider = TestProvider()

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        provider.get_multiple(mock_name, transform="json", raise_on_transform_error=True)

    assert "Extra data" in str(excinfo)


def test_base_provider_get_multiple_transform_binary(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with a binary transform
    """

    mock_binary = mock_value.encode()
    mock_data = base64.b64encode(mock_binary).decode()

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data}

    provider = TestProvider()

    value = provider.get_multiple(mock_name, transform="binary")

    assert isinstance(value, dict)
    assert value["A"] == mock_binary


def test_base_provider_get_multiple_transform_binary_partial_failure(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with a binary transform that contains a partial failure
    """

    mock_binary = mock_value.encode()
    mock_data_a = base64.b64encode(mock_binary).decode()
    mock_data_b = "qw"

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data_a, "B": mock_data_b}

    provider = TestProvider()

    value = provider.get_multiple(mock_name, transform="binary")

    assert isinstance(value, dict)
    assert value["A"] == mock_binary
    assert value["B"] is None


def test_base_provider_get_multiple_transform_binary_exception(mock_name):
    """
    Test BaseProvider.get_multiple() with a binary transform that raises an exception
    """

    mock_data = "qw"

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_data}

    provider = TestProvider()

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        provider.get_multiple(mock_name, transform="binary", raise_on_transform_error=True)

    assert "Incorrect padding" in str(excinfo)


def test_base_provider_get_multiple_cached(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with cached values
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    provider.store[(mock_name, None)] = ExpirableValue({"A": mock_value}, datetime.now() + timedelta(seconds=60))

    value = provider.get_multiple(mock_name)

    assert isinstance(value, dict)
    assert value["A"] == mock_value


def test_base_provider_get_multiple_expired(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple() with expired values
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_value}

    provider = TestProvider()

    provider.store[(mock_name, None)] = ExpirableValue({"B": mock_value}, datetime.now() - timedelta(seconds=60))

    value = provider.get_multiple(mock_name)

    assert isinstance(value, dict)
    assert value["A"] == mock_value


def test_get_parameter(monkeypatch, mock_name, mock_value):
    """
    Test get_parameter()
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    value = parameters.get_parameter(mock_name)

    assert value == mock_value


def test_get_parameter_new(monkeypatch, mock_name, mock_value):
    """
    Test get_parameter() without a default provider
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            assert not kwargs["decrypt"]
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setattr(parameters.ssm, "DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters.ssm, "SSMProvider", TestProvider)

    value = parameters.get_parameter(mock_name)

    assert value == mock_value


def test_get_parameters(monkeypatch, mock_name, mock_value):
    """
    Test get_parameters()
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_value}

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    values = parameters.get_parameters(mock_name)

    assert len(values) == 1
    assert values["A"] == mock_value


def test_get_parameters_new(monkeypatch, mock_name, mock_value):
    """
    Test get_parameters() without a default provider
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            assert kwargs["recursive"]
            assert not kwargs["decrypt"]
            return mock_value

    monkeypatch.setattr(parameters.ssm, "DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters.ssm, "SSMProvider", TestProvider)

    value = parameters.get_parameters(mock_name)

    assert value == mock_value


def test_get_secret(monkeypatch, mock_name, mock_value):
    """
    Test get_secret()
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "secrets", TestProvider())

    value = parameters.get_secret(mock_name)

    assert value == mock_value


def test_get_secret_new(monkeypatch, mock_name, mock_value):
    """
    Test get_secret() without a default provider
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setattr(parameters.secrets, "DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters.secrets, "SecretsProvider", TestProvider)

    value = parameters.get_secret(mock_name)

    assert value == mock_value


def test_appconf_provider_get_configuration_json_content_type(mock_name, config):
    """
    Test get_configuration.get with default values
    """

    # Create a new provider
    environment = "dev"
    application = "myapp"
    provider = parameters.AppConfigProvider(environment=environment, application=application, config=config)

    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    encoded_message = json.dumps(mock_body_json).encode("utf-8")
    mock_value = StreamingBody(BytesIO(encoded_message), len(encoded_message))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {"Content": mock_value, "ConfigurationVersion": "1", "ContentType": "application/json"}
    stubber.add_response("get_configuration", response)
    stubber.activate()

    try:
        value = provider.get(mock_name, transform="json", ClientConfigurationVersion="2")

        assert value == mock_body_json
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_appconf_provider_get_configuration_no_transform(mock_name, config):
    """
    Test appconfigprovider.get with default values
    """

    # Create a new provider
    environment = "dev"
    application = "myapp"
    provider = parameters.AppConfigProvider(environment=environment, application=application, config=config)

    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    encoded_message = json.dumps(mock_body_json).encode("utf-8")
    mock_value = StreamingBody(BytesIO(encoded_message), len(encoded_message))

    # Stub the boto3 client
    stubber = stub.Stubber(provider.client)
    response = {"Content": mock_value, "ConfigurationVersion": "1", "ContentType": "application/json"}
    stubber.add_response("get_configuration", response)
    stubber.activate()

    try:
        value = provider.get(mock_name)
        str_value = value.decode("utf-8")
        assert str_value == json.dumps(mock_body_json)
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_appconf_get_app_config_no_transform(monkeypatch, mock_name):
    """
    Test get_app_config()
    """
    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return json.dumps(mock_body_json).encode("utf-8")

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "appconfig", TestProvider())

    environment = "dev"
    application = "myapp"
    value = parameters.get_app_config(mock_name, environment=environment, application=application)
    str_value = value.decode("utf-8")
    assert str_value == json.dumps(mock_body_json)


def test_appconf_get_app_config_new(monkeypatch, mock_name, mock_value):
    # GIVEN
    class TestProvider(BaseProvider):
        def __init__(self, environment: str, application: str):
            super().__init__()

        def get(self, name: str, **kwargs) -> str:
            return mock_value

        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setattr(parameters.appconfig, "DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters.appconfig, "AppConfigProvider", TestProvider)

    # WHEN
    value = parameters.get_app_config(mock_name, environment="dev", application="myapp")

    # THEN
    assert parameters.appconfig.DEFAULT_PROVIDERS["appconfig"] is not None
    assert value == mock_value


def test_transform_value_json(mock_value):
    """
    Test transform_value() with a json transform
    """

    mock_data = json.dumps({"A": mock_value})

    value = parameters.base.transform_value(mock_data, "json")

    assert isinstance(value, dict)
    assert value["A"] == mock_value


def test_transform_value_json_exception(mock_value):
    """
    Test transform_value() with a json transform that fails
    """

    mock_data = json.dumps({"A": mock_value}) + "{"

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        parameters.base.transform_value(mock_data, "json")

    assert "Extra data" in str(excinfo)


def test_transform_value_binary(mock_value):
    """
    Test transform_value() with a binary transform
    """

    mock_binary = mock_value.encode()
    mock_data = base64.b64encode(mock_binary).decode()

    value = parameters.base.transform_value(mock_data, "binary")

    assert isinstance(value, bytes)
    assert value == mock_binary


def test_transform_value_binary_exception():
    """
    Test transform_value() with a binary transform that fails
    """

    mock_data = "qw"

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        parameters.base.transform_value(mock_data, "binary")

    assert "Incorrect padding" in str(excinfo)


def test_transform_value_wrong(mock_value):
    """
    Test transform_value() with an incorrect transform
    """

    with pytest.raises(parameters.TransformParameterError) as excinfo:
        parameters.base.transform_value(mock_value, "INCORRECT")

    assert "Invalid transform type" in str(excinfo)


def test_transform_value_ignore_error(mock_value):
    """
    Test transform_value() does not raise errors when raise_on_transform_error is False
    """

    value = parameters.base.transform_value(mock_value, "INCORRECT", raise_on_transform_error=False)

    assert value is None


@pytest.mark.parametrize("original_transform", ["json", "binary", "other", "Auto", None])
def test_get_transform_method_preserve_original(original_transform):
    """
    Check if original transform method is returned for anything other than "auto"
    """
    transform = parameters.base.get_transform_method("key", original_transform)

    assert transform == original_transform


@pytest.mark.parametrize("extension", ["json", "binary"])
def test_get_transform_method_preserve_auto(extension, mock_name):
    """
    Check if we can auto detect the transform method by the support extensions json / binary
    """
    transform = parameters.base.get_transform_method(f"{mock_name}.{extension}", "auto")

    assert transform == extension


@pytest.mark.parametrize("key", ["json", "binary", "example", "example.jsonp"])
def test_get_transform_method_preserve_auto_unhandled(key):
    """
    Check if any key that does not end with a supported extension returns None when
    using the transform="auto"
    """
    transform = parameters.base.get_transform_method(key, "auto")

    assert transform is None


def test_base_provider_get_multiple_force_update(mock_name, mock_value):
    """
    Test BaseProvider.get_multiple()  with cached values and force_fetch is True
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            raise NotImplementedError()

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            assert path == mock_name
            return {"A": mock_value}

    provider = TestProvider()

    provider.store[(mock_name, None)] = ExpirableValue({"B": mock_value}, datetime.now() + timedelta(seconds=60))

    value = provider.get_multiple(mock_name, force_fetch=True)

    assert isinstance(value, dict)
    assert value["A"] == mock_value


def test_base_provider_get_force_update(mock_name, mock_value):
    """
    Test BaseProvider.get()  with cached values and force_fetch is True
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    provider = TestProvider()

    provider.store[(mock_name, None)] = ExpirableValue("not-value", datetime.now() + timedelta(seconds=60))

    value = provider.get(mock_name, force_fetch=True)

    assert isinstance(value, str)
    assert value == mock_value
