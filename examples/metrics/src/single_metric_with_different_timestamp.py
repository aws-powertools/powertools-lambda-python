from aws_lambda_powertools import Logger, single_metric
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext):

    for record in event:

        record_id: str = record.get("record_id")
        amount: int = record.get("amount")
        timestamp: int = record.get("timestamp")

        with single_metric(name="Orders", unit=MetricUnit.Count, value=amount, namespace="Powertools") as metric:
            logger.info(f"Processing record id {record_id}")
            metric.set_timestamp(timestamp)
