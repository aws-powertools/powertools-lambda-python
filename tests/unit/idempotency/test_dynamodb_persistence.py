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
