import base64
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict

import pytest
from boto3.dynamodb.conditions import Key
from botocore import stub

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


def test_dynamodb_provider_get(mock_name, mock_value):
    """
    Test DynamoDBProvider.get() with a non-cached value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, region="us-east-1")

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


def test_dynamodb_provider_get_default_region(monkeypatch, mock_name, mock_value):
    """
    Test DynamoDBProvider.get() without setting a region
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


def test_dynamodb_provider_get_cached(mock_name, mock_value):
    """
    Test DynamoDBProvider.get() with a cached value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, region="us-east-1")

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


def test_dynamodb_provider_get_expired(mock_name, mock_value):
    """
    Test DynamoDBProvider.get() with a cached but expired value
    """

    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, region="us-east-1")

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


def test_dynamodb_provider_get_multiple(mock_name, mock_value):
    """
    Test DynamoDBProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, region="us-east-1")

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


def test_dynamodb_provider_get_multiple_next_token(mock_name, mock_value):
    """
    Test DynamoDBProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]
    table_name = "TEST_TABLE"

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, region="us-east-1")

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


def test_ssm_provider_get(mock_name, mock_value, mock_version):
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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_default_region(monkeypatch, mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get() without specifying the region
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


def test_ssm_provider_get_cached(mock_name, mock_value):
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


def test_ssm_provider_get_expired(mock_name, mock_value, mock_version):
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
    expected_params = {"Name": mock_name, "WithDecryption": False}
    stubber.add_response("get_parameter", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)

        assert value == mock_value
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_ssm_provider_get_multiple(mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get_multiple() with a non-cached path
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

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


def test_ssm_provider_get_multiple_different_path(mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get_multiple() with a non-cached path and names that don't start with the path
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

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


def test_ssm_provider_get_multiple_next_token(mock_name, mock_value, mock_version):
    """
    Test SSMProvider.get_multiple() with a non-cached path with multiple calls
    """

    mock_param_names = ["A", "B", "C"]

    # Create a new provider
    provider = parameters.SSMProvider(region="us-east-1")

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


def test_secrets_provider_get(mock_name, mock_value):
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


def test_secrets_provider_get_default_region(monkeypatch, mock_name, mock_value):
    """
    Test SecretsProvider.get() without specifying a region
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


def test_secrets_provider_get_cached(mock_name, mock_value):
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


def test_secrets_provider_get_expired(mock_name, mock_value):
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

    monkeypatch.setitem(parameters._DEFAULT_PROVIDERS, "ssm", TestProvider())

    value = parameters.get_parameter(mock_name)

    assert value == mock_value


def test_get_parameter_new(monkeypatch, mock_name, mock_value):
    """
    Test get_parameter() without a default provider
    """

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setattr(parameters, "_DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters, "SSMProvider", TestProvider)

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

    monkeypatch.setitem(parameters._DEFAULT_PROVIDERS, "ssm", TestProvider())

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
            return mock_value

    monkeypatch.setattr(parameters, "_DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters, "SSMProvider", TestProvider)

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

    monkeypatch.setitem(parameters._DEFAULT_PROVIDERS, "secrets", TestProvider())

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

    monkeypatch.setattr(parameters, "_DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters, "SecretsProvider", TestProvider)

    value = parameters.get_secret(mock_name)

    assert value == mock_value
