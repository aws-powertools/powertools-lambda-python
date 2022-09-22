import time

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(expires_after_seconds=20)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):

    time_now = time.time()

    return {"time": str(time_now)}
