from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


def book_flight(flight_id: str, **kwargs): 
    # logic to book flight
    ...
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        book_flight(flight_id=event.get("flight_id", ""))
    finally:
        metrics.flush_metrics()
