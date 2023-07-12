from __future__ import annotations

import base64
import json
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Tuple

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from botocore import stub
from botocore.config import Config
from botocore.response import StreamingBody

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.parameters.base import (
    TRANSFORM_METHOD_MAPPING,
    BaseProvider,
    ExpirableValue,
)
from aws_lambda_powertools.utilities.parameters.ssm import SSMProvider


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


@pytest.fixture
def mock_binary_value() -> str:
    return "ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnpkV0lpT2lJeE1qTTBOVFkzT0Rrd0lpd2libUZ0WlNJNklrcHZhRzRnUkc5bElpd2lhV0YwSWpveE5URTJNak01TURJeWZRLlNmbEt4d1JKU01lS0tGMlFUNGZ3cE1lSmYzNlBPazZ5SlZfYWRRc3N3NWMK"  # noqa: E501


def build_get_parameters_stub(params: Dict[str, Any], invalid_parameters: List[str] | None = None) -> Dict[str, List]:
    invalid_parameters = invalid_parameters or []
    version = random.randrange(1, 1000)
    return {
        "Parameters": [
            {
                "Name": param,
                "Type": "String",
                "Value": value,
                "Version": version,
                "Selector": f"{param}:{version}",
                "SourceResult": "string",
                "LastModifiedDate": datetime(2015, 1, 1),
                "ARN": f"arn:aws:ssm:us-east-2:111122223333:parameter/{param.lstrip('/')}",
                "DataType": "string",
            }
            for param, value in params.items()
            if param not in invalid_parameters
        ],
        "InvalidParameters": invalid_parameters,  # official SDK stub fails validation here, need to raise an issue
    }


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


def test_dynamodb_provider_get_with_custom_client(mock_name, mock_value, config):
    """
    Test DynamoDBProvider.get() with SDK options
    """

    table_name = "TEST_TABLE"
    client = boto3.resource("dynamodb", config=config)
    table_resource_client = client.Table(table_name)

    # Create a new provider
    provider = parameters.DynamoDBProvider(table_name, boto3_client=client)

    # Stub the boto3 client
    stubber = stub.Stubber(provider.table.meta.client)
    response = {"Item": {"id": {"S": mock_name}, "value": {"S": mock_value}}}
    expected_params = {"TableName": table_name, "Key": {"id": mock_name}, "ConsistentRead": True}
    stubber.add_response("get_item", response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name, ConsistentRead=True)

        assert value == mock_value
        # confirm table resource client comes from the same custom client provided
        assert id(table_resource_client.meta.client) == id(provider.table.meta.client)
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
        ],
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
        ],
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
        ],
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
        ],
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
        ],
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
        },
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


def test_ssm_provider_get_with_custom_client(mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get() with a non-cached value
    """

    client = boto3.client("ssm", config=config)

    # Create a new provider
    provider = parameters.SSMProvider(boto3_client=client)

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
        },
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


def test_ssm_provider_get_with_decrypt_environment_variable(monkeypatch, mock_name, mock_value, mock_version, config):
    """
    Test SSMProvider.get() with decrypt value replaced by environment variable
    """

    # Setting environment variable to override the default value
    monkeypatch.setenv("POWERTOOLS_PARAMETERS_SSM_DECRYPT", "true")

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
        },
    }
    expected_params = {"Name": mock_name, "WithDecryption": True}
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
        },
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


def test_providers_global_clear_cache(mock_name, mock_value, monkeypatch):
    # GIVEN all providers are previously initialized
    # and parameters, secrets, and app config are fetched
    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            return mock_value

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            ...

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())
    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "secrets", TestProvider())
    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "appconfig", TestProvider())

    parameters.get_parameter(mock_name)
    parameters.get_secret(mock_name)
    parameters.get_app_config(name=mock_name, environment="test", application="test")

    # WHEN clear_caches is called
    parameters.clear_caches()

    # THEN all providers cache should be reset
    assert parameters.base.DEFAULT_PROVIDERS == {}


def test_ssm_provider_clear_cache(mock_name, mock_value, config):
    # GIVEN a provider is initialized with a cached value
    provider = parameters.SSMProvider(config=config)
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # WHEN clear_cache is called from within the provider instance
    provider.clear_cache()

    # THEN store should be empty
    assert provider.store == {}


def test_ssm_provider_get_parameters_by_name_raise_on_failure(mock_name, mock_value, config):
    # GIVEN two parameters are requested
    provider = parameters.SSMProvider(config=config)
    success = f"/dev/{mock_name}"
    fail = f"/prod/{mock_name}"

    params = {success: {}, fail: {}}
    param_names = list(params.keys())
    stub_params = {success: mock_value}

    expected_stub_response = build_get_parameters_stub(params=stub_params, invalid_parameters=[fail])
    expected_stub_params = {"Names": param_names}

    stubber = stub.Stubber(provider.client)
    stubber.add_response("get_parameters", expected_stub_response, expected_stub_params)
    stubber.activate()

    # WHEN one of them fails to be retrieved
    # THEN raise GetParameterError
    with pytest.raises(parameters.exceptions.GetParameterError, match=f"Failed to fetch parameters: .*{fail}.*"):
        try:
            provider.get_parameters_by_name(parameters=params)
            stubber.assert_no_pending_responses()
        finally:
            stubber.deactivate()


def test_ssm_provider_get_parameters_by_name_do_not_raise_on_failure(mock_name, mock_value, config):
    # GIVEN two parameters are requested
    success = f"/dev/{mock_name}"
    fail = f"/prod/{mock_name}"
    params = {success: {}, fail: {}}
    param_names = list(params.keys())
    stub_params = {success: mock_value}

    expected_stub_response = build_get_parameters_stub(params=stub_params, invalid_parameters=[fail])
    expected_stub_params = {"Names": param_names}

    provider = parameters.SSMProvider(config=config)
    stubber = stub.Stubber(provider.client)
    stubber.add_response("get_parameters", expected_stub_response, expected_stub_params)
    stubber.activate()

    # WHEN one of them fails to be retrieved
    try:
        ret = provider.get_parameters_by_name(parameters=params, raise_on_error=False)

        # THEN there should be no error raised
        # and failed ones available within "_errors" key
        stubber.assert_no_pending_responses()
        assert ret["_errors"]
        assert len(ret["_errors"]) == 1
        assert fail not in ret
    finally:
        stubber.deactivate()


def test_ssm_provider_get_parameters_by_name_do_not_raise_on_failure_with_decrypt(mock_name, config):
    # GIVEN one parameter requires decryption and an arbitrary SDK error occurs
    param = f"/{mock_name}"
    params = {param: {"decrypt": True}}

    provider = parameters.SSMProvider(config=config)
    stubber = stub.Stubber(provider.client)
    stubber.add_client_error("get_parameters", "InvalidKeyId")
    stubber.activate()

    # WHEN fail-fast is disabled in get_parameters_by_name
    try:
        ret = provider.get_parameters_by_name(parameters=params, raise_on_error=False)
        stubber.assert_no_pending_responses()

        # THEN there should be no error raised but added under `_errors` key
        assert ret["_errors"]
        assert len(ret["_errors"]) == 1
        assert param not in ret
    finally:
        stubber.deactivate()


def test_ssm_provider_get_parameters_by_name_do_not_raise_on_failure_batch_decrypt_combined(
    mock_value,
    mock_version,
    config,
):
    # GIVEN three parameters are requested
    # one requires decryption, two can be batched
    # and an arbitrary SDK error is injected
    fail = "/fail"
    success = "/success"
    decrypt_fail = "/fail/decrypt"
    params = {decrypt_fail: {"decrypt": True}, success: {}, fail: {}}

    expected_stub_params = {"Names": [success, fail]}
    expected_stub_response = build_get_parameters_stub(
        params={fail: mock_value, success: mock_value},
        invalid_parameters=[fail],
    )

    provider = parameters.SSMProvider(config=config)
    stubber = stub.Stubber(provider.client)
    stubber.add_client_error("get_parameter")
    stubber.add_response("get_parameters", expected_stub_response, expected_stub_params)
    stubber.activate()

    # WHEN fail-fast is disabled in get_parameters_by_name
    # and only one parameter succeeds out of three
    try:
        ret = provider.get_parameters_by_name(parameters=params, raise_on_error=False)

        # THEN there should be no error raised
        # successful params returned accordingly
        # and failed ones available within "_errors" key
        stubber.assert_no_pending_responses()
        assert success in ret
        assert ret["_errors"]
        assert len(ret["_errors"]) == 2
        assert fail not in ret
        assert decrypt_fail not in ret
    finally:
        stubber.deactivate()


def test_ssm_provider_get_parameters_by_name_raise_on_reserved_errors_key(mock_name, mock_value, config):
    # GIVEN one of the parameters is named `_errors`
    success = f"/dev/{mock_name}"
    fail = "_errors"

    params = {success: {}, fail: {}}
    provider = parameters.SSMProvider(config=config)

    # WHEN using get_parameters_by_name to fetch
    # THEN raise GetParameterError
    with pytest.raises(parameters.exceptions.GetParameterError, match="You cannot fetch a parameter named"):
        provider.get_parameters_by_name(parameters=params, raise_on_error=False)


def test_ssm_provider_get_parameters_by_name_all_decrypt_should_use_get_parameters_api(mock_name, mock_value, config):
    # GIVEN all parameters require decryption
    param_a = f"/a/{mock_name}"
    param_b = f"/b/{mock_name}"
    fail = "/does_not_exist"  # stub model doesn't support all-success yet

    all_params = {param_a: {}, param_b: {}, fail: {}}
    all_params_names = list(all_params.keys())

    expected_param_values = {param_a: mock_value, param_b: mock_value}
    expected_stub_response = build_get_parameters_stub(params=expected_param_values, invalid_parameters=[fail])
    expected_stub_params = {"Names": all_params_names, "WithDecryption": True}

    provider = parameters.SSMProvider(config=config)
    stubber = stub.Stubber(provider.client)
    stubber.add_response("get_parameters", expected_stub_response, expected_stub_params)
    stubber.activate()

    # WHEN get_parameters_by_name is called
    # THEN we should only use GetParameters WithDecryption=true to prevent throttling
    try:
        ret = provider.get_parameters_by_name(parameters=all_params, decrypt=True, raise_on_error=False)
        stubber.assert_no_pending_responses()

        assert ret is not None
    finally:
        stubber.deactivate()


def test_dynamodb_provider_clear_cache(mock_name, mock_value, config):
    # GIVEN a provider is initialized with a cached value
    provider = parameters.DynamoDBProvider(table_name="test", config=config)
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # WHEN clear_cache is called from within the provider instance
    provider.clear_cache()

    # THEN store should be empty
    assert provider.store == {}


def test_secrets_provider_clear_cache(mock_name, mock_value, config):
    # GIVEN a provider is initialized with a cached value
    provider = parameters.SecretsProvider(config=config)
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # WHEN clear_cache is called from within the provider instance
    provider.clear_cache()

    # THEN store should be empty
    assert provider.store == {}


def test_appconf_provider_clear_cache(mock_name, config):
    # GIVEN a provider is initialized with a cached value
    provider = parameters.AppConfigProvider(environment="test", application="test", config=config)
    provider.store[(mock_name, None)] = ExpirableValue(mock_value, datetime.now() + timedelta(seconds=60))

    # WHEN clear_cache is called from within the provider instance
    provider.clear_cache()

    # THEN store should be empty
    assert provider.store == {}


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
        },
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
        },
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
        ],
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
        ],
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
        ],
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
        ],
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
        ],
    }
    expected_params = {"Path": mock_name, "Recursive": False, "WithDecryption": False}
    stubber.add_response("get_parameters_by_path", response, expected_params)
    stubber.activate()

    try:
        values = provider.get_multiple(
            mock_name,
            Path="THIS_SHOULD_BE_OVERWRITTEN",
            Recursive=False,
            WithDecryption=True,
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


def test_secrets_provider_get_binary_secret(mock_name, mock_binary_value, config):
    # GIVEN a new provider
    provider = parameters.SecretsProvider(config=config)
    expected_params = {"SecretId": mock_name}
    expected_response = {
        "ARN": f"arn:aws:secretsmanager:us-east-1:132456789012:secret/{mock_name}",
        "Name": mock_name,
        "VersionId": "edc66e31-3d5f-4276-aaa1-95ed44cfed72",
        "SecretBinary": mock_binary_value,
        "CreatedDate": datetime(2015, 1, 1),
    }

    stubber = stub.Stubber(provider.client)
    stubber.add_response("get_secret_value", expected_response, expected_params)
    stubber.activate()

    try:
        value = provider.get(mock_name)
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()

    assert value == mock_binary_value


def test_secrets_provider_get_with_custom_client(mock_name, mock_value, config):
    """
    Test SecretsProvider.get() with a non-cached value
    """
    client = boto3.client("secretsmanager", config=config)

    # Create a new provider
    provider = parameters.SecretsProvider(boto3_client=client)

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


def test_get_parameters_by_name(monkeypatch, mock_name, mock_value, config):
    params = {mock_name: {}}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        def get_parameters_by_name(self, *args, **kwargs) -> Dict[str, str] | Dict[str, bytes] | Dict[str, dict]:
            return {mock_name: mock_value}

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    values = parameters.get_parameters_by_name(parameters=params)

    assert len(values) == 1
    assert values[mock_name] == mock_value


def test_get_parameters_by_name_with_decrypt_override(monkeypatch, mock_name, mock_value, config):
    # GIVEN 2 out of 3 parameters have decrypt override
    decrypt_param = "/api_key"
    decrypt_param_two = "/another/secret"
    decrypt_params = {decrypt_param: {"decrypt": True}, decrypt_param_two: {"decrypt": True}}
    decrypted_response = "decrypted"
    params = {mock_name: {}, **decrypt_params}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        def _get(self, name: str, decrypt: bool = False, **sdk_options) -> str:
            # THEN params with `decrypt` override should use GetParameter` (`_get`)
            assert name in decrypt_params
            assert decrypt
            return decrypted_response

        def _get_parameters_by_name(self, *args, **kwargs) -> Tuple[Dict[str, Any], List[str]]:
            return {mock_name: mock_value}, []

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    # WHEN get_parameters_by_name is called
    values = parameters.get_parameters_by_name(parameters=params)

    # THEN all parameters should be merged in the response
    assert len(values) == 3
    assert values[mock_name] == mock_value
    assert values[decrypt_param] == decrypted_response
    assert values[decrypt_param_two] == decrypted_response


def test_get_parameters_by_name_with_override_and_explicit_global(monkeypatch, mock_name, mock_value, config):
    # GIVEN a parameter overrides a default setting
    default_cache_period = 500
    params = {mock_name: {"max_age": 0}, "no-override": {}}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        # NOTE: By convention, we check at `_get_parameters_by_name`
        # as that's right before we call SSM, and when options have been merged
        # def _get_parameters_by_name(self, parameters: Dict[str, Dict], raise_on_error: bool = True) -> Dict[str, Any]:
        def _get_parameters_by_name(
            self,
            parameters: Dict[str, Dict],
            raise_on_error: bool = True,
            decrypt: bool = False,
        ) -> Tuple[Dict[str, Any], List[str]]:
            # THEN max_age should use no_cache_param override
            assert parameters[mock_name]["max_age"] == 0
            assert parameters["no-override"]["max_age"] == default_cache_period

            return {mock_name: mock_value}, []

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    # WHEN get_parameters_by_name is called with max_age set to 500 as the default
    parameters.get_parameters_by_name(parameters=params, max_age=default_cache_period)


def test_get_parameters_by_name_with_max_batch(monkeypatch, config):
    # GIVEN a batch of 20 parameters
    params = {f"param_{i}": {} for i in range(20)}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        def _get_parameters_by_name(
            self,
            parameters: Dict[str, Dict],
            raise_on_error: bool = True,
            decrypt: bool = False,
        ) -> Tuple[Dict[str, Any], List[str]]:
            # THEN we should always split to respect GetParameters max
            assert len(parameters) == self._MAX_GET_PARAMETERS_ITEM
            return {}, []

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    # WHEN get_parameters_by_name is called
    parameters.get_parameters_by_name(parameters=params)


def test_get_parameters_by_name_cache(monkeypatch, mock_name, mock_value, config):
    # GIVEN we have a parameter to fetch but is already in cache
    params = {mock_name: {}}
    cache_key = (mock_name, None)

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        def _get_parameters_by_name(self, *args, **kwargs) -> Tuple[Dict[str, Any], List[str]]:
            raise RuntimeError("Should not be called if it's in cache")

    provider = TestProvider()
    provider.add_to_cache(key=(mock_name, None), value=mock_value, max_age=10)

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", provider)

    # WHEN get_parameters_by_name is called
    provider.get_parameters_by_name(parameters=params)

    # THEN the cache should be used and _get_parameters_by_name should not be called
    assert provider.has_not_expired_in_cache(key=cache_key)


def test_get_parameters_by_name_empty_batch(monkeypatch, config):
    # GIVEN we have an empty dictionary
    params = {}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", TestProvider())

    # WHEN get_parameters_by_name is called
    # THEN it should return an empty response
    assert parameters.get_parameters_by_name(parameters=params) == {}


def test_get_parameters_by_name_cache_them_individually_not_batch(monkeypatch, mock_name, mock_version):
    # GIVEN we have a parameter to fetch but is already in cache
    dev_param = f"/dev/{mock_name}"
    prod_param = f"/prod/{mock_name}"
    params = {dev_param: {}, prod_param: {}}

    stub_params = {dev_param: mock_value, prod_param: mock_value}
    stub_response = build_get_parameters_stub(params=stub_params)

    class FakeClient:
        def get_parameters(self, *args, **kwargs):
            return stub_response

    provider = SSMProvider(boto3_client=FakeClient())
    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "ssm", provider)

    # WHEN get_parameters_by_name is called
    provider.get_parameters_by_name(parameters=params)

    # THEN the cache should be populated with each parameter
    assert len(provider.store) == len(params)


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


def test_get_parameters_by_name_new(monkeypatch, mock_name, mock_value, config):
    """
    Test get_parameters_by_name() without a default provider
    """
    params = {mock_name: {}}

    class TestProvider(SSMProvider):
        def __init__(self, config: Config = config, **kwargs):
            super().__init__(config, **kwargs)

        def get_parameters_by_name(self, *args, **kwargs) -> Dict[str, str] | Dict[str, bytes] | Dict[str, dict]:
            return {mock_name: mock_value}

    monkeypatch.setattr(parameters.ssm, "DEFAULT_PROVIDERS", {})
    monkeypatch.setattr(parameters.ssm, "SSMProvider", TestProvider)

    value = parameters.get_parameters_by_name(params)

    assert value[mock_name] == mock_value


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

    stubber = stub.Stubber(provider.client)
    response_start_config_session = {"InitialConfigurationToken": "initial_token"}
    stubber.add_response("start_configuration_session", response_start_config_session)

    response_get_latest_config = {
        "Configuration": mock_value,
        "NextPollConfigurationToken": "initial_token",
        "ContentType": "application/json",
    }
    stubber.add_response("get_latest_configuration", response_get_latest_config)
    stubber.activate()

    try:
        value = provider.get(
            mock_name,
            transform="json",
            ApplicationIdentifier=application,
            EnvironmentIdentifier=environment,
        )

        assert value == mock_body_json
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_appconf_provider_get_configuration_json_content_type_with_custom_client(mock_name, config):
    """
    Test get_configuration.get with default values
    """

    client = boto3.client("appconfigdata", config=config)

    # Create a new provider
    environment = "dev"
    application = "myapp"
    provider = parameters.AppConfigProvider(environment=environment, application=application, boto3_client=client)

    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    encoded_message = json.dumps(mock_body_json).encode("utf-8")
    mock_value = StreamingBody(BytesIO(encoded_message), len(encoded_message))

    stubber = stub.Stubber(provider.client)
    response_start_config_session = {"InitialConfigurationToken": "initial_token"}
    stubber.add_response("start_configuration_session", response_start_config_session)

    response_get_latest_config = {
        "Configuration": mock_value,
        "NextPollConfigurationToken": "initial_token",
        "ContentType": "application/json",
    }
    stubber.add_response("get_latest_configuration", response_get_latest_config)
    stubber.activate()

    try:
        value = provider.get(
            mock_name,
            transform="json",
            ApplicationIdentifier=application,
            EnvironmentIdentifier=environment,
        )

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

    stubber = stub.Stubber(provider.client)
    response_start_config_session = {"InitialConfigurationToken": "initial_token"}
    stubber.add_response("start_configuration_session", response_start_config_session)

    response_get_latest_config = {
        "Configuration": mock_value,
        "NextPollConfigurationToken": "initial_token",
        "ContentType": "application/json",
    }
    stubber.add_response("get_latest_configuration", response_get_latest_config)
    stubber.activate()

    try:
        value: bytes = provider.get(mock_name)
        str_value = value.decode("utf-8")
        assert str_value == json.dumps(mock_body_json)
        stubber.assert_no_pending_responses()
    finally:
        stubber.deactivate()


def test_appconf_provider_multiple_unique_config_names(mock_name, config):
    """
    Test appconfig_provider.get with multiple config names
    """

    # GIVEN a provider instance, we should be able to retrieve multiple appconfig profiles.
    environment = "dev"
    application = "myapp"
    provider = parameters.AppConfigProvider(environment=environment, application=application, config=config)

    mock_body_json_first_call = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    encoded_message_first_call = json.dumps(mock_body_json_first_call).encode("utf-8")
    mock_value_first_call = StreamingBody(BytesIO(encoded_message_first_call), len(encoded_message_first_call))

    mock_body_json_second_call = {"myenvvar1": "Thor", "myenvvar2": 5}
    encoded_message_second_call = json.dumps(mock_body_json_second_call).encode("utf-8")
    mock_value_second_call = StreamingBody(BytesIO(encoded_message_second_call), len(encoded_message_second_call))

    # WHEN making two API calls using the same provider instance.
    stubber = stub.Stubber(provider.client)

    response_get_latest_config_first_call = {
        "Configuration": mock_value_first_call,
        "NextPollConfigurationToken": "initial_token",
        "ContentType": "application/json",
    }

    response_start_config_session = {"InitialConfigurationToken": "initial_token"}
    stubber.add_response("start_configuration_session", response_start_config_session)
    stubber.add_response("get_latest_configuration", response_get_latest_config_first_call)

    response_get_latest_config_second_call = {
        "Configuration": mock_value_second_call,
        "NextPollConfigurationToken": "initial_token",
        "ContentType": "application/json",
    }
    response_start_config_session = {"InitialConfigurationToken": "initial_token"}
    stubber.add_response("start_configuration_session", response_start_config_session)
    stubber.add_response("get_latest_configuration", response_get_latest_config_second_call)

    stubber.activate()

    try:
        # THEN we should expect different return values.
        value_first_call: bytes = provider.get(mock_name)
        value_second_call: bytes = provider.get(f"{mock_name}_ second_config")

        assert value_first_call != value_second_call
        stubber.assert_no_pending_responses()

    finally:
        stubber.deactivate()


def test_appconf_get_app_config_no_transform(monkeypatch, mock_name):
    """
    Test get_app_config()
    """
    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    mock_body_bytes = str.encode(json.dumps(mock_body_json))

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> bytes:
            assert name == mock_name
            return mock_body_bytes

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "appconfig", TestProvider())

    environment = "dev"
    application = "myapp"
    value = parameters.get_app_config(mock_name, environment=environment, application=application)
    str_value = value.decode("utf-8")
    assert str_value == json.dumps(mock_body_json)
    assert value == mock_body_bytes


def test_appconf_get_app_config_transform_json(monkeypatch, mock_name):
    """
    Test get_app_config()
    """
    mock_body_json = {"myenvvar1": "Black Panther", "myenvvar2": 3}
    mock_body_bytes = str.encode(json.dumps(mock_body_json))

    class TestProvider(BaseProvider):
        def _get(self, name: str, **kwargs) -> str:
            assert name == mock_name
            return mock_body_bytes

        def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
            raise NotImplementedError()

    monkeypatch.setitem(parameters.base.DEFAULT_PROVIDERS, "appconfig", TestProvider())

    environment = "dev"
    application = "myapp"
    value = parameters.get_app_config(mock_name, environment=environment, application=application, transform="json")
    assert value == mock_body_json


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


def test_transform_value_auto(mock_value: str):
    # GIVEN
    json_data = json.dumps({"A": mock_value})
    mock_binary = mock_value.encode()
    binary_data = base64.b64encode(mock_binary).decode()

    # WHEN
    json_value = parameters.base.transform_value(key="/a.json", value=json_data, transform="auto")
    binary_value = parameters.base.transform_value(key="/a.binary", value=binary_data, transform="auto")

    # THEN
    assert isinstance(json_value, dict)
    assert isinstance(binary_value, bytes)
    assert json_value["A"] == mock_value
    assert binary_value == mock_binary


def test_transform_value_auto_incorrect_key(mock_value: str):
    # GIVEN
    mock_key = "/missing/json/suffix"
    json_data = json.dumps({"A": mock_value})

    # WHEN
    value = parameters.base.transform_value(key=mock_key, value=json_data, transform="auto")

    # THEN it should echo back its value
    assert isinstance(value, str)
    assert value == json_data


def test_transform_value_auto_unsupported_transform(mock_value: str):
    # GIVEN
    mock_key = "/a.does_not_exist"
    mock_dict = {"hello": "world"}

    # WHEN
    value = parameters.base.transform_value(key=mock_key, value=mock_value, transform="auto")
    dict_value = parameters.base.transform_value(key=mock_key, value=mock_dict, transform="auto")

    # THEN it should echo back its value
    assert value == mock_value
    assert dict_value == mock_dict


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


def test_transform_value_ignore_error(mock_value):
    """
    Test transform_value() does not raise errors when raise_on_transform_error is False
    """

    value = parameters.base.transform_value(mock_value, "INCORRECT", raise_on_transform_error=False)

    assert value is None


@pytest.mark.parametrize("extension", ["json", "binary"])
def test_get_transform_method_preserve_auto(extension, mock_name):
    """
    Check if we can auto detect the transform method by the support extensions json / binary
    """
    transform = parameters.base.get_transform_method(f"{mock_name}.{extension}", "auto")

    assert transform == TRANSFORM_METHOD_MAPPING[extension]


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


def test_cache_ignores_max_age_zero_or_negative(mock_value, config):
    # GIVEN we have two parameters that shouldn't be cached
    param = "/no_cache"
    provider = SSMProvider(config=config)
    cache_key = (param, None)

    # WHEN a provider adds them into the cache
    provider.add_to_cache(key=cache_key, value=mock_value, max_age=0)
    provider.add_to_cache(key=cache_key, value=mock_value, max_age=-10)

    # THEN they should not be added to the cache
    assert len(provider.store) == 0
    assert provider.has_not_expired_in_cache(cache_key) is False
