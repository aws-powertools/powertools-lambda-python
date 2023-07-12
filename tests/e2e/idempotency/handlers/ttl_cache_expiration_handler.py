import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)

TABLE_NAME = os.getenv("IdempotencyTable", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=TABLE_NAME)
config = IdempotencyConfig(expires_after_seconds=5)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    time_now = time.time()

    return {"time": str(time_now)}
