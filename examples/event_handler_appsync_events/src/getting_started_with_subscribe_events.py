from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler import AppSyncEventsResolver  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.on_subscribe("/*")
def handle_all_subscriptions():
    path = app.current_event.info.channel_path

    # Perform access control checks
    if not is_authorized(path):
        raise Exception("You are not authorized to subscribe to this channel")

    return True


def is_authorized(path: str):
    # Your authorization logic here
    return path != "not_allowed_path_here"


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
