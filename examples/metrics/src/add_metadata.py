from uuid import uuid4

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="booking_id", value=f"{uuid4()}")
