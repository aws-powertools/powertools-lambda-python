from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.on_publish("/default/channel1")
def handle_specific_channel(payload: dict[str, Any]):
    # This handler will be called for events on /default/channel1
    return {"source": "specific_handler", "data": payload}


@app.on_publish("/default/*")
def handle_default_namespace(payload: dict[str, Any]):
    # This handler will be called for all channels in the default namespace
    # EXCEPT for /default/channel1 which has a more specific handler
    return {"source": "namespace_handler", "data": payload}


@app.on_publish("/*")
def handle_all_channels(payload: dict[str, Any]):
    # This handler will be called for all channels in all namespaces
    # EXCEPT for those that have more specific handlers
    return {"source": "catch_all_handler", "data": payload}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
