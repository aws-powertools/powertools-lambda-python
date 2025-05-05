from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()
logger = Logger()


class ChannelException(Exception):
    pass


@app.on_publish("/default/*", aggregate=True)
def handle_default_namespace_batch(payload: list[dict[str, Any]]):
    results: list = []

    # Process all events in the batch together
    for event in payload:
        try:
            # Process each event
            results.append({"id": event.get("id"), "payload": {"processed": True, "originalEvent": event}})
        except Exception as e:
            logger.error("Found and error")
            raise ChannelException("An exception occurred") from e

    return results


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
