from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEventsEvent

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.on_publish("/default/channel1")
def handle_channel1_publish(payload: dict[str, Any]):
    # Access the full event and context
    lambda_event: AppSyncResolverEventsEvent = app.current_event

    # Access request headers
    header_user_agent = lambda_event.request_headers["user-agent"]

    return {
        "originalMessage": payload,
        "userAgent": header_user_agent,
    }


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
