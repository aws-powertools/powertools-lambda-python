from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


class ValidationError(Exception):
    pass


@app.on_publish("/default/channel")
def handle_channel1_publish(payload: dict[str, Any]):
    if not is_valid_payload(payload):
        raise ValidationError("Invalid payload format")

    return {"processed": payload["data"]}


def is_valid_payload(payload: dict[str, Any]):
    return "data" in payload


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
