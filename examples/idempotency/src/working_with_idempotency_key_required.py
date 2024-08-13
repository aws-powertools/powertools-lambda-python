from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(
    event_key_jmespath='["user.uid", "order_id"]',
    raise_on_no_idempotency_key=True,
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
