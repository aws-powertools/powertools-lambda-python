from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver  # type: ignore[attr-defined]
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEventsEvent  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


class ValidationError(Exception):
    pass


@app.on_publish("/default/channel1")
def handle_channel1_publish(payload: dict[str, Any]):
    # Access the full event and context
    lambda_event: AppSyncResolverEventsEvent = app.current_event
    lambda_context: LambdaContext = app.context

    # Access request headers
    headers = lambda_event.get("request", {}).get("headers", {})

    # Check remaining time
    remaining_time = lambda_context.get_remaining_time_in_millis()

    return {
        "originalMessage": payload,
        "userAgent": headers.get("User-Agent"),
        "timeRemaining": remaining_time,
    }


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
