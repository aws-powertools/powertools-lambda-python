from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayWebSocketResolver()


@app.exception_handler(ValueError)  # (1)!
def handle_invalid_message(exc: ValueError):
    logger.error(f"Invalid message: {exc}")
    return {"error": str(exc)}, 400  # (2)!


@app.route("orderUpdate")
def order_update():
    order = app.current_event.json_body
    if "orderId" not in order:
        raise ValueError("missing orderId")
    return {"orderId": order["orderId"], "status": "received"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
