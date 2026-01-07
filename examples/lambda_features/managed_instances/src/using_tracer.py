from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    order_id = event.get("order_id", "unknown")
    result = process_order(order_id)
    return {"statusCode": 200, "body": result}


@tracer.capture_method
def process_order(order_id: str) -> str:
    # Each concurrent request creates its own trace
    return f"Processed order {order_id}"
