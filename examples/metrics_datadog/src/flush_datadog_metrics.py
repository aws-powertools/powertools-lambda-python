from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = DatadogMetrics()


def book_flight(flight_id: str, **kwargs):
    # logic to book flight
    ...
    metrics.add_metric(name="SuccessfulBooking", value=1)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        book_flight(flight_id=event.get("flight_id", ""))
    finally:
        metrics.flush_metrics()
