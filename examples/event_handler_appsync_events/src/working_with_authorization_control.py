from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver
from aws_lambda_powertools.event_handler.events_appsync.exceptions import UnauthorizedException

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.on_publish("/default/foo")
def handle_specific_channel(payload: dict[str, Any]):
    return payload


@app.on_publish("/*")
def handle_root_channel(payload: dict[str, Any]):
    raise UnauthorizedException("You can only publish to /default/foo")


@app.on_subscribe("/default/foo")
def handle_subscription_specific_channel():
    return True


@app.on_subscribe("/*")
def handle_subscription_root_channel():
    raise UnauthorizedException("You can only subscribe to /default/foo")


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
