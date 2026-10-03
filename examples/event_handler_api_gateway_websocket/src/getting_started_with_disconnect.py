from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayWebSocketResolver()


@app.on_disconnect()
def disconnect():  # (1)!
    request_context = app.current_event.request_context
    logger.info(
        "Connection closed",
        connection_id=request_context.connection_id,
        status_code=request_context.disconnect_status_code,
        reason=request_context.disconnect_reason,
    )


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
