from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext):
    print("expensive operation")
    return {
        "payment_id": 12345,
        "message": "success",
        "statusCode": 200,
    }
