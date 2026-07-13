from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayWebSocketResolver()


@app.route("orderUpdate")
def order_update():
    identity = app.current_event.request_context.authorizer  # (1)!
    order = app.current_event.json_body
    return {
        "orderId": order["orderId"],
        "status": "received",
        "processedFor": identity["principalId"],
        "tenant": identity.get("tenantId"),  # (2)!
    }


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
