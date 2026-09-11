from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayWebSocketResolver()


def log_route(app, next_middleware):  # (1)!
    logger.info("Dispatching", route_key=app.current_event.request_context.route_key)
    return next_middleware(app)  # (2)!


def enforce_order_limit(app, next_middleware):
    order = app.current_event.json_body
    if order.get("quantity", 0) > 100:
        return {"error": "quantity over limit"}, 400  # (3)!
    return next_middleware(app)


app.use(middlewares=[log_route])  # (4)!


@app.route("orderUpdate", middlewares=[enforce_order_limit])  # (5)!
def order_update():
    order = app.current_event.json_body
    return {"orderId": order["orderId"], "status": "received"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
