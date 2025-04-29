from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.on_publish("/default/channel")
def handle_channel1_publish(payload: dict[str, Any]):  # (1)!
    # Process the payload for this specific channel
    return {
        "processed": True,
        "original_payload": payload,
    }


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
