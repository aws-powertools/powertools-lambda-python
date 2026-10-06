import working_with_router_orders

from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayWebSocketResolver()
app.include_router(working_with_router_orders.router)  # (1)!


@app.on_connect()
def connect():
    return None


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
