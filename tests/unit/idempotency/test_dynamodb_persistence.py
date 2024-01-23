from dataclasses import dataclass

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer
from tests.e2e.utils.data_builder.common import build_random_value


def test_custom_sdk_client_injection():
    # GIVEN
    @dataclass
    class DummyClient:
        table_name: str

    table_name = build_random_value()
    fake_client = DummyClient(table_name)

    # WHEN
    persistence_layer = DynamoDBPersistenceLayer(table_name, boto3_client=fake_client)

    # THEN
    assert persistence_layer.table_name == table_name
    assert persistence_layer.client == fake_client


def test_boto3_version_supports_condition_check_failure():
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("0.0.3") is False
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.25") is False
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.25") is False
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.26.163") is False
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.26.164") is True
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.26.165") is True
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("1.27.0") is True
    assert DynamoDBPersistenceLayer.boto3_supports_condition_check_failure("2.0.0") is True
