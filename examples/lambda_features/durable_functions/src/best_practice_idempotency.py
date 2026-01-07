from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    idempotent,
)

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(persistence_store=persistence_layer)
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    # Protected against duplicate SQS/Kinesis/DynamoDB triggers

    result: str = context.step(
        lambda _: "processed",
        name="process",
    )

    return result
