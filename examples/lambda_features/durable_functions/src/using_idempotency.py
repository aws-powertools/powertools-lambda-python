from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


def process_order(event: dict) -> str:
    return f"processed-{event.get('order_id')}"


@idempotent(persistence_store=persistence_layer)
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    # Idempotency protects against duplicate ESM invocations
    # Steps within the workflow are already idempotent via checkpoints

    result: str = context.step(
        lambda _: process_order(event),
        name="process_order",
    )

    return result
