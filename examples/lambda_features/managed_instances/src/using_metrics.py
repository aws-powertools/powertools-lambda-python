from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()
logger = Logger()


@metrics.log_metrics
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    # Metrics are flushed per request
    metrics.add_metric(name="OrderProcessed", unit=MetricUnit.Count, value=1)

    return {"statusCode": 200}
