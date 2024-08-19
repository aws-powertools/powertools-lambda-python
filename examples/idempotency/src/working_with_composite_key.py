from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable", sort_key_attr="sort_key")


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    user_id: str = event.get("body", "")["user_id"]
    return {"message": "success", "user_id": user_id}
