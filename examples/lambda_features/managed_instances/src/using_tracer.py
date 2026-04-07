from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
metrics = Metrics()


@tracer.capture_lambda_handler
@metrics.log_metrics
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    order_id = event.get("order_id", "unknown")
    logger.append_keys(order_id=order_id)

    result = process_order(order_id)

    # Metrics are flushed per request
    metrics.add_metric(name="OrderProcessed", unit=MetricUnit.Count, value=1)

    return {"statusCode": 200, "body": result}


@tracer.capture_method
def process_order(order_id: str) -> str:
    logger.info("Processing order")
    return f"Processed order {order_id}"
