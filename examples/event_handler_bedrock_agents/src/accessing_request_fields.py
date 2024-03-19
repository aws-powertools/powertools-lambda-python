from time import time

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = BedrockAgentResolver()


@app.get("/current_time", description="Gets the current time in seconds")  # (1)!
def current_time() -> int:
    logger.append_keys(
        session_id=app.current_event.session_id,
        action_group=app.current_event.action_group,
        input_text=app.current_event.input_text,
    )

    logger.info("Serving current_time")
    return int(time())


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
