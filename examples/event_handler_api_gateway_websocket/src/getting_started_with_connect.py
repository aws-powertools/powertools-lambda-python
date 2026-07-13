from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayWebSocketResolver()


@app.on_connect()
def connect():
    if "Authorization" not in app.current_event.headers:  # (1)!
        return None, 401  # (2)!

    connection_id = app.current_event.request_context.connection_id
    logger.info("Connection accepted", connection_id=connection_id)
    return None  # (3)!


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
