from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    # Idempotency is guaranteed across all concurrent requests
    # DynamoDB handles the distributed locking
    return {"statusCode": 200, "body": "Order processed"}
