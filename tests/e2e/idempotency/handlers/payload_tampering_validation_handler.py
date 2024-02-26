import os
import uuid

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)

TABLE_NAME = os.getenv("IdempotencyTable", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=TABLE_NAME)
config = IdempotencyConfig(event_key_jmespath='["refund_id", "customer_id"]', payload_validation_jmespath="details")


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"request": str(uuid.uuid4())}
