import time

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(expires_after_seconds=1)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):

    sleep_time: int = event.get("sleep") or 0
    time.sleep(sleep_time)

    return event
