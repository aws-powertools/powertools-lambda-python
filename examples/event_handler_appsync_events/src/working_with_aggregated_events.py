from __future__ import annotations

from typing import TYPE_CHECKING, Any

import boto3
from boto3.dynamodb.types import TypeSerializer

from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

dynamodb = boto3.client("dynamodb")
serializer = TypeSerializer()
app = AppSyncEventsResolver()


def marshall(item: dict[str, Any]) -> dict[str, Any]:
    return {k: serializer.serialize(v) for k, v in item.items()}


@app.on_publish("/default/foo/*", aggregate=True)
async def handle_default_namespace_batch(payload: list[dict[str, Any]]):  # (1)!
    write_operations: list = []

    write_operations.extend({"PutRequest": {"Item": marshall(item)}} for item in payload)

    if write_operations:
        dynamodb.batch_write_item(
            RequestItems={
                "your-table-name": write_operations,
            },
        )

    return payload


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
