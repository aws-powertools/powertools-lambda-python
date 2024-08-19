from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(
    table_name="IdempotencyTable",
    key_attr="idempotency_key",
    expiry_attr="expires_at",
    in_progress_expiry_attr="in_progress_expires_at",
    status_attr="current_status",
    data_attr="result_data",
    validation_key_attr="validation_key",
)


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
