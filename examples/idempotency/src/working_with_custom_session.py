import boto3

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

# See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#module-boto3.session
boto3_session = boto3.session.Session()

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable", boto3_session=boto3_session)

config = IdempotencyConfig(event_key_jmespath="body")


@idempotent(persistence_store=persistence_layer, config=config)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
