from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayWebSocketResolver()


@app.route("orderUpdate")  # (1)!
def order_update():
    order = app.current_event.json_body
    return {"orderId": order["orderId"], "status": "received"}


@app.on_default()  # (2)!
def default():
    return {"error": "unknown action"}, 400


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
