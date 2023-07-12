import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

TABLE_NAME = os.getenv("IdempotencyTable", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=TABLE_NAME)


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event, context):
    time.sleep(5)

    return event
