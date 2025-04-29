from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.event_handler import AppSyncEventsResolver
from aws_lambda_powertools.event_handler.events_appsync.exceptions import UnauthorizedException
from aws_lambda_powertools.metrics import MetricUnit

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()
metrics = Metrics(namespace="AppSyncEvents", service="GettingStartedWithSubscribeEvents")


@app.on_subscribe("/*")
def handle_all_subscriptions():
    path = app.current_event.info.channel_path

    # Perform access control checks
    if not is_authorized(path):
        raise UnauthorizedException("You are not authorized to subscribe to this channel")

    metrics.add_dimension(name="channel", value=path)
    metrics.add_metric(name="subscription", unit=MetricUnit.Count, value=1)

    return True


def is_authorized(path: str):
    # Your authorization logic here
    return path != "not_allowed_path_here"


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
