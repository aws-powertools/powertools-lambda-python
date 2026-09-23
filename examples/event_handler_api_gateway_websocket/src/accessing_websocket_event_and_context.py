from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayWebSocketResolver()


@app.on_default()
def default():
    request_context = app.current_event.request_context  # (1)!
    return {
        "connectionId": request_context.connection_id,
        "routeKey": request_context.route_key,
        "message": app.current_event.json_body,  # (2)!
        "remainingTimeMs": app.lambda_context.get_remaining_time_in_millis(),  # (3)!
    }


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
