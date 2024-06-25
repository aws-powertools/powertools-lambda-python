import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("IDEMPOTENCY_TABLE")
persistence_layer = DynamoDBPersistenceLayer(table_name=table)
config = IdempotencyConfig(
    event_key_jmespath="body",
    expires_after_seconds=24 * 60 * 60,  # 24 hours
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context: LambdaContext):
    return event
